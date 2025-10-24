"""
Utility functions for the converter module.
"""

from .latex_processing import (
    clean_latex_response,
    validate_frame_structure,
    remove_duplicate_images,
    validate_and_fix_image_references
)
from .text_processing import (
    convert_text_to_latex,
    convert_markdown_to_latex
)

__all__ = [
    'clean_latex_response',
    'validate_frame_structure', 
    'remove_duplicate_images',
    'validate_and_fix_image_references',
    'convert_text_to_latex',
    'convert_markdown_to_latex'
]
