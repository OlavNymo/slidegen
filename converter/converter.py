"""
Main converter class for PDF to LaTeX conversion using 3-stage workflow.
"""

import os
import re
from typing import Dict, List, Any

from .exceptions import ConversionError, APIError, ValidationError
from .services import GeminiService
from .workflow import (
    create_basic_latex_structure,
    extract_page_structure,
    analyze_all_images,
    place_images_in_latex
)
from .utils import (
    clean_latex_response,
    validate_frame_structure,
    remove_duplicate_images,
    validate_and_fix_image_references
)


class PDFToLatexConverter:
    """Main converter class for PDF to LaTeX conversion."""
    
    def __init__(self, api_key: str):
        """Initialize the converter with API key."""
        self.gemini_service = GeminiService(api_key)
    
    def convert(self, extracted_data: Dict[str, Any]) -> str:
        """
        Convert extracted PDF content to LaTeX using a 3-stage approach.
        
        Stage 1: Extract markdown and render basic LaTeX structure
        Stage 2: Analyze all images and convert tables/formulas to LaTeX
        Stage 3: Use LLM to intelligently place images in LaTeX
        
        Args:
            extracted_data: Dictionary containing extracted PDF data
            
        Returns:
            LaTeX content as string
            
        Raises:
            ConversionError: If conversion fails
        """
        print("Stage 1: Creating basic LaTeX structure...")
        # Stage 1: Create basic LaTeX structure from markdown
        basic_latex = create_basic_latex_structure(extracted_data)
        page_structure = extract_page_structure(extracted_data)
        
        print("Stage 2: Analyzing images...")
        # Stage 2: Analyze all images and decide what to convert vs keep
        image_plan = analyze_all_images(extracted_data, self.gemini_service)
        
        print("Stage 3: Placing images in LaTeX...")
        # Stage 3: Use LLM to intelligently place images
        final_latex = place_images_in_latex(basic_latex, page_structure, image_plan, self.gemini_service, extracted_data)
        
        # Final validation and cleanup
        final_latex = self._finalize_latex(final_latex, extracted_data)
        
        return final_latex
    
    def _finalize_latex(self, latex_content: str, extracted_data: Dict[str, Any]) -> str:
        """Final validation and cleanup of LaTeX content."""
        print("Finalizing LaTeX content...")
        
        # Clean the response
        latex_content = clean_latex_response(latex_content)
        
        # Check if double paths are fixed after clean_latex_response
        double_paths_after_clean = len(re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content))
        print(f"Double paths after clean_latex_response: {double_paths_after_clean}")
        
        # Validate and fix image references
        available_images = extracted_data.get("images", [])
        available_image_paths = [img["path"] for img in available_images if os.path.exists(img["path"])]
        latex_content = validate_and_fix_image_references(latex_content, available_image_paths)
        
        # Check if double paths are still fixed after validate_and_fix_image_references
        double_paths_after_validate = len(re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content))
        print(f"Double paths after validate_and_fix_image_references: {double_paths_after_validate}")
        
        # Validate frame structure
        latex_content = validate_frame_structure(latex_content)
        
        # Remove duplicate images
        latex_content = remove_duplicate_images(latex_content)
        
        # Check final double paths count
        double_paths_final = len(re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content))
        print(f"Double paths final: {double_paths_final}")
        
        return latex_content
    


# Backward compatibility function
def convert_content_to_latex(extracted_data: Dict[str, Any], api_key: str) -> str:
    """
    Convert extracted PDF content to LaTeX using a two-stage approach.
    
    This function maintains backward compatibility with the old interface.
    """
    converter = PDFToLatexConverter(api_key)
    return converter.convert(extracted_data)
