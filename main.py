import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler
from utils.batch_processor import BatchProcessor
from utils.resume_injector import ResumeInjector
from utils.batch_resume_injector import BatchResumeInjector
from utils.validators import InputValidator, MessageFormatter
from utils.deduplicator import PointDeduplicator
from utils.persistence import SettingsPersistence, RecentUsedManager
from utils.gemini_points_generator import GeminiPointsGenerator, PointsValidator
from utils.cloud_storage_manager import get_cloud_storage_manager
from utils.email_sender import get_email_sender
import io
import zipfile
from pathlib import Path
import pandas as pd
import logging
import os

# Setup logging
logger = logging.getLogger(__name__)

# ==================== CACHING FUNCTIONS ====================
@st.cache_resource
def get_neon_manager():
    """Cache Neon manager for entire session"""
    from utils.neon_resume_manager import NeonResumeManager
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    return NeonResumeManager(db_url)

@st.cache_resource
def get_automation_workflow():
    """Cache automation workflow for entire session"""
    from automation_workflow import AutomationWorkflow
    return AutomationWorkflow()

# ===========================================================

def main():
    st.set_page_config(
        page_title="Text Processor",
        page_icon="📝",
        layout="wide"
    )

    st.title("Structured Text Processor")
    st.markdown("""
    Extract and reorganize structured content with headings and bullet points.
    """)

    # Initialize session state
    if 'processed_text' not in st.session_state:
        st.session_state.processed_text = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None
    if 'tab3_detected_bookmarks' not in st.session_state:
        st.session_state.tab3_detected_bookmarks = []
    if 'tab3_custom_mapping' not in st.session_state:
        st.session_state.tab3_custom_mapping = {}
    
    # Cache for bookmark detection
    if 'bookmark_cache' not in st.session_state:
        st.session_state.bookmark_cache = {}  # {file_hash: bookmarks}
    
    # Settings persistence
    if 'settings' not in st.session_state:
        st.session_state.settings = SettingsPersistence()
    
    # Input validation
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    
    # Undo/Redo stacks for text processing
    if 'undo_stack' not in st.session_state:
        st.session_state.undo_stack = []
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = []
    
    # Last injection state for resume tab
    if 'last_injection' not in st.session_state:
        st.session_state.last_injection = None
    
    # Batch resume injection state
    if 'batch_resumes' not in st.session_state:
        st.session_state.batch_resumes = {}
    if 'batch_texts' not in st.session_state:
        st.session_state.batch_texts = {}
    if 'batch_mapping' not in st.session_state:
        st.session_state.batch_mapping = {}
    if 'batch_injection_results' not in st.session_state:
        st.session_state.batch_injection_results = None

    # Create tabs for single and batch processing
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Single File Processing", "Batch Processing", "Resume Template Injection", "Batch Resume Injection", "Auto Points from Job Description", "📧 Send Resumes via Email", "🚀 Complete Automation"])

    with tab1:
        st.markdown("### 📝 Step 1: Input Your Text")
        
        # Help section
        with st.expander("📖 Format Help & Troubleshooting", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(MessageFormatter.get_format_help())
            with col2:
                st.markdown(MessageFormatter.get_troubleshooting())
        
        # Single file processing UI
        if st.button("📋 Load Sample Input"):
            sample_text = """Heading 1
• Point 1
• Point 2
• Point 3
• Point 4

Heading 2
• Item A
• Item B
• Item C
• Item D

Heading 3
• Task 1
• Task 2
• Task 3
• Task 4"""
            st.session_state.input_text = sample_text
            st.rerun()

        # Text input area with validation feedback
        input_text = st.text_area(
            "Enter your structured text (headings followed by bullet points)",
            value=st.session_state.input_text,
            height=300,
            key="tab1_input_text",
            help="Enter your text with headings and bullet points (• or -)"
        )

        # Real-time input validation
        if input_text:
            is_valid, error_msg = InputValidator.validate_text_input(input_text)
            if not is_valid:
                st.warning(error_msg)

        # Process button and points per heading input
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            points_per_heading = st.number_input(
                "Number of points to extract per heading per cycle",
                min_value=1,
                max_value=10,
                value=st.session_state.settings.get('points_per_cycle', 2),
                key="tab1_points_per_cycle"
            )
            # Validate and save setting
            is_valid, error_msg = InputValidator.validate_points_per_cycle(points_per_heading)
            if not is_valid:
                st.error(error_msg)
            else:
                st.session_state.settings.set('points_per_cycle', points_per_heading)

        with col2:
            process_button = st.button("🔄 Process Text", use_container_width=True)
        
        with col3:
            dedup_enabled = st.checkbox("🔍 Remove Duplicates", value=st.session_state.settings.get('deduplication_enabled', False))
            st.session_state.settings.set('deduplication_enabled', dedup_enabled)

        # Process text when button is clicked
        if process_button and input_text:
            try:
                # Validate input before processing
                is_valid, error_msg = InputValidator.validate_text_input(input_text)
                if not is_valid:
                    st.error(error_msg)
                else:
                    # Create a spinner to show processing status
                    with st.spinner('Processing text...'):
                        processor = TextProcessor()
                        processed_content = processor.process_text(input_text, points_per_heading)

                        if processed_content:
                            # Save to undo stack before modifying
                            if st.session_state.processed_text:
                                st.session_state.undo_stack.append(st.session_state.processed_text)
                                st.session_state.redo_stack = []  # Clear redo stack on new operation
                            
                            # Apply deduplication if enabled
                            if dedup_enabled:
                                # Extract points from processed content and deduplicate
                                lines = processed_content.split('\n')
                                dedup_lines = []
                                current_section_points = []
                                
                                for line in lines:
                                    if line.strip().startswith('Cycle'):
                                        # If we have accumulated points, deduplicate them
                                        if current_section_points:
                                            dedup_points = PointDeduplicator.deduplicate_points_exact(current_section_points)
                                            dedup_lines.extend(dedup_points)
                                            current_section_points = []
                                        dedup_lines.append(line)
                                    elif line.strip() and not line.strip().startswith(('Cycle', '=')):
                                        current_section_points.append(line)
                                    else:
                                        if current_section_points:
                                            dedup_points = PointDeduplicator.deduplicate_points_exact(current_section_points)
                                            dedup_lines.extend(dedup_points)
                                            current_section_points = []
                                        if line.strip():
                                            dedup_lines.append(line)
                                
                                # CRITICAL: Flush any remaining points at the end (especially Cycle 2+)
                                if current_section_points:
                                    dedup_points = PointDeduplicator.deduplicate_points_exact(current_section_points)
                                    dedup_lines.extend(dedup_points)
                                
                                processed_content = '\n'.join(dedup_lines)
                                st.info(f"🔍 Duplicates removed from output")
                            
                            st.session_state.processed_text = processed_content
                            st.session_state.input_text = input_text  # Preserve input text
                            st.session_state.settings.add_to_history(f"Processed {len(input_text)} chars")

                            st.success("✅ Text processed successfully!")

                            # Display processed output in a container
                            with st.container():
                                st.subheader("📊 Processed Output")
                                st.text_area(
                                    "Preview",
                                value=processed_content,
                                height=1000,
                                key="processed_output"
                            )

                            # Export options
                            st.subheader("Export Options")
                            export_col1, export_col2, export_col3 = st.columns(3)

                            with export_col1:
                                if st.button("Copy to Clipboard"):
                                    st.code(processed_content)
                                    st.toast("Text ready to copy!")

                            with export_col2:
                                export_handler = ExportHandler()
                                docx_file = export_handler.generate_docx(processed_content)
                                st.download_button(
                                    label="Download DOCX",
                                    data=docx_file.getvalue(),
                                    file_name="processed_text.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )

                            with export_col3:
                                pdf_file = export_handler.generate_pdf(processed_content)
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_file.getvalue(),
                                    file_name="processed_text.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error("No output was generated. Please check your input format.")

            except ValueError as e:
                st.error(f"❌ Input Error: {str(e)}")
                st.warning("📋 Expected format example:")
                st.code("""Heading 1
• Point 1
• Point 2

Heading 2
• Item A
• Item B""")
            except Exception as e:
                from utils.security_utils import InputSanitizer
                sanitized_error = InputSanitizer.sanitize_error_message(e, user_facing=True)
                st.error(f"❌ Unexpected error: {type(e).__name__}")
                st.info(f"Please try again or contact support if the issue persists.")
                with st.expander("Technical details"):
                    st.code(sanitized_error)

    with tab2:
        # Batch processing UI
        st.markdown("### 📦 Batch Text Processing")
        
        # Initialize batch mode session state
        if 'batch_mode' not in st.session_state:
            st.session_state.batch_mode = 'paste'
        
        # Mode selector
        batch_mode = st.radio(
            "Choose input method:",
            options=['paste', 'upload'],
            format_func=lambda x: '📝 Paste & Process' if x == 'paste' else '📁 Upload Files',
            horizontal=True,
            key='batch_mode_selector'
        )
        st.session_state.batch_mode = batch_mode
        
        # ============ PASTE & PROCESS MODE ============
        if batch_mode == 'paste':
            st.markdown("""
            Paste multiple texts separated by **`---`** (three dashes on their own line).
            Each section will be processed separately and exported as individual files.
            """)
            
            # Text input area
            batch_paste_text = st.text_area(
                "Paste multiple texts (separate by --- on its own line)",
                height=300,
                help="Example: Text 1\n---\nText 2\n---\nText 3",
                key="batch_paste_input"
            )
            
            # Settings
            col1, col2 = st.columns([2, 1])
            with col1:
                points_per_heading_batch = st.number_input(
                    "Number of points to extract per heading per cycle",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.settings.get('points_per_cycle', 2),
                    key="batch_paste_points"
                )
            with col2:
                batch_dedup = st.checkbox("🔍 Remove Duplicates", value=st.session_state.settings.get('deduplication_enabled', False), key="batch_paste_dedup")
            
            if st.button("🔄 Process Texts", use_container_width=True, key="batch_paste_button"):
                if batch_paste_text.strip():
                    with st.spinner('Processing texts...'):
                        try:
                            # Split texts by separator
                            texts = batch_paste_text.split('\n---\n')
                            texts = [t.strip() for t in texts if t.strip()]
                            
                            if not texts:
                                st.error("❌ No valid text found. Make sure texts are separated by '---' on its own line.")
                            else:
                                # Create virtual file objects from texts
                                class VirtualFile:
                                    def __init__(self, name, content):
                                        self.name = name
                                        self.content = content
                                    
                                    def read(self):
                                        return self.content.encode('utf-8')
                                
                                virtual_files = [
                                    VirtualFile(f"text_{i+1}.txt", text) 
                                    for i, text in enumerate(texts)
                                ]
                                
                                # Process using batch processor
                                batch_processor = BatchProcessor()
                                results = batch_processor.process_files(virtual_files, points_per_heading_batch, dedup_enabled=batch_dedup)
                                
                                if results:
                                    successful = sum(1 for r in results for filename, (text, _, _) in r.items() if not (isinstance(text, str) and text.startswith("Error")))
                                    st.success(f"✅ Successfully processed {successful}/{len(results)} text(s)!")
                                    
                                    # Display individual results
                                    for result in results:
                                        for filename, (text, docx, pdf) in result.items():
                                            st.subheader(f"📄 {filename}")
                                            if isinstance(text, str) and text.startswith("Error"):
                                                st.error(text)
                                            else:
                                                st.text_area(
                                                    "Processed Text",
                                                    value=text,
                                                    height=800,
                                                    key=f"batch_{filename}",
                                                    disabled=True
                                                )
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    if docx:
                                                        st.download_button(
                                                            label=f"📥 {filename}.docx",
                                                            data=docx,
                                                            file_name=f"{filename}.docx",
                                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                            key=f"{filename}_docx",
                                                            use_container_width=True
                                                        )
                                                with col2:
                                                    if pdf:
                                                        st.download_button(
                                                            label=f"📄 {filename}.pdf",
                                                            data=pdf,
                                                            file_name=f"{filename}.pdf",
                                                            mime="application/pdf",
                                                            key=f"{filename}_pdf"
                                                        )
                                    
                                    # Create ZIP file for batch download
                                    if successful > 0:
                                        st.subheader("Download All Results")
                                        zip_buffer = io.BytesIO()
                                        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                                            for result in results:
                                                for filename, (text, docx, pdf) in result.items():
                                                    if isinstance(text, str) and docx is not None and pdf is not None:
                                                        zip_file.writestr(f"{filename}.txt", text)
                                                        if docx:
                                                            zip_file.writestr(f"{filename}.docx", docx)
                                                        if pdf:
                                                            zip_file.writestr(f"{filename}.pdf", pdf)
                                        
                                        st.download_button(
                                            label="Download All Files (ZIP)",
                                            data=zip_buffer.getvalue(),
                                            file_name="processed_texts.zip",
                                            mime="application/zip",
                                            key="batch_paste_zip"
                                        )
                        
                        except ValueError as e:
                            st.error(f"❌ Format Error: {str(e)}")
                            st.warning("Check that all texts contain properly formatted headings and bullet points.")
                        except Exception as e:
                            st.error(f"❌ Processing Failed: {type(e).__name__}")
                            with st.expander("Technical details"):
                                st.code(str(e))
                else:
                    st.warning("Please paste some text to process.")
        
        # ============ UPLOAD MODE ============
        else:
            st.markdown("""
            Upload multiple text files to process them all at once.
            Each file should contain structured text with headings and bullet points.
            """)
            
            uploaded_files = st.file_uploader(
                "Upload text files",
                type=['txt'],
                accept_multiple_files=True,
                help="Select multiple .txt files to process",
                key="batch_upload_files"
            )

            if uploaded_files:
                # Validate files
                valid_files = []
                for file in uploaded_files:
                    is_valid, error_msg = InputValidator.validate_text_file(file.name)
                    if is_valid:
                        valid_files.append(file)
                    else:
                        st.error(f"❌ {error_msg}")
                
                if valid_files:
                    st.info(f"✅ Found {len(valid_files)} valid file(s) to process")

                    points_per_heading_batch = st.number_input(
                        "Number of points to extract per heading per cycle (batch)",
                        min_value=1,
                        max_value=10,
                        value=st.session_state.settings.get('points_per_cycle', 2),
                        key="batch_upload_points"
                    )

                    batch_dedup = st.checkbox("🔍 Remove Duplicates", value=st.session_state.settings.get('deduplication_enabled', False), key="batch_upload_dedup")

                    if st.button("🔄 Process Batch", use_container_width=True, key="batch_upload_button"):
                        with st.spinner('Processing files...'):
                            try:
                                batch_processor = BatchProcessor()
                                results = batch_processor.process_files(valid_files, points_per_heading_batch, dedup_enabled=batch_dedup)

                                if results:
                                    successful = sum(1 for r in results for filename, (text, _, _) in r.items() if not (isinstance(text, str) and text.startswith("Error")))
                                    st.success(f"✅ Successfully processed {successful}/{len(results)} files!")

                                    # Display individual results
                                    for result in results:
                                        for filename, (text, docx, pdf) in result.items():
                                            st.subheader(f"📄 {filename}")
                                            if isinstance(text, str) and text.startswith("Error"):
                                                st.error(text)
                                            else:
                                                st.text_area(
                                                    "Processed Text",
                                                    value=text,
                                                    height=800,
                                                    key=f"batch_{filename}",
                                                    disabled=True
                                                )
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    if docx:
                                                        st.download_button(
                                                            label=f"📥 {filename}.docx",
                                                            data=docx,
                                                            file_name=f"{filename}.docx",
                                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                            key=f"{filename}_docx",
                                                            use_container_width=True
                                                        )
                                                with col2:
                                                    if pdf:
                                                        st.download_button(
                                                            label=f"📄 {filename}.pdf",
                                                            data=pdf,
                                                            file_name=f"{filename}.pdf",
                                                            mime="application/pdf",
                                                            key=f"{filename}_pdf"
                                                        )

                                    # Create ZIP file for batch download
                                    if successful > 0:
                                        st.subheader("Download All Results")
                                        zip_buffer = io.BytesIO()
                                        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                                            for result in results:
                                                for filename, (text, docx, pdf) in result.items():
                                                    # Only add successful results (docx/pdf are not None)
                                                    if isinstance(text, str) and docx is not None and pdf is not None:
                                                        # Add text file
                                                        zip_file.writestr(f"{filename}.txt", text)
                                                        # Add DOCX file
                                                        if docx:
                                                            zip_file.writestr(f"{filename}.docx", docx)
                                                        # Add PDF file
                                                        if pdf:
                                                            zip_file.writestr(f"{filename}.pdf", pdf)

                                        st.download_button(
                                            label="Download All Files (ZIP)",
                                            data=zip_buffer.getvalue(),
                                            file_name="processed_files.zip",
                                            mime="application/zip",
                                            key="batch_upload_zip"
                                        )
                                else:
                                    st.warning("No files were processed. Please check your input files.")

                            except ValueError as e:
                                st.error(f"❌ Format Error: {str(e)}")
                                st.warning("Check that all files contain properly formatted headings and bullet points.")
                            except Exception as e:
                                st.error(f"❌ Batch Processing Failed: {type(e).__name__}")
                                st.info("Some files may have failed to process. Check file formats and try again.")
                                with st.expander("Technical details"):
                                    st.code(str(e))

    with tab3:
        # Resume Template Injection UI
        st.markdown("### 🎯 Resume Template Injection")
        st.markdown("""
        Inject extracted points into your resume template with flexible bookmark mapping.
        
        **Features:**
        - ✅ Auto-detects bookmarks (any naming convention)
        - ✅ Smart cycle-to-bookmark mapping
        - ✅ Interactive mapping editor
        - ✅ Save/reuse bookmark profiles
        - ✅ Preview before injection
        """)
        
        # Import BookmarkManager
        from utils.bookmark_manager import BookmarkManager
        
        bm_manager = BookmarkManager()
        recent_manager = RecentUsedManager()
        
        # Enhanced Profile Management Section
        st.markdown("### 📁 Bookmark Profiles & Recent Mappings")
        
        profile_col1, profile_col2, profile_col3, profile_col4 = st.columns(4)
        
        with profile_col1:
            if st.button("📋 View Profiles", use_container_width=True):
                profiles = bm_manager.list_profiles()
                if profiles:
                    st.write("**Saved Profiles:**")
                    for i, profile in enumerate(profiles):
                        col_delete = st.columns([3, 1])[0]
                        st.write(f"**{i+1}. {profile['name']}**")
                        st.caption(f"Resume: {profile['resume_name']} | Bookmarks: {profile['bookmarks_count']}")
                else:
                    st.info("No saved profiles yet")
        
        with profile_col2:
            if st.button("⏱️ Recent Mappings", use_container_width=True):
                recent = recent_manager.list_recent_mappings()
                if recent:
                    st.write("**Recently Used:**")
                    for i, mapping in enumerate(recent):
                        st.caption(f"{i+1}. {mapping['name']}")
                else:
                    st.info("No recent mappings")
        
        with profile_col3:
            if st.button("🗑️ Manage", use_container_width=True):
                st.markdown("**Manage Profiles:**")
                profiles = bm_manager.list_profiles()
                if profiles:
                    profile_to_delete = st.selectbox(
                        "Select profile to delete:",
                        [p['name'] for p in profiles],
                        key="delete_profile_select"
                    )
                    if st.button("🗑️ Delete Profile", key="confirm_delete"):
                        if bm_manager.delete_profile(profile_to_delete):
                            st.success(f"✅ Profile deleted: {profile_to_delete}")
                            st.rerun()
                else:
                    st.info("No profiles to manage")
        
        with profile_col4:
            if st.button("❓ Tutorial", use_container_width=True):
                st.markdown("""
                ### 📚 Resume Bookmark Guide
                
                **To create bookmarks in Word:**
                1. Select text where you want injected points
                2. Go to Insert → Bookmark
                3. Name it descriptively (e.g., "Company_Responsibilities")
                4. Click Add
                5. Save as .docx file
                
                **Naming convention:**
                - Use underscores: `Company_Name_Section`
                - Avoid special characters
                - Keep names meaningful
                """)
        
        # Step 1: Upload resume template
        st.markdown("### Step 1: Upload Resume Template")
        resume_file = st.file_uploader(
            "Upload your resume template (DOCX with bookmarks)",
            type=['docx'],
            key="resume_upload"
        )
        
        # Initialize variables to avoid scope issues
        detected_bookmarks = []
        resume_bytes = None
        
        if resume_file:
            try:
                # Validate file
                is_valid, error_msg = InputValidator.validate_docx_file(resume_file.name)
                if not is_valid:
                    st.error(error_msg)
                else:
                    resume_bytes = io.BytesIO(resume_file.read())
                    resume_bytes.seek(0)  # Reset stream position to beginning
                    injector = ResumeInjector()
                    detected_bookmarks = injector.get_available_bookmarks(resume_bytes)
                    
                    if not detected_bookmarks:
                        st.warning("⚠️ No bookmarks found in resume. Please add bookmarks first and try again.")
                        st.markdown(MessageFormatter.get_troubleshooting())
                    else:
                        st.success(f"✅ Resume template loaded")
                        st.info(f"📌 Found **{len(detected_bookmarks)}** bookmark(s)")
                        
                        # Display bookmarks
                        with st.expander("📍 View detected bookmarks", expanded=False):
                            col1, col2 = st.columns([1, 1])
                            for i, bm in enumerate(detected_bookmarks):
                                if i % 2 == 0:
                                    with col1:
                                        st.code(f"{i+1}. {bm}")
                                else:
                                    with col2:
                                        st.code(f"{i+1}. {bm}")
                        
                        # Option to load existing profile
                        st.markdown("#### Load Profile (Optional)")
                        profiles = bm_manager.list_profiles()
                        if profiles:
                            profile_names = [p['name'] for p in profiles]
                            selected_profile = st.selectbox(
                                "Load a saved profile:",
                                ["-- Create Custom Mapping --"] + profile_names,
                                key="profile_select"
                            )
                            
                            if selected_profile != "-- Create Custom Mapping --":
                                profile_data = bm_manager.load_profile(selected_profile)
                                if profile_data:
                                    st.success(f"✅ Profile loaded: {selected_profile}")
                                    st.info(f"Contains {len(profile_data.get('mapping', {}))} cycle mappings")
                        
                        resume_bytes.seek(0)
                
            except ValueError as e:
                st.error(f"❌ Validation Error: {str(e)}")
                st.info("Please ensure your file is a valid DOCX file with bookmarks.")
            except Exception as e:
                st.error(f"❌ Error reading resume template: {str(e)}")
                st.info("Ensure your resume is a valid DOCX file with bookmarks.")
                resume_file = None
        
        if resume_file and detected_bookmarks:
            # Step 2: Get processed text
            st.markdown("### Step 2: Provide Extracted Points")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                input_method = st.radio(
                    "How would you like to provide extracted points?",
                    ["Paste Text", "Upload File"],
                    key="resume_input_method"
                )
            
            processed_text = None
            
            if input_method == "Paste Text":
                processed_text = st.text_area(
                    "Paste your processed text here",
                    height=1000,
                    help="Text should contain 'Cycle 1:', 'Cycle 2:', etc. followed by points",
                    key="resume_text_input"
                )
            else:
                text_file = st.file_uploader(
                    "Upload text file with extracted points",
                    type=['txt'],
                    key="resume_text_upload"
                )
                if text_file:
                    try:
                        file_content = text_file.read()  # Read once
                        try:
                            processed_text = file_content.decode('utf-8')
                        except UnicodeDecodeError:
                            # Try alternative encodings
                            try:
                                processed_text = file_content.decode('latin-1')
                            except UnicodeDecodeError:
                                processed_text = file_content.decode('utf-8', errors='replace')
                    except Exception as e:
                        st.error(f"❌ Error reading text file: {str(e)}")
                else:
                    st.info("Use Tab 1 to process your text first and copy the output.")
            
            if processed_text and processed_text.strip():
                # Validate cycle format
                is_valid, error_msg = InputValidator.validate_cycle_format(processed_text)
                if not is_valid:
                    st.error(error_msg)
                    st.markdown(MessageFormatter.get_troubleshooting())
                else:
                    # Extract cycles from text
                    import re
                    cycle_matches = re.findall(r'Cycle\s+(\d+):', processed_text, re.IGNORECASE)
                    num_cycles = len(set(cycle_matches)) if cycle_matches else 0
                    
                    if num_cycles > 0:
                        st.markdown(f"### Step 3: Map Cycles to Bookmarks ({num_cycles} cycles detected)")
                        
                        # Auto-suggest mapping
                        suggested_mapping = bm_manager.suggest_mappings(detected_bookmarks, num_cycles)
                        
                        # Validate cycle count vs bookmarks
                        is_valid, message = InputValidator.validate_cycle_count(num_cycles, len(detected_bookmarks))
                        if is_valid:
                            st.info(message)
                        
                        # ⚠️ ENHANCED MISMATCH DETECTION & HANDLING
                        has_mismatch = num_cycles != len(detected_bookmarks)
                        if has_mismatch:
                            if num_cycles < len(detected_bookmarks):
                                unused_bookmarks = [b for b in detected_bookmarks if b not in suggested_mapping.values()]
                                st.warning(f"""
⚠️ **Bookmark Mismatch Detected!**
- 📌 Resume has **{len(detected_bookmarks)}** bookmarks
- 📊 You have **{num_cycles}** cycles of data
- 🔲 **{len(unused_bookmarks)}** bookmark(s) will remain unchanged: {', '.join(unused_bookmarks)}

**What happens:**
✓ Cycles will be injected into matching bookmarks
⚠️ Unused bookmarks keep their original resume content
                                """)
                            else:
                                st.warning(f"""
⚠️ **More Cycles Than Bookmarks**
- 📊 You have **{num_cycles}** cycles of data
- 📌 Resume has only **{len(detected_bookmarks)}** bookmarks

**What happens:**
✓ Only first {len(detected_bookmarks)} cycles will be used
⚠️ Additional cycles cannot be injected
                                """)
                        
                        st.info(f"💡 **Auto-suggested mapping:** {', '.join([f'Cycle {c}→{b}' for c, b in suggested_mapping.items()])}")
                        
                        # Interactive mapping editor
                        st.markdown("#### Customize Mapping (if needed)")
                        custom_mapping = {}
                        
                        cols = st.columns(min(3, num_cycles))
                        for cycle_num in range(1, num_cycles + 1):
                            col = cols[(cycle_num - 1) % len(cols)]
                            with col:
                                # Safe index calculation to avoid out-of-bounds error
                                suggested_bm = suggested_mapping.get(cycle_num, detected_bookmarks[0] if detected_bookmarks else "")
                                bm_index = detected_bookmarks.index(suggested_bm) if suggested_bm in detected_bookmarks else 0
                                selected_bookmark = st.selectbox(
                                    f"Cycle {cycle_num}",
                                    detected_bookmarks,
                                    index=bm_index,
                                    key=f"cycle_{cycle_num}_mapping"
                                )
                                custom_mapping[cycle_num] = selected_bookmark
                        
                        # Enhanced Preview table with status
                        st.markdown("#### 📊 Mapping Summary")
                        
                        # Create detailed preview
                        preview_rows = []
                        for cycle_num in range(1, num_cycles + 1):
                            preview_rows.append({
                                "Cycle": f"Cycle {cycle_num}",
                                "→": "→",
                                "Bookmark": custom_mapping[cycle_num],
                                "Status": "✅ NEW"
                            })
                        
                        # Show untouched bookmarks if there's a mismatch
                        if has_mismatch and num_cycles < len(detected_bookmarks):
                            for bm in detected_bookmarks:
                                if bm not in custom_mapping.values():
                                    preview_rows.append({
                                        "Cycle": "—",
                                        "→": "—",
                                        "Bookmark": bm,
                                        "Status": "⚠️ UNCHANGED"
                                    })
                        
                        # Display as table
                        preview_df = pd.DataFrame(preview_rows)
                        st.dataframe(preview_df, use_container_width=True)
                        
                        # Enhanced Mismatch handling options
                        if has_mismatch and num_cycles < len(detected_bookmarks):
                            st.markdown("#### 🔧 Advanced: Handling Unused Bookmarks")
                            unused_handling = st.radio(
                                "How to handle bookmarks without matching cycles:",
                                {
                                    "keep": "✓ Keep original content (recommended)",
                                    "repeat": "🔄 Repeat last cycle's content",
                                    "clear": "🗑️ Clear content"
                                },
                                captions=[
                                    "Preserves existing resume text",
                                    "Fills all unused bookmarks with last cycle data",
                                    "Removes content from unused bookmarks"
                                ],
                                index=0,
                                help="Choose how to handle bookmarks that don't have matching cycles"
                            )
                            
                            unused_bms = [b for b in detected_bookmarks if b not in custom_mapping.values()]
                            st.caption(f"Affected bookmarks: {', '.join(unused_bms)}")
                        else:
                            unused_handling = "keep"
                        
                        # Save profile option
                        st.markdown("#### 💾 Save this Mapping as Profile (Optional)")
                        profile_save_col1, profile_save_col2 = st.columns([3, 1])
                        with profile_save_col1:
                            profile_name = st.text_input(
                                "Profile name",
                                value=resume_file.name.replace('.docx', ''),
                                help="e.g., 'Java Resume', 'Google Profile'"
                            )
                        with profile_save_col2:
                            if st.button("💾 Save Profile"):
                                if profile_name:
                                    bm_manager.save_profile(
                                        profile_name,
                                        detected_bookmarks,
                                        custom_mapping,
                                        resume_file.name
                                    )
                                    st.success(f"✓ Profile saved: {profile_name}")
                                else:
                                    st.warning("Enter a profile name first")
                    
                    # Step 4: Inject and download with Undo
                    st.markdown("### Step 4: Inject, Review & Download")
                    
                    inject_col1, inject_col2, inject_col3 = st.columns([2, 1, 1])
                    
                    with inject_col1:
                        if st.button("✨ Inject Points into Resume", type="primary", use_container_width=True):
                            with st.spinner('Injecting points...'):
                                try:
                                    resume_bytes.seek(0)
                                    injector = ResumeInjector()
                                    
                                    # Store current state for undo
                                    if 'last_injection' not in st.session_state:
                                        st.session_state.last_injection = None
                                    
                                    updated_resume, injections = injector.inject_points_into_resume(
                                        resume_bytes,
                                        processed_text,
                                        custom_mapping=custom_mapping
                                    )
                                    
                                    # Save for undo
                                    st.session_state.last_injection = updated_resume.getvalue()
                                    
                                    st.success("✅ Points injected successfully!")
                                    
                                    # Show summary with formatting  
                                    st.markdown("#### 📊 **Injection Summary**")
                                    summary_cols = st.columns(len(injections))
                                    for i, (bookmark, count) in enumerate(injections.items()):
                                        with summary_cols[i % len(summary_cols)]:
                                            st.metric(f"📌 {bookmark[:25]}", f"{count} points")
                                    
                                    # Download button
                                    st.download_button(
                                        label="📥 Download Updated Resume",
                                        data=updated_resume.getvalue(),
                                        file_name="Resume_Updated.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key="resume_download",
                                        use_container_width=True
                                    )
                                    
                                    # Save to recent mappings
                                    recent_manager.save_recent_mapping(
                                        f"{resume_file.name.replace('.docx', '')}_{num_cycles}cycles",
                                        {str(k): v for k, v in custom_mapping.items()}
                                    )
                                    
                                except ValueError as e:
                                    st.error(f"❌ Format Error: {str(e)}")
                                    with st.expander("📋 Troubleshooting - Format Issues"):
                                        st.markdown(MessageFormatter.get_troubleshooting())
                                        st.text_area(
                                            "Text preview (first 500 chars):",
                                            value=processed_text[:500],
                                            height=400,
                                            disabled=True
                                        )
                                except Exception as e:
                                    st.error(f"❌ Injection Failed: {type(e).__name__}")
                                    with st.expander("🔍 Debug Information"):
                                        st.error(f"**Error Message:** {str(e)}")
                                        st.text(f"**Cycles detected:** {num_cycles}")
                                        st.text(f"**Bookmarks found:** {len(detected_bookmarks)}")
                                        st.text(f"**Text length:** {len(processed_text)} characters")
                                    
                                    st.markdown("**Quick Fixes:**")
                                    st.info("1️⃣ Go back to Tab 1 and reprocess the text")
                                    st.info("2️⃣ Ensure Resume template has valid bookmarks")
                                    st.info("3️⃣ Check that cycle format is correct (Cycle 1:, Cycle 2:, etc)")
                    
                    with inject_col2:
                        if st.session_state.last_injection:
                            if st.button("↩️ Undo", help="Download previous version"):
                                st.download_button(
                                    label="↩️ Download Previous",
                                    data=st.session_state.last_injection,
                                    file_name="Resume_Previous.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="resume_undo_download",
                                    use_container_width=True
                                )
                    
                    with inject_col3:
                        if st.button("🔄 Restart", help="Clear all and start over"):
                            st.session_state.tab3_detected_bookmarks = []
                            st.session_state.tab3_custom_mapping = {}
                            st.session_state.last_injection = None
                            st.rerun()
            
            if not processed_text or not processed_text.strip():
                st.info("💡 Step2 required: Paste or upload your processed text from Tab 1")
    
    with tab4:
        # Batch Resume Injection UI
        st.markdown("### 🎯 Batch Resume Injection")
        st.markdown("""
        Inject multiple text files into multiple resume templates with custom mapping.
        
        **Features:**
        - ✅ Upload multiple resume templates (up to 20)
        - ✅ Upload multiple text files with extracted points (up to 20)
        - ✅ Create custom mapping (Text File 1 → Resume A, Text File 2 → Resume B, etc.)
        - ✅ Download each result individually
        - ✅ View injection summary for each pair
        """)
        
        batch_injector = BatchResumeInjector()
        
        # Step 1: Upload multiple resume templates
        st.markdown("### Step 1: Upload Resume Templates")
        st.info("📌 Each resume should have bookmarks defined for injection")
        
        resume_files = st.file_uploader(
            "Upload resume templates (DOCX with bookmarks)",
            type=['docx'],
            accept_multiple_files=True,
            key="batch_resume_upload"
        )
        
        batch_resumes_data = {}
        if resume_files:
            is_valid, error_msg, batch_resumes_data = batch_injector.validate_resume_files(resume_files)
            
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                st.success(f"✅ Loaded {len(batch_resumes_data)} resume template(s)")
                
                # Show resume details
                with st.expander("📄 Resume Files Details", expanded=True):
                    for resume_name, resume_info in batch_resumes_data.items():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{resume_name}**")
                        with col2:
                            st.caption(f"Original: {resume_info['original_name']}")
                        with col3:
                            st.badge(f"{len(resume_info['bookmarks'])} bookmarks", icon="📌")
        
        if batch_resumes_data:
            # Step 2: Upload multiple text files
            st.markdown("### Step 2: Upload Text Files")
            st.info("📝 Each file should contain processed text with Cycle format")
            
            text_files = st.file_uploader(
                "Upload text files with extracted points",
                type=['txt'],
                accept_multiple_files=True,
                key="batch_text_upload"
            )
            
            batch_texts_data = {}
            if text_files:
                is_valid, error_msg, batch_texts_data = batch_injector.validate_text_files(text_files)
                
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    st.success(f"✅ Loaded {len(batch_texts_data)} text file(s)")
                    
                    # Show text file details
                    with st.expander("📋 Text Files Details", expanded=True):
                        for text_name, text_info in batch_texts_data.items():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{text_name}**")
                            with col2:
                                st.caption(f"Original: {text_info['original_name']}")
                            with col3:
                                st.badge(f"{len(text_info['content'])} chars", icon="📄")
        
        if batch_resumes_data and batch_texts_data:
            # Step 3: Create mapping
            st.markdown("### Step 3: Create Mapping")
            st.info("🔗 Pair each text file with a resume file")
            
            mapping = {}
            resume_names = list(batch_resumes_data.keys())
            text_names = list(batch_texts_data.keys())
            
            # Create mapping UI
            cols_header = st.columns([2, 1, 2])
            with cols_header[0]:
                st.write("**Text File**")
            with cols_header[1]:
                st.write("**→**")
            with cols_header[2]:
                st.write("**Resume File**")
            
            st.divider()
            
            for i, text_name in enumerate(text_names):
                cols = st.columns([2, 1, 2])
                with cols[0]:
                    st.write(f"📝 {text_name}")
                with cols[1]:
                    st.write("→")
                with cols[2]:
                    # Default to same index if available, otherwise first resume
                    default_resume = resume_names[i] if i < len(resume_names) else resume_names[0]
                    selected_resume = st.selectbox(
                        f"Select resume for {text_name}",
                        resume_names,
                        index=resume_names.index(default_resume),
                        key=f"batch_mapping_{i}_{text_name}",
                        label_visibility="collapsed"
                    )
                    mapping[text_name] = selected_resume
            
            # Show mapping summary
            st.markdown("#### 📊 Mapping Summary")
            summary_rows = []
            for text_name, resume_name in mapping.items():
                summary_rows.append({
                    "Text File": text_name,
                    "→": "→",
                    "Resume File": resume_name
                })
            summary_df = pd.DataFrame(summary_rows)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Step 4: Perform batch injection
            st.markdown("### Step 4: Execute Batch Injection")
            
            col_inject, col_reset = st.columns([1, 1])
            
            with col_inject:
                if st.button("✨ Execute Batch Injection", type="primary", use_container_width=True):
                    with st.spinner("Processing batch injection..."):
                        try:
                            # Reset stream positions
                            for resume_info in batch_resumes_data.values():
                                resume_info['bytes'].seek(0)
                            
                            results, errors = batch_injector.inject_batch(
                                batch_texts_data,
                                batch_resumes_data,
                                mapping
                            )
                            
                            # Store results in session state
                            st.session_state.batch_injection_results = {
                                'results': results,
                                'errors': errors
                            }
                            
                            st.success("✅ Batch injection completed!")
                            
                        except Exception as e:
                            st.error(f"❌ Batch injection failed: {str(e)}")
                            logger.error(f"Batch injection error: {str(e)}", exc_info=True)
            
            with col_reset:
                if st.button("🔄 Clear & Start Over", use_container_width=True):
                    st.session_state.batch_injection_results = None
                    st.session_state.batch_resumes = {}
                    st.session_state.batch_texts = {}
                    st.session_state.batch_mapping = {}
                    st.rerun()
            
            # Step 5: Download results
            if st.session_state.batch_injection_results:
                results = st.session_state.batch_injection_results['results']
                errors = st.session_state.batch_injection_results['errors']
                
                st.markdown("### Step 5: Download Results")
                
                # Show summary
                summary = batch_injector.generate_summary(results, errors)
                
                summary_cols = st.columns(3)
                with summary_cols[0]:
                    st.metric("Total Pairs", summary['total_pairs'])
                with summary_cols[1]:
                    st.metric("✅ Successful", summary['successful'], delta_color="off")
                with summary_cols[2]:
                    st.metric("❌ Failed", summary['failed'], delta_color="inverse")
                
                # Show errors if any
                if errors:
                    st.markdown("#### ⚠️ Errors")
                    for error in errors:
                        st.error(error)
                
                # Show successful results
                if results:
                    st.markdown("#### ✅ Successful Injections")
                    
                    for pair_name, (injected_bytes, injection_summary, output_name) in results.items():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Show injection details
                            detail_text = f"**{pair_name}** - "
                            detail_text += ", ".join([f"{bm}: {count} points" for bm, count in injection_summary.items()])
                            st.write(detail_text)
                        
                        with col2:
                            # Custom filename input
                            custom_filename = st.text_input(
                                "Filename",
                                value=output_name,
                                label_visibility="collapsed",
                                key=f"batch_filename_{pair_name}"
                            )
                            
                            # Download button
                            st.download_button(
                                label="📥 Download",
                                data=injected_bytes,
                                file_name=custom_filename.replace('.docx', '') + '.docx',
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"batch_download_{pair_name}"
                            )
                    
                    # Bulk download as ZIP option
                    st.markdown("#### 📦 Bulk Download")
                    if st.button("📦 Download All as ZIP", use_container_width=True):
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for pair_name, (injected_bytes, _, output_name) in results.items():
                                safe_filename = output_name.replace('.docx', '') + '.docx'
                                zip_file.writestr(safe_filename, injected_bytes)
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download All Files as ZIP",
                            data=zip_buffer.getvalue(),
                            file_name="batch_injected_resumes.zip",
                            mime="application/zip",
                            key="batch_zip_download"
                        )
        
        if not batch_resumes_data:
            st.info("📌 Step 1: Start by uploading resume templates")
        elif not batch_texts_data:
            st.info("📝 Step 2: Upload text files with extracted points")
    
    with tab5:
        # Auto Points Generator from Job Description
        st.markdown("### 🤖 Auto Points Generation from Job Description")
        st.markdown("""
        **Workflow:**
        1. Enter job description
        2. Enter desired job title
        3. Set number of points per technology
        4. Get AI-generated bullet points automatically (using FREE Groq API)
        5. Use results with Tab 3 for resume injection
        """)
        
        # Initialize session state for Tab 5
        if 'tab5_api_key_valid' not in st.session_state:
            st.session_state.tab5_api_key_valid = False
        if 'tab5_tech_stacks' not in st.session_state:
            st.session_state.tab5_tech_stacks = []
        if 'tab5_generated_points' not in st.session_state:
            st.session_state.tab5_generated_points = ""
        
        # Check if API key is configured
        import os
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        
        # Step 1: API Key Status
        st.markdown("### Step 1: API Configuration")
        if api_key and api_key != "your_api_key_here":
            st.session_state.tab5_api_key_valid = True
        else:
            st.error("❌ Groq API Key not found!")
            with st.expander("🔧 Setup Instructions", expanded=True):
                st.markdown("""
                **Step 1: Get your FREE Groq API Key**
                1. Visit: https://console.groq.com/keys
                2. Sign up (free, no credit card needed)
                3. Generate new API Key
                4. Copy the key
                
                **Step 2: Store it in .env file**
                1. Open the `.env` file in the project root
                2. Replace with your actual key:
                   ```
                   GROQ_API_KEY=your_actual_key_here
                   ```
                3. Save the file
                   
                **Step 3: Restart the app**
                ```bash
                streamlit run main.py
                ```
                
                ✅ **Why Groq?**
                - Completely FREE (no limits exceeded)
                - Super fast (runs on specialized hardware)
                - Generous free tier (100+ requests daily)
                - No credit card required
                """)
        
        # Step 2: Job Description Input
        st.markdown("### Step 2: Job Description")
        job_description = st.text_area(
            "Paste the job description",
            height=250,
            placeholder="Paste job description here...",
            key="tab5_job_description",
            disabled=not st.session_state.tab5_api_key_valid
        )
        
        # Step 3: Job Details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            job_title = st.text_input(
                "Job Title",
                placeholder="e.g., Senior Full Stack Developer",
                key="tab5_job_title",
                disabled=not st.session_state.tab5_api_key_valid
            )
        
        with col2:
            num_points = st.number_input(
                "Points per Technology",
                min_value=1,
                max_value=5,
                value=3,
                key="tab5_num_points",
                help="Number of bullet points per tech stack",
                disabled=not st.session_state.tab5_api_key_valid
            )
        
        with col3:
            st.markdown("###")  # Spacing
            process_button = st.button(
                "🚀 Generate Points",
                use_container_width=True,
                key="tab5_process_button",
                disabled=not st.session_state.tab5_api_key_valid
            )
        
        # Process Job Description
        if process_button:
            if not job_description or not job_description.strip():
                st.error("❌ Please provide a job description")
            elif not job_title or not job_title.strip():
                st.error("❌ Please provide a job title")
            else:
                try:
                    with st.spinner("🔄 Processing with Groq AI..."):
                        # Initialize generator (will use .env API key)
                        generator = GeminiPointsGenerator()
                        
                        # Generate points
                        tech_stacks, generated_points = generator.process_job_description(
                            job_description=job_description,
                            job_title=job_title,
                            num_points=num_points
                        )
                        
                        # Store in session
                        st.session_state.tab5_tech_stacks = tech_stacks
                        st.session_state.tab5_generated_points = generated_points
                        
                        st.success("✅ Points generated successfully!")
                
                except ValueError as e:
                    st.error(f"❌ Validation Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("Technical Details"):
                        st.code(str(e))
        
        # Display Results
        if st.session_state.tab5_tech_stacks and st.session_state.tab5_generated_points:
            st.markdown("### 📊 Results")
            
            # Show extracted tech stacks
            st.markdown("#### 🔧 Extracted Technologies")
            tech_stack_text = ", ".join(st.session_state.tab5_tech_stacks)
            st.info(f"Found: {tech_stack_text}")
            
            # Show generated points
            st.markdown("#### 📝 Generated Bullet Points")
            st.text_area(
                "Your auto-generated points",
                value=st.session_state.tab5_generated_points,
                height=400,
                disabled=True,
                key="tab5_output",
                label_visibility="collapsed"
            )
            
            # Export Options
            st.markdown("#### 📥 Export Options")
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("📋 Copy to Clipboard", use_container_width=True, key="tab5_copy"):
                    st.code(st.session_state.tab5_generated_points)
                    st.toast("✅ Ready to copy!")
            
            with export_col2:
                # Download as DOCX
                export_handler = ExportHandler()
                docx_file = export_handler.generate_docx(st.session_state.tab5_generated_points)
                st.download_button(
                    label="📄 Download DOCX",
                    data=docx_file.getvalue(),
                    file_name="generated_points.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="tab5_download_docx"
                )
            
            with export_col3:
                # Download as PDF
                pdf_file = export_handler.generate_pdf(st.session_state.tab5_generated_points)
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_file.getvalue(),
                    file_name="generated_points.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="tab5_download_pdf"
                )
            
            # Pass to Tab 3 Option
            st.markdown("#### 🔗 Next Steps")
            if st.button("➡️ Use These Points in Tab 3 (Resume Injection)", use_container_width=True, key="tab5_to_tab3"):
                st.session_state.input_text = st.session_state.tab5_generated_points
                st.info("✅ Points copied to Tab 3! Go to Tab 3 → Step 2 to inject into your resume.")
            
            # Clear option
            if st.button("🔄 Clear Results", use_container_width=True, key="tab5_clear"):
                st.session_state.tab5_tech_stacks = []
                st.session_state.tab5_generated_points = ""
                st.rerun()
    
    with tab6:
        st.markdown("### 📧 Send Resumes via Email")
        st.markdown("""
        Send resumes from your cloud storage (OneDrive, Google Drive, Dropbox) 
        without needing to login to office email on this laptop.
        
        **Features:**
        - ✅ Access resumes from cloud storage
        - ✅ Send via Gmail with App Password (no login required)
        - ✅ Send via Outlook/Office 365
        - ✅ Send multiple resumes at once
        - ✅ Track email history
        """)
        
        # Initialize session state for email tab
        if 'email_tab_resumes' not in st.session_state:
            st.session_state.email_tab_resumes = {}
        if 'email_history' not in st.session_state:
            st.session_state.email_history = []
        
        # Step 1: Select Cloud Storage Provider
        st.markdown("### Step 1️⃣ : Select Cloud Storage Provider")
        
        cloud_provider = st.radio(
            "Where are your resumes stored?",
            options=["onedrive", "google", "dropbox"],
            format_func=lambda x: {
                "onedrive": "☁️ OneDrive",
                "google": "🔵 Google Drive",
                "dropbox": "🔷 Dropbox"
            }[x],
            horizontal=True,
            key="cloud_provider"
        )
        
        # Load resumes from selected provider
        if st.button("🔄 Load Resumes from Cloud", use_container_width=True, key="load_cloud_resumes"):
            with st.spinner("Loading resumes from cloud storage..."):
                try:
                    storage_manager = get_cloud_storage_manager(cloud_provider)
                    resumes = storage_manager.list_files()
                    
                    if resumes:
                        st.session_state.email_tab_resumes = {r['name']: r for r in resumes}
                        st.success(f"✅ Loaded {len(resumes)} resume(s) from {cloud_provider.title()}")
                    else:
                        st.warning(f"⚠️ No resumes found in {cloud_provider.title()}")
                        st.info("💡 Make sure you have a 'Resumes' folder in your cloud storage")
                except Exception as e:
                    st.error(f"❌ Error loading resumes: {str(e)}")
                    st.info("💡 Check that you're connected to the internet and have access to cloud storage")
        
        # Display loaded resumes
        if st.session_state.email_tab_resumes:
            st.success(f"✅ Found {len(st.session_state.email_tab_resumes)} resume(s)")
            with st.expander("📄 Available Resumes", expanded=True):
                for resume_name, resume_info in st.session_state.email_tab_resumes.items():
                    size_kb = resume_info['size'] / 1024
                    st.write(f"📄 **{resume_name}** ({size_kb:.1f} KB)")
        
        # Step 2: Select Email Provider
        st.markdown("### Step 2️⃣ : Select Email Provider")
        
        email_provider = st.radio(
            "How do you want to send emails?",
            options=["gmail", "outlook", "sendgrid"],
            format_func=lambda x: {
                "gmail": "📧 Gmail (App Password)",
                "outlook": "📧 Outlook/Office 365",
                "sendgrid": "📧 SendGrid API"
            }[x],
            horizontal=True,
            key="email_provider"
        )
        
        # Email provider setup instructions
        with st.expander("ℹ️ Setup Instructions for " + email_provider.title(), expanded=True):
            if email_provider == "gmail":
                st.markdown("""
                **Gmail Setup (No Login Required):**
                
                1. Go to [myaccount.google.com](https://myaccount.google.com)
                2. Click **Security** (left sidebar)
                3. Enable **2-Step Verification** (if not already enabled)
                4. Go back to Security page
                5. Find **App Passwords** (appears after 2FA is enabled)
                6. Select "Mail" and "Windows Computer"
                7. Copy the **16-character password** shown
                8. Paste it below
                """)
                
                gmail_email = st.text_input(
                    "Gmail Address",
                    placeholder="your.email@gmail.com",
                    key="gmail_email_input",
                    help="Your Gmail address"
                )
                
                gmail_password = st.text_input(
                    "Gmail App Password",
                    type="password",
                    placeholder="16-character app password",
                    key="gmail_password_input",
                    help="16-character password from Google Account"
                )
            
            elif email_provider == "outlook":
                st.markdown("""
                **Outlook Setup:**
                
                1. Enter your Office 365 email address
                2. Enter your password (or App Password if 2FA is enabled)
                3. If 2FA enabled, get app password from:
                   - Go to [account.microsoft.com](https://account.microsoft.com)
                   - Click **Security** → **App passwords**
                """)
                
                outlook_email = st.text_input(
                    "Outlook/Office Email",
                    placeholder="your.email@company.com",
                    key="outlook_email_input"
                )
                
                outlook_password = st.text_input(
                    "Password or App Password",
                    type="password",
                    placeholder="Your password",
                    key="outlook_password_input"
                )
            
            else:  # sendgrid
                st.markdown("""
                **SendGrid Setup (Most Professional):**
                
                1. Create free account at [sendgrid.com](https://sendgrid.com)
                2. Create API Key
                3. Set environment variable: `SENDGRID_API_KEY`
                   
                Or paste API key below:
                """)
                
                sendgrid_api_key = st.text_input(
                    "SendGrid API Key",
                    type="password",
                    placeholder="SG.xxxxx...",
                    key="sendgrid_api_key_input"
                )
        
        # Step 3: Email Recipients
        st.markdown("### Step 3️⃣ : Email Recipients")
        
        recipients_input = st.text_area(
            "Email addresses (one per line)",
            placeholder="john@example.com\njane@example.com\nbob@example.com",
            height=150,
            key="email_recipients_input",
            help="Enter one email address per line"
        )
        
        # Parse recipients
        recipients = [email.strip() for email in recipients_input.split('\n') if email.strip()]
        if recipients:
            st.success(f"✅ {len(recipients)} recipient(s) added")
        
        # Step 4: Email Content
        st.markdown("### Step 4️⃣ : Email Content")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            email_subject = st.text_input(
                "Email Subject",
                value="Resume for Your Review",
                key="email_subject_input"
            )
        
        with col2:
            resume_to_send = st.selectbox(
                "Select Resume",
                options=list(st.session_state.email_tab_resumes.keys()) if st.session_state.email_tab_resumes else ["No resumes loaded"],
                key="resume_to_send_select"
            )
        
        email_body = st.text_area(
            "Email Message",
            value="""Dear Hiring Manager,

Please find my resume attached for your review.

Thank you for your time and consideration.

Best regards,
Your Name""",
            height=200,
            key="email_body_input"
        )
        
        # Step 5: Send Emails
        st.markdown("### Step 5️⃣ : Send Emails")
        
        if st.button("🚀 Send Emails", use_container_width=True, key="send_emails_button"):
            if not recipients:
                st.error("❌ Please add at least one recipient")
            elif not resume_to_send or resume_to_send == "No resumes loaded":
                st.error("❌ Please load and select a resume")
            elif email_provider == "gmail" and (not gmail_email or not gmail_password):
                st.error("❌ Please enter Gmail email and App Password")
            elif email_provider == "outlook" and (not outlook_email or not outlook_password):
                st.error("❌ Please enter Outlook email and password")
            else:
                with st.spinner("Sending emails..."):
                    try:
                        # Get email sender
                        if email_provider == "gmail":
                            sender = get_email_sender("gmail", 
                                                     sender_email=gmail_email,
                                                     app_password=gmail_password)
                        elif email_provider == "outlook":
                            sender = get_email_sender("outlook",
                                                     sender_email=outlook_email,
                                                     password=outlook_password)
                        else:
                            sender = get_email_sender("sendgrid",
                                                     api_key=sendgrid_api_key if sendgrid_api_key else None)
                        
                        if not sender:
                            st.error("❌ Failed to initialize email sender")
                        else:
                            # Get resume from cloud storage
                            storage_manager = get_cloud_storage_manager(cloud_provider)
                            resume_info = st.session_state.email_tab_resumes[resume_to_send]
                            resume_content = storage_manager.download_file(resume_info['path'])
                            
                            if not resume_content:
                                st.error("❌ Failed to download resume from cloud storage")
                            else:
                                # Send to each recipient
                                success_count = 0
                                failed_recipients = []
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for idx, recipient in enumerate(recipients):
                                    status_text.text(f"Sending to {recipient} ({idx + 1}/{len(recipients)})...")
                                    
                                    # Download fresh copy of resume for each recipient
                                    resume_content.seek(0)
                                    
                                    success = sender.send_email(
                                        recipient=recipient,
                                        subject=email_subject,
                                        body=email_body,
                                        attachments=[(resume_to_send, resume_content)]
                                    )
                                    
                                    if success:
                                        success_count += 1
                                        st.session_state.email_history.append({
                                            "recipient": recipient,
                                            "resume": resume_to_send,
                                            "timestamp": pd.Timestamp.now(),
                                            "status": "Success"
                                        })
                                    else:
                                        failed_recipients.append(recipient)
                                        st.session_state.email_history.append({
                                            "recipient": recipient,
                                            "resume": resume_to_send,
                                            "timestamp": pd.Timestamp.now(),
                                            "status": "Failed"
                                        })
                                    
                                    progress_bar.progress((idx + 1) / len(recipients))
                                
                                status_text.empty()
                                progress_bar.empty()
                                
                                # Results summary
                                st.success(f"✅ Successfully sent to {success_count}/{len(recipients)} recipients")
                                
                                if failed_recipients:
                                    st.warning(f"⚠️ Failed to send to: {', '.join(failed_recipients)}")
                    
                    except Exception as e:
                        st.error(f"❌ Error sending emails: {str(e)}")
                        with st.expander("Technical Details"):
                            st.code(str(e))
        
        # Email History
        st.markdown("### 📋 Email History")
        if st.session_state.email_history:
            history_df = pd.DataFrame(st.session_state.email_history)
            st.dataframe(history_df, use_container_width=True)
            
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.email_history = []
                st.rerun()
        else:
            st.info("No emails sent yet")
    
    with tab7:
        st.markdown("## 🚀 Complete Resume Automation")
        st.markdown("""
        **One-Click Automation:** Job Description → Auto-Select Resume → Generate Points → Inject → Download
        """)
        
        # Use cached workflow (same instance for entire session)
        workflow = get_automation_workflow()
        
        # STEP 0: Resume Storage Location
        st.markdown("### 📂 Step 0: Resume Storage Location")
        
        storage_option = st.radio(
            "Where are your resumes stored?",
            options=["local", "google_drive", "onedrive", "neon", "upload"],
            format_func=lambda x: {
                "local": "💻 Local Folder (./resumes/)",
                "google_drive": "🔵 Google Drive (Shared Team)",
                "onedrive": "☁️ OneDrive (Personal/Company)",
                "neon": "🐘 Neon PostgreSQL (Database)",
                "upload": "📤 Upload Files Now"
            }[x],
            horizontal=True,
            key="resume_storage_location"
        )
        
        # Show instructions for each storage option
        with st.expander("📖 How to Store Resumes", expanded=storage_option=="upload"):
            if storage_option == "local":
                st.markdown("""
                **Local Storage (Your Computer):**
                1. Create folder: `./resumes/`
                2. Add resume files with format: `PersonName_Tech1_Tech2.docx`
                   - Example: `John_Python_Django.docx`
                   - Example: `John_React_Node.docx`
                3. Add Word bookmarks to your resume sections
                4. Run: `python setup_resumes.py`
                5. System automatically detects and registers all resumes
                """)
            
            elif storage_option == "google_drive":
                st.markdown("""
                **Google Drive (Team Resumes):**
                1. Create folder in Google Drive: "Resumes"
                2. Upload resume files
                3. Right-click folder → Share → Get shareable link
                4. In app: Add Google Drive API credentials
                5. System auto-syncs from shared folder
                
                **Setup in .env:**
                ```
                GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
                ```
                
                Get folder ID from URL: 
                `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
                """)
            
            elif storage_option == "onedrive":
                st.markdown("""
                **OneDrive (Company/Personal):**
                1. Create folder: "Resumes" in OneDrive root
                2. Upload all resume files
                3. Share folder with team (if needed)
                4. System auto-syncs from folder
                
                **Setup in .env:**
                ```
                ONEDRIVE_FOLDER_PATH=/Resumes
                ```
                
                **For Company Account:**
                - Use Office 365 credentials
                - Set folder in SharePoint
                """)
            
            elif storage_option == "neon":
                st.markdown("""
                **Neon PostgreSQL (Database):**
                1. Create free account at neon.tech
                2. Create database
                3. Copy connection string
                4. Add to .env:
                   ```
                   DATABASE_URL=postgresql://user:password@host:5432/db
                   AWS_S3_BUCKET=resume-files
                   ```
                5. Run setup:
                   ```
                   python setup_neon.py
                   ```
                6. Upload resumes (auto-stores metadata in Neon)
                
                **Best for:**
                - Teams sharing resume catalog
                - Tracking resume versions
                - Multiple users, one database
                - Production deployments
                """)
            
            elif storage_option == "upload":
                st.markdown("""
                **Upload Files (One-Time):**
                1. Select your resume files
                2. Files stored in app session
                3. Use with current job application
                4. Files clear after app refresh
                
                **For Persistent Storage:**
                Use Local, Google Drive, OneDrive, or Neon instead
                """)
        
        # NEON STORAGE: User authentication & resume upload
        if storage_option == "neon":
            st.markdown("### 🔐 Neon Account & Resume Upload")
            
            # Use cached Neon manager (same instance for entire session)
            neon_mgr = get_neon_manager()
            
            if not neon_mgr:
                st.error("❌ Neon database not configured on server")
                st.stop()
            
            # User email for identification
            user_email = st.text_input(
                "Your Email Address",
                placeholder="your.email@example.com",
                key="neon_user_email",
                help="Used to identify your resume collection"
            )
            
            if user_email and '@' in user_email:
                # Show user's existing resumes
                st.markdown("#### 📄 Your Resumes")
                
                # Cache user resumes in session state
                cache_key = f"neon_resumes_{user_email}"
                if cache_key not in st.session_state or st.session_state.get('force_reload_neon', False):
                    success, user_resumes = neon_mgr.get_user_resumes(user_email)
                    st.session_state[cache_key] = user_resumes
                    st.session_state.force_reload_neon = False
                else:
                    user_resumes = st.session_state[cache_key]
                
                if user_resumes:
                    st.success(f"✅ You have {len(user_resumes)} resume(s) in database")
                    
                    with st.expander("View Your Resumes", expanded=True):
                        for resume in user_resumes:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                techs = ", ".join(resume['technologies']) if resume['technologies'] else "N/A"
                                st.write(f"📄 **{resume['filename']}**")
                                st.caption(f"Tech: {techs} | Size: {resume['size']/1024:.1f}KB")
                            
                            with col2:
                                if st.button("📥", key=f"download_{resume['id']}", help="Download"):
                                    success, content = neon_mgr.get_resume_file(resume['id'])
                                    if success:
                                        st.download_button(
                                            label="Download",
                                            data=content.getvalue(),
                                            file_name=resume['filename'],
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                            key=f"dl_{resume['id']}"
                                        )
                            
                            with col3:
                                if st.button("🗑️", key=f"delete_{resume['id']}", help="Delete"):
                                    success, msg = neon_mgr.delete_resume(resume['id'], user_email)
                                    if success:
                                        st.session_state.force_reload_neon = True
                                        st.success("Resume deleted")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                else:
                    st.info("No resumes yet. Upload your first resume below!")
                
                # Upload new resume
                st.markdown("#### ⬆️ Upload New Resume")
                
                uploaded_file = st.file_uploader(
                    "Choose a resume file",
                    type=["docx"],
                    key="neon_resume_upload"
                )
                
                if uploaded_file:
                    if st.button("💾 Save to Neon Database", use_container_width=True, key="neon_save_button"):
                        with st.spinner("Uploading to database..."):
                            success, msg = neon_mgr.upload_resume(
                                uploaded_file,
                                uploaded_file.name,
                                user_email
                            )
                            
                            if success:
                                st.session_state.force_reload_neon = True
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Enter your email to get started")
        
        # Load resumes based on storage option
        elif storage_option == "upload":
            uploaded_files = st.file_uploader(
                "Upload Your Resumes",
                type=["docx"],
                accept_multiple_files=True,
                key="resume_upload_files"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} resume(s) selected")
                # Store in session for use
                st.session_state.uploaded_resumes = {f.name: f for f in uploaded_files}
        
        # Show resume catalog
        st.markdown("### 📋 Resume Catalog")
        
        if storage_option == "neon":
            # Show Neon catalog statistics
            stats = neon_mgr.get_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Resumes (Database)", stats.get('total_resumes', 0))
            with col2:
                st.metric("Users", stats.get('total_users', 0))
            with col3:
                st.metric("Applications", stats.get('total_jobs', 0))
            
            if stats.get('total_resumes', 0) == 0:
                st.error("❌ No resumes in database!")
                st.info("💡 Upload your resume above first")
                st.stop()
            
            # Get user's resumes from Neon for the automation
            success, user_resumes = neon_mgr.get_user_resumes(user_email) if user_email else (False, [])
            
            if not user_resumes:
                st.error("❌ No resumes in your account!")
                st.info("💡 Upload a resume above to use in automation")
                st.stop()
        else:
            # Show local/cloud catalog statistics (cached in session)
            if 'catalog_summary' not in st.session_state:
                st.session_state.catalog_summary = workflow.catalog.get_catalog_summary()
            
            summary = st.session_state.catalog_summary
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Resumes", summary['total_resumes'])
            with col2:
                st.metric("Local", summary['local_resumes'])
            with col3:
                st.metric("Technologies", len(summary['unique_technologies']))
            
            if summary['total_resumes'] == 0 and storage_option != "upload":
                st.error("❌ No resumes found in selected location!")
                st.info(f"💡 Please add resumes to your {storage_option} storage location")
                st.stop()
            elif storage_option == "upload" and not st.session_state.get('uploaded_resumes'):
                st.error("❌ No resumes uploaded!")
                st.stop()
        
        # Input section
        st.markdown("### 📝 Job Details")
        
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g., Senior Java Developer")
        with col2:
            points_per_tech = st.slider("Points per Technology", 1, 5, 2)
        
        job_description = st.text_area(
            "Job Description",
            height=250,
            placeholder="Paste job description here..."
        )
        
        recruiter_email = st.text_input("Recruiter Email", placeholder="recruiter@company.com")
        
        # Optional message
        st.markdown("### 💬 Personalized Message (Optional)")
        personal_message = st.text_area(
            "Leave blank for auto-generated message",
            height=100,
            placeholder="Hi, I'm interested in..."
        )
        
        # Run automation
        if st.button("🚀 Run Automation", use_container_width=True):
            if not job_title:
                st.error("❌ Enter job title")
            elif not job_description or len(job_description) < 50:
                st.error("❌ Job description too short (min 50 chars)")
            elif not recruiter_email or '@' not in recruiter_email:
                st.error("❌ Invalid email address")
            else:
                with st.spinner("🔄 Processing..."):
                    try:
                        # Run workflow
                        success, result = workflow.run_workflow(
                            job_description=job_description,
                            job_title=job_title,
                            points_per_tech=points_per_tech,
                            recruiter_email=recruiter_email,
                            personal_message=personal_message
                        )
                        
                        if success:
                            st.success("✅ Automation Completed!")
                            
                            # Show results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Selected Resume", result['selected_resume']['name'].split('.')[0])
                            with col2:
                                st.metric("Match Score", f"{result['match_score']:.0f}%")
                            with col3:
                                st.metric("Points Injected", 8)
                            
                            # Download button
                            resume_path = result['resume_file_path']
                            with open(resume_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download Updated Resume",
                                    data=f.read(),
                                    file_name=Path(resume_path).name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
                                )
                            
                            # Show what was generated
                            st.markdown("### 📊 Generated Points Preview")
                            with st.expander("View Generated Points"):
                                st.text(result['generated_text'][:500] + "...")
                            
                            # Show execution log
                            with st.expander("📋 Execution Log"):
                                if result.get('log_file'):
                                    import json
                                    with open(result['log_file'], 'r') as f:
                                        log_data = json.load(f)
                                        for step in log_data:
                                            st.write(f"**{step['step']}:** {step['status']}")
                        else:
                            st.error("❌ Automation failed")
                            for error in result.get('errors', []):
                                st.error(f"  - {error}")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()