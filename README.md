
# Text Processing Application

A Streamlit-based text processing application designed to extract, reorganize, and transform structured content with multiple export capabilities.

## Features

- Interactive web interface using Streamlit
- Text parsing and restructuring with cycle-based organization
- Multiple export formats (DOCX, PDF)
- Copy to clipboard functionality
- Robust error handling and input validation
- Pattern matching for both bullet points and numbered lists
- Cycle-based content organization

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

1. Enter or paste structured text with headings and bullet points
2. Set the number of points to extract per heading per cycle
3. Click "Process Text" to reorganize the content
4. Use the export options to:
   - Copy to clipboard
   - Download as DOCX
   - Download as PDF

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
Heading 1
• Point 1
• Point 2

Heading 2
• Item A
• Item B
```

## Running the Application

```bash
streamlit run main.py
```

## Correct Format

Heading 1
• Point 1
• Point 2
• Point 3

Heading 2
• Item A
• Item B
• Item C

Heading 3
• Task 1
• Task 2

## Development

The application is structured as follows:
- `main.py`: Main Streamlit application
- `utils/text_processor.py`: Text processing logic
- `utils/export_handler.py`: Export functionality (DOCX, PDF)
- `.streamlit/config.toml`: Streamlit configuration

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT
