#!/usr/bin/env python3
"""
Test script for PDF to LaTeX conversion.
"""

import os
import sys
from main import convert_pdf_to_latex


def test_conversion():
    """Test the PDF conversion with the first 10 pages of the provided PDF."""
    
    # Check if API key is provided
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please set GEMINI_API_KEY environment variable")
        print("Example: export GEMINI_API_KEY='your_api_key_here'")
        return False
    
    # Test with the provided PDF (first 10 pages only)
    pdf_path = "Paper_Presentation_PCA-Semireg_VaR_and_ES_models.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return False
    
    print(f"Testing conversion of: {pdf_path} (first 10 pages only)")
    print("This may take a few minutes...")
    
    # Convert PDF (first 10 pages only)
    result = convert_pdf_to_latex(pdf_path, api_key, max_pages=5)
    
    if result:
        print(f"✅ Success! Generated PDF: {result}")
        return True
    else:
        print("❌ Conversion failed!")
        return False


if __name__ == "__main__":
    success = test_conversion()
    sys.exit(0 if success else 1)
