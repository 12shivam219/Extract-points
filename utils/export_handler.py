from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

class ExportHandler:
    def generate_docx(self, text):
        """Generate a DOCX file from the processed text."""
        doc = Document()
        
        # Add content to the document
        for line in text.split('\n'):
            if line.strip():
                # Format headings and cycles
                if line.startswith('Cycle'):
                    doc.add_heading(line, level=1)
                elif line.startswith('•'):
                    doc.add_paragraph(line, style='List Bullet')
                else:
                    doc.add_heading(line, level=2)

        # Save to memory buffer
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        return docx_buffer

    def generate_pdf(self, text):
        """Generate a PDF file from the processed text."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set up initial position
        y = height - 50
        left_margin = 50
        
        # Add content
        for line in text.split('\n'):
            if not line.strip():
                continue
                
            # Format different line types
            if line.startswith('Cycle'):
                c.setFont("Helvetica-Bold", 14)
                y -= 30
            elif line.startswith('•'):
                c.setFont("Helvetica", 12)
                line = "  " + line
            else:
                c.setFont("Helvetica-Bold", 12)
                y -= 20
            
            # Add text and move position
            c.drawString(left_margin, y, line)
            y -= 15
            
            # Check if we need a new page
            if y < 50:
                c.showPage()
                y = height - 50
                
        c.save()
        buffer.seek(0)
        return buffer
import io
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class ExportHandler:
    def __init__(self):
        pass

    def generate_docx(self, content):
        """Generate a DOCX file from the processed text."""
        document = Document()
        
        # Split the content by newlines
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Add headings and bullet points
            if line.startswith('Cycle'):
                document.add_heading(line, level=1)
            elif line.startswith('•'):
                document.add_paragraph(line, style='ListBullet')
            else:
                document.add_heading(line, level=2)
        
        # Save the document to a BytesIO object
        docx_file = io.BytesIO()
        document.save(docx_file)
        docx_file.seek(0)
        
        return docx_file

    def generate_pdf(self, content):
        """Generate a PDF file from the processed text."""
        pdf_file = io.BytesIO()
        c = canvas.Canvas(pdf_file, pagesize=letter)
        width, height = letter
        
        # Set font and margins
        c.setFont("Helvetica", 12)
        y_position = height - 50
        margin = 50
        
        # Split the content by newlines
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Cycle'):
                c.setFont("Helvetica-Bold", 16)
                c.drawString(margin, y_position, line)
                y_position -= 30
                c.setFont("Helvetica", 12)
            elif line.startswith('•'):
                c.drawString(margin + 20, y_position, line)
                y_position -= 20
            else:
                c.setFont("Helvetica-Bold", 14)
                c.drawString(margin, y_position, line)
                y_position -= 25
                c.setFont("Helvetica", 12)
            
            # Check if new page is needed
            if y_position < 50:
                c.showPage()
                y_position = height - 50
        
        c.save()
        pdf_file.seek(0)
        return pdf_file
