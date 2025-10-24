"""
Stage 3: Use LLM to intelligently place images in the LaTeX structure.
"""

import os
from typing import Dict, List, Any
from ..services import GeminiService
from ..exceptions import LatexGenerationError


def place_images_in_latex(basic_latex: str, page_structure: List[Dict], image_plan: Dict, gemini_service: GeminiService, extracted_data: Dict[str, Any]) -> str:
    """
    Stage 3: Use LLM to intelligently place images in the LaTeX structure.
    """
    # Prepare image placement data
    placement_data = prepare_image_placement_data(page_structure, image_plan)
    
    # Create placement prompt
    placement_prompt = create_image_placement_prompt(basic_latex, placement_data)
    
    # Get images that need to be placed
    images_to_place = get_images_to_place(image_plan, extracted_data)
    
    # Use LLM to place images
    response = gemini_service.generate_latex(placement_prompt, images_to_place)
    
    # Clean and validate the response
    from ..utils.latex_processing import clean_latex_response, validate_frame_structure
    final_latex = clean_latex_response(response)
    final_latex = validate_frame_structure(final_latex)
    
    return final_latex


def prepare_image_placement_data(page_structure: List[Dict], image_plan: Dict) -> Dict[str, Any]:
    """Prepare data for image placement."""
    decisions = image_plan.get("image_decisions", {})
    
    # Separate images by action
    images_to_place = []
    latex_conversions = []
    
    for filename, decision in decisions.items():
        action = decision.get("action")
        
        if action == "KEEP_AS_IMAGE":
            # Find the page this image came from
            for page in page_structure:
                for img in page.get('images', []):
                    if img['filename'] == filename:
                        images_to_place.append({
                            'filename': filename,
                            'page': page['page_number'],
                            'page_title': page['title'],
                            'content_preview': page['content_preview']
                        })
                        break
        
        elif action == "CONVERT_TO_LATEX" and decision.get("latex_content"):
            latex_conversions.append({
                'filename': filename,
                'latex_content': decision["latex_content"],
                'image_type': decision.get("image_type", "other")
            })
    
    return {
        'images_to_place': images_to_place,
        'latex_conversions': latex_conversions,
        'page_structure': page_structure
    }


def create_image_placement_prompt(basic_latex: str, placement_data: Dict[str, Any]) -> str:
    """Create the image placement prompt."""
    images_to_place = placement_data['images_to_place']
    latex_conversions = placement_data['latex_conversions']
    page_structure = placement_data['page_structure']
    
    # Create image list
    image_list = "\n".join([
        f"- {img['filename']} (from page {img['page']}: {img['page_title']})"
        for img in images_to_place
    ])
    
    # Create LaTeX conversions list
    conversions_list = "\n\n".join([
        f"**{conv['filename']}** ({conv['image_type']}):\n{conv['latex_content']}"
        for conv in latex_conversions
    ])
    
    return f"""
You are placing images and LaTeX conversions into a LaTeX Beamer presentation.

CURRENT LATEX STRUCTURE:
{basic_latex}

IMAGES TO PLACE:
{image_list}

LATEX CONVERSIONS TO INTEGRATE:
{conversions_list}

CRITICAL PLACEMENT STRATEGY:
1. **MANDATORY NEW FRAMES FOR IMAGES**: For EVERY image in the "IMAGES TO PLACE" list, you MUST create a completely new frame. DO NOT place images within existing frames.

2. **INTEGRATE CONVERSIONS**: Place LaTeX conversions in appropriate existing frames where they fit naturally

3. **MAINTAIN FLOW**: Ensure the presentation flows logically with new image frames inserted appropriately

4. **PROPER SIZING**: Use appropriate image sizes (width=0.7\\textwidth for most images)

STRICT INSTRUCTIONS:
1. For EACH image in the "IMAGES TO PLACE" list, create a NEW frame with:
   - A descriptive title based on the page content and image context
   - The image centered using \\centering
   - Proper image sizing: \\includegraphics[width=0.7\\textwidth]{{images/filename.png}}
   - IMPORTANT: Use exactly "images/filename.png" - do NOT use "images/images/filename.png"
   - Optional brief description if the image needs context

2. For LaTeX conversions, integrate them into existing frames where appropriate

3. Maintain the original presentation structure and flow

4. Use proper LaTeX syntax and Beamer frame structure

5. Ensure all \\begin{{frame}} have matching \\end{{frame}}

6. **DO NOT** place images within existing frames - they must get their own frames

OUTPUT FORMAT:
Return the complete LaTeX presentation body with images in NEW frames and conversions properly placed.
"""


def get_images_to_place(image_plan: Dict, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get list of images that need to be placed."""
    decisions = image_plan.get("image_decisions", {})
    images_to_place = []
    
    for filename, decision in decisions.items():
        if decision.get("action") == "KEEP_AS_IMAGE":
            # Find the actual image path from extracted data
            for img in extracted_data.get("images", []):
                if os.path.basename(img["path"]) == filename:
                    images_to_place.append({
                        "filename": filename,
                        "path": img["path"]
                    })
                    print(f"Image to place: {filename} -> {img['path']}")
                    break
    
    return images_to_place


