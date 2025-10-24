"""
Stage 2: Analyze all images and convert tables/formulas to LaTeX.
"""

import os
import base64
import re
from typing import Dict, List, Any
from ..services import GeminiService
from ..exceptions import ImageProcessingError


def analyze_all_images(extracted_data: Dict[str, Any], gemini_service: GeminiService) -> Dict[str, Any]:
    """
    Stage 2: Analyze all images and decide what to convert vs keep.
    """
    images = extracted_data.get("images", [])
    if not images:
        return {"image_decisions": {}}
    
    # Prepare images for analysis
    images_with_context = []
    for img_data in images:
        if os.path.exists(img_data["path"]):
            images_with_context.append({
                "filename": os.path.basename(img_data["path"]),
                "page": img_data["page"] + 1,
                "path": img_data["path"],
                "mime_type": "image/png"
            })
    
    # Create analysis prompt
    analysis_prompt = create_image_analysis_prompt(extracted_data, images_with_context)
    
    # Analyze images using Gemini
    response = gemini_service.analyze_images(analysis_prompt, images_with_context)
    
    # Parse response
    plan = parse_image_analysis_response(response, images_with_context)
    
    return plan


def create_image_analysis_prompt(extracted_data: dict, images: list) -> str:
    """Create the image analysis prompt."""
    structure = _extract_presentation_structure(extracted_data.get("markdown", ""))
    image_list = _create_image_list(images)
    
    return f"""
You are analyzing images from a PDF presentation to determine the best processing strategy.

{structure}

IMAGES TO ANALYZE:
{image_list}

FOR EACH IMAGE, decide one of these actions:

1. CONVERT_TO_LATEX - if the image contains:
   - Text that should be converted to LaTeX
   - Tables that should be converted to LaTeX tables
   - Mathematical formulas or equations
   - Simple diagrams that can be recreated in LaTeX
   - Flowcharts or process diagrams

2. KEEP_AS_IMAGE - if the image contains:
   - Complex charts, graphs, or plots
   - Photos or screenshots
   - Complex diagrams that cannot be easily recreated
   - Visual elements that are essential to keep as images

3. REMOVE - if the image is:
   - Decorative or redundant
   - Low quality or unclear
   - Not relevant to the presentation content

RESPONSE FORMAT (JSON):
{{
  "image_decisions": {{
    "filename.png": {{
      "action": "CONVERT_TO_LATEX|KEEP_AS_IMAGE|REMOVE",
      "reasoning": "Brief explanation of decision",
      "latex_content": "LaTeX code if CONVERT_TO_LATEX, null otherwise",
      "image_type": "table|formula|diagram|chart|photo|other",
      "complexity": "simple|medium|complex"
    }}
  }}
}}
"""


def parse_image_analysis_response(response_content: str, images: List[Dict]) -> Dict[str, Any]:
    """Parse the LLM response from image analysis."""
    # Extract JSON from the response
    json_start = response_content.find('{')
    json_end = response_content.rfind('}') + 1
    
    if json_start == -1 or json_end <= json_start:
        raise ValueError("No valid JSON found in image analysis response")
    
    json_str = response_content[json_start:json_end]
    import json
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"JSON string: {json_str[:500]}...")
        
        # Try to fix common JSON issues
        # Fix unescaped backslashes
        json_str = json_str.replace('\\', '\\\\')
        
        # Fix missing commas between objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        
        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e2:
            print(f"Still failed after fixes: {e2}")
            # Return a minimal valid response
            return {"image_decisions": {}}




def _extract_presentation_structure(markdown_content) -> str:
    """Extract the logical structure of the presentation."""
    if isinstance(markdown_content, list):
        # Handle pymupdf4llm page chunks
        structure = "PRESENTATION OUTLINE:\n"
        for i, page_data in enumerate(markdown_content):
            if isinstance(page_data, dict):
                page_title = f"Page {i+1}"
                if 'toc_items' in page_data.get('metadata', {}):
                    toc_items = page_data['metadata']['toc_items']
                    if toc_items and len(toc_items) > 0:
                        page_title = toc_items[0][1] if len(toc_items[0]) > 1 else page_title
                
                # Get first few lines of content for context
                text_content = page_data.get('text', '')[:200]
                structure += f"- {page_title}: {text_content}...\n"
    else:
        # Handle string markdown
        lines = markdown_content.split('\n')
        structure = "PRESENTATION OUTLINE:\n"
        for line in lines:
            if line.startswith('#'):
                structure += f"- {line.strip()}\n"
    
    return structure


def _create_image_list(images: list) -> str:
    """Create a formatted list of images for the prompt."""
    image_list_lines = []
    for idx, img in enumerate(images):
        image_list_lines.append(f"{idx+1}. {img['filename']} (from page {img['page']})")
    return "\n".join(image_list_lines)
