import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler
from utils.batch_processor import BatchProcessor
from utils.resume_injector import ResumeInjector
import io
import zipfile
import pandas as pd

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

    # Create tabs for single and batch processing
    tab1, tab2, tab3 = st.tabs(["Single File Processing", "Batch Processing", "Resume Template Injection"])

    with tab1:
        # Single file processing UI
        if st.button("Load Sample Input"):
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
            st.info("""
            ℹ️ Format Guide:
            - Each heading should be on its own line
            - Bullet points should start with •, -, *, + or a number
            - Leave a blank line between different headings
            """)
        else:
            if 'input_text' not in st.session_state:
                st.session_state.input_text = ""

        # Text input area
        input_text = st.text_area(
            "Enter your structured text (headings followed by bullet points)",
            value=st.session_state.input_text,
            height=300,
            help="Enter your text with headings and bullet points (• or -)"
        )

        # Process button and points per heading input
        col1, col2 = st.columns([2, 1])
        with col1:
            points_per_heading = st.number_input(
                "Number of points to extract per heading per cycle",
                min_value=1,
                max_value=10,
                value=2
            )

        with col2:
            process_button = st.button("Process Text")

        # Process text when button is clicked
        if process_button and input_text:
            try:
                # Create a spinner to show processing status
                with st.spinner('Processing text...'):
                    processor = TextProcessor()
                    processed_content = processor.process_text(input_text, points_per_heading)

                    if processed_content:
                        st.session_state.processed_text = processed_content
                        st.session_state.input_text = input_text  # Preserve input text

                        st.success("Text processed successfully!")

                        # Display processed output in a container
                        with st.container():
                            st.subheader("Processed Output")
                            st.text_area(
                                "Preview",
                                value=processed_content,
                                height=300,
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
        st.subheader("Batch Text Processing")
        st.markdown("""
        Upload multiple text files to process them all at once.
        Each file should contain structured text with headings and bullet points.
        """)

        uploaded_files = st.file_uploader(
            "Upload text files",
            type=['txt'],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.info(f"Found {len(uploaded_files)} files to process")

            points_per_heading_batch = st.number_input(
                "Number of points to extract per heading per cycle (batch)",
                min_value=1,
                max_value=10,
                value=2,
                key="batch_points"
            )

            if st.button("Process Batch"):
                with st.spinner('Processing files...'):
                    try:
                        batch_processor = BatchProcessor()
                        results = batch_processor.process_files(uploaded_files, points_per_heading_batch)

                        if results:
                            st.success(f"Successfully processed {len(results)} files!")

                            # Display individual results
                            for result in results:
                                for filename, (text, docx, pdf) in result.items():
                                    st.subheader(f"Results for {filename}")
                                    if isinstance(text, str) and text.startswith("Error"):
                                        st.error(text)
                                    else:
                                        st.text_area(
                                            "Processed Text",
                                            value=text,
                                            height=200,
                                            key=f"batch_{filename}"
                                        )
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if docx:
                                                st.download_button(
                                                    label=f"Download {filename}.docx",
                                                    data=docx,
                                                    file_name=f"{filename}.docx",
                                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                    key=f"{filename}_docx"
                                                )
                                        with col2:
                                            if pdf:
                                                st.download_button(
                                                    label=f"Download {filename}.pdf",
                                                    data=pdf,
                                                    file_name=f"{filename}.pdf",
                                                    mime="application/pdf",
                                                    key=f"{filename}_pdf"
                                                )

                            # Create ZIP file for batch download
                            st.subheader("Download All Results")
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                                for result in results:
                                    for filename, (text, docx, pdf) in result.items():
                                        if isinstance(text, str) and not text.startswith("Error"):
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
                                key="batch_zip"
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
        st.subheader("Resume Template Injection")
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
        
        # Profile Management Section
        st.markdown("### 📁 Bookmark Profiles (Optional)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 View Saved Profiles"):
                profiles = bm_manager.list_profiles()
                if profiles:
                    st.write("**Saved Profiles:**")
                    for profile in profiles:
                        st.write(f"- **{profile['name']}** ({profile['resume_name']}) - {profile['bookmarks_count']} bookmarks")
                else:
                    st.info("No saved profiles yet")
        
        # Step 1: Upload resume template
        st.markdown("### Step 1: Upload Resume Template")
        resume_file = st.file_uploader(
            "Upload your resume template (DOCX with bookmarks)",
            type=['docx'],
            key="resume_upload"
        )
        
        detected_bookmarks = []
        resume_bytes = None
        
        if resume_file:
            try:
                resume_bytes = io.BytesIO(resume_file.read())
                injector = ResumeInjector()
                detected_bookmarks = injector.get_available_bookmarks(resume_bytes)
                
                st.success(f"✅ Resume template loaded")
                st.info(f"📌 Found **{len(detected_bookmarks)}** bookmark(s)")
                
                # Display bookmarks
                expander = st.expander("View detected bookmarks", expanded=False)
                with expander:
                    for i, bm in enumerate(detected_bookmarks, 1):
                        st.write(f"{i}. `{bm}`")
                
                # Option to load existing profile
                st.markdown("#### Load Profile (Optional)")
                profiles = bm_manager.list_profiles()
                if profiles:
                    profile_names = [p['name'] for p in profiles]
                    selected_profile = st.selectbox(
                        "Load a saved profile:",
                        ["Custom mapping"] + profile_names,
                        key="profile_select"
                    )
                    
                    if selected_profile != "Custom mapping":
                        profile_data = bm_manager.load_profile(selected_profile)
                        if profile_data:
                            st.success(f"✓ Profile loaded: {selected_profile}")
                            st.info(f"Contains {len(profile_data.get('mapping', {}))} cycle mappings")
                
                resume_bytes.seek(0)
                
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
                    height=250,
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
                        processed_text = text_file.read().decode('utf-8')
                    except Exception as e:
                        st.error(f"❌ Error reading text file: {str(e)}")
            
            if processed_text and processed_text.strip():
                # Extract cycles from text
                import re
                cycle_matches = re.findall(r'Cycle\s+(\d+):', processed_text, re.IGNORECASE)
                num_cycles = len(set(cycle_matches)) if cycle_matches else 0
                
                if num_cycles > 0:
                    st.markdown(f"### Step 3: Map Cycles to Bookmarks ({num_cycles} cycles found)")
                    
                    # Auto-suggest mapping
                    suggested_mapping = bm_manager.suggest_mappings(detected_bookmarks, num_cycles)
                    
                    # ⚠️ MISMATCH DETECTION & HANDLING
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
                            selected_bookmark = st.selectbox(
                                f"Cycle {cycle_num}",
                                detected_bookmarks,
                                index=detected_bookmarks.index(suggested_mapping.get(cycle_num, detected_bookmarks[0]))
                                if suggested_mapping.get(cycle_num) in detected_bookmarks else 0,
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
                    
                    # Mismatch handling options
                    if has_mismatch and num_cycles < len(detected_bookmarks):
                        st.markdown("#### 🔧 Handling Unused Bookmarks")
                        unused_handling = st.radio(
                            "What should happen with unused bookmarks?",
                            [
                                "Keep original content (default)",
                                "Repeat last cycle content",
                                "Clear content"
                            ],
                            index=0,
                            help="Choose how to handle bookmarks that don't have matching cycles"
                        )
                        
                        if unused_handling != "Keep original content (default)":
                            st.info(f"ℹ️ Unused bookmarks: {', '.join([b for b in detected_bookmarks if b not in custom_mapping.values()])}")
                    else:
                        unused_handling = "Keep original content (default)"
                    
                    # Save profile option
                    st.markdown("#### Save this Mapping as Profile (Optional)")
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
                    
                    # Step 4: Inject and download
                    st.markdown("### Step 4: Inject and Download")
                    
                    if st.button("✨ Inject Points into Resume", type="primary"):
                        with st.spinner('Injecting points...'):
                            try:
                                resume_bytes.seek(0)
                                injector = ResumeInjector()
                                
                                # Suppress debug output
                                import sys
                                from io import StringIO
                                
                                old_stdout = sys.stdout
                                sys.stdout = StringIO()
                                
                                try:
                                    updated_resume, injections = injector.inject_points_into_resume(
                                        resume_bytes,
                                        processed_text,
                                        custom_mapping=custom_mapping
                                    )
                                finally:
                                    sys.stdout = old_stdout
                                
                                st.success("✅ Points injected successfully!")
                                
                                # Show summary
                                st.subheader("Injection Summary")
                                for bookmark, count in injections.items():
                                    st.info(f"📌 **{bookmark}**: {count} points added")
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Updated Resume",
                                    data=updated_resume.getvalue(),
                                    file_name="Resume_Updated.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="resume_download"
                                )
                                
                            except ValueError as e:
                                st.error(f"❌ Format Error: {str(e)}")
                                st.warning("Debug Info:")
                                with st.expander("Show debug details"):
                                    st.text(f"Text length: {len(processed_text)} chars")
                                    st.text(f"First 300 chars:\n{processed_text[:300]}")
                                st.info("Tips:")
                                st.info("• Text must have 'Cycle 1:', 'Cycle 2:', etc.")
                                st.info("• Use Tab 1 to process text first")
                                st.info("• Copy entire output from Tab 1")
                            except Exception as e:
                                st.error(f"❌ Injection Failed: {str(e)}")
                                st.warning("Troubleshooting:")
                                with st.expander("Show debug info"):
                                    st.error(f"**Error:** {type(e).__name__}")
                                    st.text(f"Message: {str(e)}")
                                    st.text(f"Text preview: {processed_text[:200]}")
                                st.info("Try:")
                                st.info("1. Process text using Tab 1")
                                st.info("2. Copy the output (with 'Cycle' labels)")
                                st.info("3. Paste directly into Tab 3")
                else:
                    st.warning("⚠️ No cycles found in text. Format should be 'Cycle 1:', 'Cycle 2:', etc.")
            
            if not processed_text or not processed_text.strip():
                st.info("💡 Please provide extracted points text to proceed")

if __name__ == "__main__":
    main()