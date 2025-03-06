# Text Processing Application

A Streamlit-based text processing application designed to extract, reorganize, and transform structured content with multiple export capabilities.

## Features

- Interactive web interface using Streamlit
- Text parsing and restructuring with cycle-based organization
- Multiple export formats (DOCX, PDF)
- Copy to clipboard functionality
- Robust error handling and input validation

## Requirements

- Python 3.11
- Streamlit
- python-docx
- reportlab

## Usage

1. Enter or paste structured text with headings and bullet points
2. Set the number of points to extract per heading per cycle
3. Click "Process Text" to reorganize the content
4. Export the processed text in your preferred format (DOCX, PDF)

## Installation

```bash
# Install required packages
pip install streamlit python-docx reportlab
```

## Running the Application

```bash
streamlit run main.py
```
