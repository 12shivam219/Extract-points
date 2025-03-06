import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler

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

    # Sample input button
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

    # Show preserved processed text from previous runs
    elif st.session_state.processed_text and not process_button:
        st.subheader("Previous Output")
        st.text_area(
            "Preview",
            value=st.session_state.processed_text,
            height=300,
            key="previous_output"
        )

        # Export options for previous output
        st.subheader("Export Options")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Copy to Clipboard", key="prev_copy"):
                st.code(st.session_state.processed_text)
                st.toast("Text ready to copy!")

        with col2:
            export_handler = ExportHandler()
            docx_file = export_handler.generate_docx(st.session_state.processed_text)
            st.download_button(
                label="Download DOCX",
                data=docx_file.getvalue(),
                file_name="processed_text.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="prev_docx"
            )

        with col3:
            pdf_file = export_handler.generate_pdf(st.session_state.processed_text)
            st.download_button(
                label="Download PDF",
                data=pdf_file.getvalue(),
                file_name="processed_text.pdf",
                mime="application/pdf",
                key="prev_pdf"
            )

if __name__ == "__main__":
    main()