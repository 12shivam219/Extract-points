import io
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

class ExportHandler:
    def __init__(self):
        self.max_text_width = 7.5  # inches for text wrapping

    def generate_docx(self, content):
        """Generate a DOCX file from the processed text."""
        document = Document()

        # Split the content by newlines
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Add headings and regular content
            if line.startswith('Cycle'):
                document.add_heading(line, level=1)
            else:
                document.add_paragraph(line)

        # Save the document to a BytesIO object
        docx_file = io.BytesIO()
        document.save(docx_file)
        docx_file.seek(0)

        return docx_file

    def _wrap_text(self, text, max_width):
        """Wrap text to fit within max_width (in characters approximately)."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > max_width:
                if len(current_line) > 1:
                    current_line.pop()  # Remove word that caused overflow
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(' '.join(current_line))
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def generate_pdf(self, content):
        """Generate a PDF file from the processed text with proper text wrapping and pagination."""
        pdf_file = io.BytesIO()
        c = canvas.Canvas(pdf_file, pagesize=letter)
        width, height = letter

        # Set font and margins
        margin = 50
        top_margin = height - 50
        bottom_margin = 50
        y_position = top_margin
        font_size_normal = 11
        font_size_heading_cycle = 14

        # Split the content by newlines
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                # Add extra space for blank lines
                y_position -= 10
                if y_position < bottom_margin + 20:
                    c.showPage()
                    y_position = top_margin
                continue

            # Determine line type and formatting
            if line.startswith('Cycle'):
                # Cycle heading
                c.setFont("Helvetica-Bold", font_size_heading_cycle)
                wrapped_lines = self._wrap_text(line, 80)
                for wrapped_line in wrapped_lines:
                    if y_position < bottom_margin + font_size_heading_cycle:
                        c.showPage()
                        y_position = top_margin
                    c.drawString(margin, y_position, wrapped_line)
                    y_position -= font_size_heading_cycle + 5
                c.setFont("Helvetica", font_size_normal)
                y_position -= 5
                
            else:
                # Regular content line
                c.setFont("Helvetica", font_size_normal)
                wrapped_lines = self._wrap_text(line, 90)
                
                for wrapped_line in wrapped_lines:
                    if y_position < bottom_margin + font_size_normal:
                        c.showPage()
                        y_position = top_margin
                    
                    c.drawString(margin + 20, y_position, wrapped_line)
                    y_position -= font_size_normal + 4

            # Check if new page is needed
            if y_position < bottom_margin + 20:
                c.showPage()
                y_position = top_margin

        c.save()
        pdf_file.seek(0)
        return pdf_file