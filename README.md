
# Text Processing Application

A Streamlit-based text processing application designed to extract, reorganize, and transform structured content with multiple export capabilities and resume template injection.

## Features

- **Interactive web interface** using Streamlit
- **Text parsing and restructuring** with cycle-based organization
- **Multiple export formats** (DOCX, PDF)
- **Copy to clipboard** functionality
- **Robust error handling** and input validation
- **Pattern matching** for both bullet points and numbered lists
- **Cycle-based content organization**
- **Resume Template Injection** (NEW!) - Inject extracted points directly into your resume while preserving formatting

## New Feature: Resume Template Injection

Seamlessly inject extracted points into your resume template:
- ✅ Preserves all formatting (fonts, colors, spacing, bullets)
- ✅ Adds new points while keeping existing ones
- ✅ Supports multiple companies/sections
- ✅ Uses smart heading-to-bookmark matching

See [RESUME_INJECTION_GUIDE.md](RESUME_INJECTION_GUIDE.md) for detailed instructions.

## Requirements

- Python 3.11
- Streamlit
- python-docx
- reportlab

## Installation

```bash
# Install required packages
pip install streamlit python-docx reportlab
```

## Usage

### Single File Processing
1. Enter or paste structured text with headings and bullet points
2. Set the number of points to extract per heading per cycle
3. Click "Process Text" to reorganize the content
4. Use export options to copy, download as DOCX, or download as PDF

### Batch Processing
1. Upload multiple text files
2. Set points per heading per cycle
3. Process all files at once
4. Download individual or combined results as ZIP

### Resume Template Injection (NEW!)
1. Prepare resume template with bookmarks
2. Extract points from structured text
3. Upload both files to the app
4. Download updated resume with new points injected

### Input Format
```
Heading 1
• Point 1
• Point 2
• Point 3

Heading 2
• Item A
• Item B
• Item C
```

### Output Format
```
Cycle 1:
Point 1
Item A

Cycle 2:
Point 2
Item B

Cycle 3:
Point 3
Item C
```

## Running the Application

```bash
streamlit run main.py
```

Then open your browser to `http://localhost:8501`

## Project Structure

- `main.py` - Main Streamlit application with all tabs
- `utils/text_processor.py` - Text processing logic (parsing, cycle extraction)
- `utils/export_handler.py` - Export functionality (DOCX, PDF generation)
- `utils/batch_processor.py` - Batch file processing
- `utils/resume_injector.py` - Resume template injection (NEW!)
- `RESUME_INJECTION_GUIDE.md` - Detailed resume injection documentation
- `create_resume_bookmarks.py` - Helper tool to create bookmarks in your resume

## Resume Template Preparation

To use Resume Template Injection:

### Option 1: Use Pre-Made Template
A template with bookmarks is available: `Lead Engineer_with_bookmarks.docx`

### Option 2: Create Your Own Bookmarks
Run the bookmark creation tool:
```bash
python create_resume_bookmarks.py
```

Or manually add bookmarks in Word:
1. Open your resume
2. Position cursor after the last point in a "Responsibilities" section
3. Insert → Bookmark → Enter bookmark name (e.g., `CompanyName_Responsibilities`)
4. Save the file

## Supported Bullet Formats

- `•` (bullet)
- `-` (dash)
- `*` (asterisk)
- `+` (plus)
- `1.`, `2.`, etc. (numbered)
- `(a)`, `(b)`, etc. (lettered)

## Special Features

### Underscore Filtering
Lines containing only underscores (`________`) are automatically ignored and won't appear in output.

### Error Handling
- Detailed error messages guide users to fix formatting issues
- Separate handling for format errors vs. processing errors
- Technical details available in expandable sections

## Development

Feel free to contribute improvements!

## License

[Your License Here]

## Support

For issues or questions:
1. Check the format guide in the application
2. Refer to README and RESUME_INJECTION_GUIDE documentation
3. Ensure input follows the correct format
4. Review structural requirements

MIT
