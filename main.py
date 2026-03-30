import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler
from utils.batch_processor import BatchProcessor
from utils.resume_injector import ResumeInjector
from utils.batch_resume_injector import BatchResumeInjector
from utils.validators import InputValidator, MessageFormatter
from utils.deduplicator import PointDeduplicator
from utils.persistence import SettingsPersistence, RecentUsedManager
import io
import zipfile
from pathlib import Path
import pandas as pd
import logging

# Setup logging
logger = logging.getLogger(__name__)

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
    tab1, tab2, tab3, tab4 = st.tabs(["Single File Processing", "Batch Processing", "Resume Template Injection", "Batch Resume Injection"])

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
                st.error(f"❌ Unexpected error: {type(e).__name__}")
                st.info(f"Please try again or contact support if the issue persists.")
                with st.expander("Technical details"):
                    st.code(str(e))

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

if __name__ == "__main__":
    main()