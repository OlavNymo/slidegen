"""
Main Orchestrator
CLI interface to coordinate all modules for PDF to LaTeX conversion.
"""

import argparse
import os
import sys
import tempfile
import shutil
from typing import Optional

from extractor import extract_pdf_content, cleanup_temp_files
from converter import convert_content_to_latex
from generator import generate_latex_document
from compiler import compile_latex_to_pdf, check_latex_installation, cleanup_auxiliary_files


def convert_pdf_to_latex(pdf_path: str, api_key: str, output_dir: Optional[str] = None, max_pages: Optional[int] = None) -> Optional[str]:
    """
    Convert PDF to LaTeX Beamer presentation.
    
    Args:
        pdf_path: Path to input PDF file
        api_key: Google AI Studio API key
        output_dir: Output directory (optional, uses temp if not provided)
        max_pages: Maximum number of pages to process (optional)
        
    Returns:
        Path to generated PDF file, or None if conversion failed
    """
    # Validate input
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    
    # Check LaTeX installation
    if not check_latex_installation():
        print("Error: LaTeX (pdflatex) not found. Please install LaTeX.")
        return None
    
    # Setup output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="pdf_to_latex_")
        cleanup_temp = True
    else:
        os.makedirs(output_dir, exist_ok=True)
        cleanup_temp = False
    
    try:
        print("Step 1: Extracting PDF content...")
        extracted_data = extract_pdf_content(pdf_path, max_pages)
        
        print("Step 2: Converting content to LaTeX...")
        latex_body = convert_content_to_latex(extracted_data, api_key)
        
        print("Step 3: Generating LaTeX document...")
        tex_file_path = generate_latex_document(latex_body, extracted_data, output_dir)
        
        print("Step 4: Compiling LaTeX to PDF...")
        pdf_path = compile_latex_to_pdf(tex_file_path, output_dir)
        
        if pdf_path:
            print(f"Success! Generated PDF: {pdf_path}")
            
            # Clean up auxiliary files
            cleanup_auxiliary_files(output_dir)
            
            return pdf_path
        else:
            print("Error: Failed to compile LaTeX to PDF")
            return None
            
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return None
    finally:
        # Clean up temporary files
        cleanup_temp_files(extracted_data)
        
        # Clean up temp directory if we created it
        if cleanup_temp and os.path.exists(output_dir):
            shutil.rmtree(output_dir)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Convert PDF to LaTeX Beamer presentation")
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--api-key", required=True, help="Google AI Studio API key")
    parser.add_argument("--output-dir", help="Output directory (optional)")
    parser.add_argument("--output-pdf", help="Output PDF filename (optional)")
    
    args = parser.parse_args()
    
    # Convert PDF
    result_pdf = convert_pdf_to_latex(args.pdf_path, args.api_key, args.output_dir)
    
    if result_pdf and args.output_pdf:
        # Copy to specified output filename
        shutil.copy2(result_pdf, args.output_pdf)
        print(f"Copied to: {args.output_pdf}")
    
    if result_pdf:
        print("Conversion completed successfully!")
    else:
        print("Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
