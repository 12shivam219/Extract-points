import io
from typing import List, Dict, Tuple
from .text_processor import TextProcessor
from .export_handler import ExportHandler

class BatchProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.export_handler = ExportHandler()

    def process_files(self, files: List[io.BytesIO], points_per_cycle: int) -> List[Dict[str, Tuple[str, bytes, bytes]]]:
        """
        Process multiple text files and generate outputs in different formats.
        Returns a list of dictionaries containing processed text and exported files.
        """
        results = []

        for idx, file in enumerate(files):
            try:
                # Read and decode the file content
                content = file.getvalue().decode('utf-8')
                print(f"Processing file {idx + 1}...")  # Debug print
                print(f"Content: {content[:100]}...")  # Debug print (first 100 chars)

                # Process the text
                processed_text = self.text_processor.process_text(content, points_per_cycle)
                print(f"Processed text: {processed_text[:100]}...")  # Debug print

                # Generate exports
                docx_file = self.export_handler.generate_docx(processed_text)
                pdf_file = self.export_handler.generate_pdf(processed_text)

                # Store results
                results.append({
                    f"file_{idx + 1}": (
                        processed_text,
                        docx_file.getvalue(),
                        pdf_file.getvalue()
                    )
                })
                print(f"Successfully processed file {idx + 1}")  # Debug print

            except Exception as e:
                print(f"Error processing file {idx + 1}: {str(e)}")  # Debug print
                results.append({
                    f"file_{idx + 1}": (
                        f"Error: {str(e)}",
                        None,
                        None
                    )
                })

        return results