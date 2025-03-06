import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler
from utils.batch_processor import BatchProcessor
import io
import zipfile

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
    tab1, tab2 = st.tabs(["Single File Processing", "Batch Processing"])

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

            except Exception as e:
                st.error(f"Error processing text: {str(e)}")
                st.info("Please ensure your text follows the correct format with headings and bullet points.")
                print(f"Processing error: {str(e)}")  # Debug print

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

                    except Exception as e:
                        st.error(f"Error during batch processing: {str(e)}")
                        st.info("Please ensure all files contain valid headings and bullet points.")

if __name__ == "__main__":
    main()