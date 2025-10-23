"""
PDF Extraction Module
Uses pymupdf4llm to extract all content from PDF including text, hierarchies, images, and layout.
"""

import pymupdf4llm
from typing import Dict, List, Any, Optional
import json
import os


def extract_pdf_content(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """
    Extract all content from PDF using pymupdf4llm.
    
    Args:
        pdf_path: Path to the input PDF file
        max_pages: Maximum number of pages to process (optional)
        
    Returns:
        Dictionary containing extracted content structure
    """
    try:
        # Create temp_images directory
        os.makedirs("temp_images", exist_ok=True)
        
        # Extract markdown without images (we'll extract images separately)
        md_text = pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=True,
            write_images=False  # We'll extract images separately with our own filtering
        )
        
        # Extract images separately for processing
        doc = pymupdf4llm.pymupdf.Document(pdf_path)
        images = []
        
        # Limit pages if max_pages is specified
        total_pages = len(doc)
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)
        
        for page_num in range(total_pages):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = pymupdf4llm.pymupdf.Pixmap(doc, xref)
                
                # Filter out small images and header/footer images
                if should_extract_image(pix, page_num, img_index):
                    img_path = f"temp_images/page_{page_num}_img_{img_index}.png"
                    pix.save(img_path)
                    images.append({
                        "path": img_path,
                        "page": page_num,
                        "index": img_index
                    })
        
        # Extract text blocks with positioning
        text_blocks = []
        for page_num in range(total_pages):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_blocks.append({
                                "text": span["text"],
                                "bbox": span["bbox"],
                                "font": span["font"],
                                "size": span["size"],
                                "page": page_num
                            })
        
        return {
            "markdown": md_text,
            "images": images,
            "text_blocks": text_blocks,
            "total_pages": total_pages
        }
        
    except Exception as e:
        raise Exception(f"Error extracting PDF content: {str(e)}")


def should_extract_image(pix, page_num: int, img_index: int) -> bool:
    """
    Determine if an image should be extracted based on size and position.
    Filters out header/footer images and text artifacts.
    """
    # Skip very small images (likely text artifacts)
    if pix.width < 100 or pix.height < 100:
        return False
    
    # Skip very large images that are likely full-page backgrounds
    if pix.width > 2000 or pix.height > 2000:
        return False
    
    # Skip images that are likely headers/footers (very wide and short)
    if pix.width > pix.height * 3:
        return False
    
    # Skip images that are likely text rendered as images (very tall and narrow)
    if pix.height > pix.width * 3:
        return False
    
    return True


def cleanup_temp_files(extracted_data: Dict[str, Any]) -> None:
    """Clean up temporary image files."""
    for img in extracted_data.get("images", []):
        if os.path.exists(img["path"]):
            os.remove(img["path"])
