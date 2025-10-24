"""
Stage 1: Extract markdown and render basic LaTeX structure.
"""

import os
from typing import Dict, List, Any
from ..utils.text_processing import convert_markdown_to_latex


def create_basic_latex_structure(extracted_data: Dict[str, Any]) -> str:
    """
    Stage 1: Create basic LaTeX structure from markdown content.
    This creates the foundation without any images.
    """
    markdown_content = extracted_data.get("markdown", "")
    
    # Start with document structure
    latex_lines = [
        "\\begin{frame}{Contents}",
        "    \\tableofcontents",
        "\\end{frame}",
        ""
    ]
    
    # Handle structured data from pymupdf4llm
    if isinstance(markdown_content, list):
        # Convert list of page data to LaTeX frames
        current_frame = False
        frame_count = 0
        
        for page_data in markdown_content:
            if isinstance(page_data, dict):
                # Start new frame for each page
                if current_frame:
                    latex_lines.append("\\end{frame}")
                    current_frame = False
                
                frame_count += 1
                page_title = f"Slide {frame_count}"
                
                # Get page title from toc_items if available
                if 'toc_items' in page_data.get('metadata', {}):
                    toc_items = page_data['metadata']['toc_items']
                    if toc_items and len(toc_items) > 0:
                        page_title = toc_items[0][1] if len(toc_items[0]) > 1 else f"Slide {frame_count}"
                
                latex_lines.append(f"\\begin{{frame}}{{{page_title}}}")
                current_frame = True
                
                # Add text content
                text_content = page_data.get('text', '')
                if text_content:
                    # Convert text to LaTeX
                    from ..utils.text_processing import convert_text_to_latex
                    latex_text = convert_text_to_latex(text_content)
                    latex_lines.append(latex_text)
        
        # Close final frame
        if current_frame:
            latex_lines.append("\\end{frame}")
        
        return "\n".join(latex_lines)
    
    # Fallback for string format
    latex_content = convert_markdown_to_latex(markdown_content)
    return latex_content


def extract_page_structure(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract page structure information for image placement.
    """
    markdown_content = extracted_data.get("markdown", "")
    page_structure = []
    
    if isinstance(markdown_content, list):
        for i, page_data in enumerate(markdown_content):
            if isinstance(page_data, dict):
                page_info = {
                    'page_number': i + 1,
                    'title': f"Slide {i + 1}",
                    'content_preview': page_data.get('text', '')[:200] + "..." if len(page_data.get('text', '')) > 200 else page_data.get('text', ''),
                    'has_images': False,
                    'images': []
                }
                
                # Get page title from toc_items if available
                if 'toc_items' in page_data.get('metadata', {}):
                    toc_items = page_data['metadata']['toc_items']
                    if toc_items and len(toc_items) > 0:
                        page_info['title'] = toc_items[0][1] if len(toc_items[0]) > 1 else f"Slide {i + 1}"
                
                # Find images for this page
                for img in extracted_data.get("images", []):
                    if img.get('page', 0) == i:
                        page_info['has_images'] = True
                        page_info['images'].append({
                            'filename': os.path.basename(img['path']),
                            'path': img['path'],
                            'page': img.get('page', 0)
                        })
                
                page_structure.append(page_info)
    
    return page_structure
