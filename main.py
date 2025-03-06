import streamlit as st
from utils.text_processor import TextProcessor
from utils.export_handler import ExportHandler
import io

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

    if process_button and input_text:
        try:
            processor = TextProcessor()
            processed_content = processor.process_text(input_text, points_per_heading)
            st.session_state.processed_text = processed_content
            
            st.success("Text processed successfully!")
        except Exception as e:
            st.error(f"Error processing text: {str(e)}")

    # Display processed text and export options
    if st.session_state.processed_text:
        st.subheader("Processed Output")
        st.text_area("Preview", value=st.session_state.processed_text, height=200)

        # Export options
        st.subheader("Export Options")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Copy to Clipboard"):
                st.toast("Copied to clipboard!")

        with col2:
            export_handler = ExportHandler()
            docx_file = export_handler.generate_docx(st.session_state.processed_text)
            st.download_button(
                label="Download DOCX",
                data=docx_file.getvalue(),
                file_name="processed_text.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        with col3:
            pdf_file = export_handler.generate_pdf(st.session_state.processed_text)
            st.download_button(
                label="Download PDF",
                data=pdf_file.getvalue(),
                file_name="processed_text.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
