# PDF to LaTeX Beamer Converter

A Python application that converts PowerPoint PDFs to professionally formatted LaTeX Beamer presentations using the NTNU theme.

## Features

- Extracts all content from PDFs (text, images, tables, layout)
- Uses Google Gemini API for intelligent LaTeX conversion
- Converts image-based tables/equations to LaTeX code
- Preserves diagrams and photos as images
- Applies NTNU Beamer theme for professional presentation
- Compiles to final PDF automatically

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install LaTeX (required for compilation):

   - **macOS**: `brew install --cask mactex`
   - **Ubuntu**: `sudo apt-get install texlive-full`
   - **Windows**: Install MiKTeX

3. Get Google AI Studio API key from [Google AI Studio](https://aistudio.google.com/)

## Usage

### Command Line Interface

```bash
python main.py input.pdf --api-key YOUR_API_KEY
```

### Options

- `--output-dir`: Specify output directory (optional)
- `--output-pdf`: Specify output PDF filename (optional)

### Example

```bash
python main.py "Paper Presentation PCA-Semireg VaR and ES models.pdf" --api-key YOUR_API_KEY --output-pdf converted_presentation.pdf
```

## Project Structure

- `extractor.py`: PDF content extraction using pymupdf4llm
- `converter.py`: Gemini API integration for LaTeX conversion
- `generator.py`: LaTeX document generation with NTNU theme
- `compiler.py`: PDF compilation using pdflatex
- `main.py`: Main orchestrator and CLI interface

## How It Works

1. **Extraction**: Uses pymupdf4llm to extract text, images, and layout from PDF
2. **Conversion**: Sends all content to Gemini API for intelligent LaTeX generation
3. **Generation**: Wraps LLM output in NTNU Beamer template
4. **Compilation**: Compiles LaTeX to final PDF using pdflatex

## Requirements

- Python 3.8+
- LaTeX installation (pdflatex)
- Google AI Studio API key
- Internet connection for API calls

## Error Handling

- Falls back to original images if LLM conversion fails
- Provides detailed error messages for debugging
- Cleans up temporary files automatically
