
import io
from typing import List, Dict, Tuple
from .text_processor import TextProcessor
from .export_handler import ExportHandler

class BatchProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.export_handler = ExportHandler()

    def process_files(self, uploaded_files, points_per_heading) -> List[Dict[str, Tuple[str, bytes, bytes]]]:
        """
        Process multiple files and return their processed contents along with export formats.
        
        Returns:
            List of dictionaries mapping filename to (text_content, docx_bytes, pdf_bytes)
        """
        results = []
        
        for uploaded_file in uploaded_files:
            try:
                # Read the file content
                content = uploaded_file.read().decode('utf-8')
                filename = uploaded_file.name.split('.')[0]  # Get filename without extension
                
                # Process the text
                processed_text = self.text_processor.process_text(content, points_per_heading)
                
                # Generate export formats
                docx_file = self.export_handler.generate_docx(processed_text)
                pdf_file = self.export_handler.generate_pdf(processed_text)
                
                # Add to results
                results.append({
                    filename: (
                        processed_text,
                        docx_file.getvalue(),
                        pdf_file.getvalue()
                    )
                })
                
            except Exception as e:
                # Handle errors for individual files
                results.append({
                    uploaded_file.name: (
                        f"Error processing {uploaded_file.name}: {str(e)}",
                        None,
                        None
                    )
                })
                
        return results
