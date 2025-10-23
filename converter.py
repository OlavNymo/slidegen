"""
LLM Conversion Module
Interfaces with Google Gemini API to convert extracted PDF content to LaTeX.
"""

import google.generativeai as genai
from typing import Dict, List, Any
import base64
import os
import re
from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def setup_gemini_api(api_key: str) -> None:
    """Setup Gemini API with the provided key."""
    genai.configure(api_key=api_key)


def convert_content_to_latex(extracted_data: Dict[str, Any], api_key: str) -> str:
    """
    Convert extracted PDF content to LaTeX using Gemini API.
    
    Args:
        extracted_data: Dictionary containing extracted content from PDF
        api_key: Google AI Studio API key
        
    Returns:
        LaTeX document body as string
    """
    setup_gemini_api(api_key)
    
    # Initialize the model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.1
    )
    
    # Prepare the prompt
    prompt = create_conversion_prompt(extracted_data)
    
    # Prepare images for the model
    images = []
    for img_data in extracted_data.get("images", []):
        if os.path.exists(img_data["path"]):
            with open(img_data["path"], "rb") as f:
                image_data = f.read()
                images.append({
                    "mime_type": "image/png",
                    "data": image_data
                })
    
    # Create message with text and images
    content_parts = [{"type": "text", "text": prompt}]
    
    for img in images:
        content_parts.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/png;base64,{base64.b64encode(img['data']).decode()}"}
        })
    
    message = HumanMessage(content=content_parts)
    
    # Try LLM conversion first
    try:
        response = model.invoke([message])
        latex_content = response.content
        
        # Clean up markdown formatting if present
        if latex_content.startswith('```latex'):
            # Remove markdown code block markers
            latex_content = latex_content.replace('```latex', '').replace('```', '').strip()
        
        # Remove duplicate document structure if present
        if '\\begin{document}' in latex_content:
            # Extract only the body content
            start_idx = latex_content.find('\\begin{document}') + len('\\begin{document}')
            end_idx = latex_content.find('\\end{document}')
            if end_idx > start_idx:
                latex_content = latex_content[start_idx:end_idx].strip()
        
        # Remove \begin{document} if present since the generator will add it
        if latex_content.strip().startswith('\\begin{document}'):
            latex_content = latex_content.replace('\\begin{document}', '', 1).strip()
        
        # Fix image paths - ensure they reference the images/ subdirectory
        import re
        # Fix various image path formats
        latex_content = re.sub(r'\\includegraphics\[[^\]]*\]\{([^}]*page_\d+_img_\d+\.png[^}]*)\}', 
                              r'\\includegraphics[width=0.8\\textwidth]{images/\1}', 
                              latex_content)
        # Also fix paths that might have output/ prefix
        latex_content = re.sub(r'\\includegraphics\[[^\]]*\]\{([^}]*output/[^}]*page_\d+_img_\d+\.png[^}]*)\}', 
                              r'\\includegraphics[width=0.8\\textwidth]{images/\1}', 
                              latex_content)
        
        # If no images were included by the LLM, add them explicitly
        if '\\includegraphics' not in latex_content and extracted_data.get("images"):
            print("LLM didn't include images, adding them explicitly...")
            image_frames = []
            for img_data in extracted_data["images"]:
                img_filename = os.path.basename(img_data["path"])
                frame_content = f"""
\\begin{{frame}}{{Image from Page {img_data['page'] + 1}}}
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{images/{img_filename}}}
\\end{{frame}}"""
                image_frames.append(frame_content)
            
            if image_frames:
                latex_content += "\\n\\n" + "\\n".join(image_frames)
        
        return latex_content
        
    except Exception as e:
        print(f"Error in LLM conversion: {str(e)}")
        print("Falling back to basic LaTeX generation")
        return create_fallback_latex(extracted_data)


def create_conversion_prompt(extracted_data: Dict[str, Any]) -> str:
    """Create the prompt for Gemini API."""
    markdown_content = extracted_data.get("markdown", "")
    total_pages = extracted_data.get("total_pages", 0)
    images = extracted_data.get("images", [])
    
    # Handle markdown_content being a list of page chunks
    if isinstance(markdown_content, list):
        # Join the text content from each page chunk
        content_parts = []
        for page_data in markdown_content:
            if isinstance(page_data, dict) and 'text' in page_data:
                content_parts.append(page_data['text'])
            else:
                content_parts.append(str(page_data))
        markdown_content = "\n\n".join(content_parts)
    
    # Create image reference information
    image_info = ""
    if images:
        image_info = "\n\nAVAILABLE IMAGES:\n"
        for img in images:
            img_filename = os.path.basename(img['path'])
            image_info += f"- {img_filename} (page {img['page'] + 1})\n"
        image_info += "\nUse these exact filenames in \\includegraphics commands."
    
    prompt = f"""
You are a LaTeX expert specializing in Beamer presentations. Convert the following PowerPoint PDF content into a well-structured LaTeX Beamer presentation.

CONTENT TO CONVERT:
- Total pages: {total_pages}
- Markdown content: {markdown_content}{image_info}

INSTRUCTIONS:
1. Create a complete LaTeX Beamer presentation body (without documentclass/preamble)
2. Use proper Beamer structure with \\section{{}}, \\subsection{{}}, \\begin{{frame}}, etc.
3. For images:
   - If an image contains text, tables, or equations: convert to LaTeX code
   - If an image is a diagram, chart, or photo: use \\includegraphics with the EXACT filenames listed above
4. Maintain the original presentation flow and hierarchy
5. Use appropriate Beamer blocks (block, alertblock, exampleblock) for emphasis
6. Ensure all text is properly escaped for LaTeX
7. Include proper frame titles and structure

OUTPUT FORMAT:
Return ONLY the LaTeX body content (between \\begin{{document}} and \\end{{document}}).
Do NOT include:
- Documentclass, usepackage, or other preamble commands
- \\begin{{document}} or \\end{{document}} markers
- Markdown code block markers (```latex or ```)
- Title, author, or date commands (these are handled separately)

Focus on creating a professional, well-structured presentation that maintains the original content's meaning and flow.
"""
    return prompt


def create_fallback_latex(extracted_data: Dict[str, Any]) -> str:
    """Create a basic LaTeX structure as fallback."""
    markdown_content = extracted_data.get("markdown", "")
    images = extracted_data.get("images", [])
    
    # Start with document structure
    latex_lines = [
        "\\begin{document}",
        "\\maketitle",
        "",
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
                    latex_text = convert_text_to_latex(text_content)
                    latex_lines.append(latex_text)
                
                # Add images for this page
                page_num = page_data.get('metadata', {}).get('page', 0)
                
                # Find all extracted images for this page (pymupdf4llm page numbers are 1-indexed)
                for extracted_img in images:
                    if extracted_img.get('page', 0) == page_num - 1:
                        img_filename = os.path.basename(extracted_img['path'])
                        latex_lines.append(f"\\includegraphics[width=0.8\\textwidth]{{images/{img_filename}}}")
        
        # Close final frame
        if current_frame:
            latex_lines.append("\\end{frame}")
        
        return "\n".join(latex_lines)
    
    # Fallback for string format
    latex_content = convert_markdown_to_latex(markdown_content)
    return latex_content


def convert_text_to_latex(text: str) -> str:
    """Convert plain text to LaTeX with proper escaping."""
    if not text:
        return ""
    
    # Convert markdown bold to LaTeX
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    
    # Escape LaTeX special characters
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('^', '\\textasciicircum{}')
    text = text.replace('_', '\\_')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('~', '\\textasciitilde{}')
    
    # Fix Unicode characters
    text = text.replace('−', '-')
    text = text.replace('–', '--')
    text = text.replace('—', '---')
    text = text.replace('"', '``')
    text = text.replace('"', "''")
    text = text.replace(''', "`")
    text = text.replace(''', "'")
    
    # Fix Greek letters
    text = text.replace('α', '$\\alpha$')
    text = text.replace('β', '$\\beta$')
    text = text.replace('γ', '$\\gamma$')
    text = text.replace('δ', '$\\delta$')
    text = text.replace('ε', '$\\varepsilon$')
    text = text.replace('ζ', '$\\zeta$')
    text = text.replace('η', '$\\eta$')
    text = text.replace('θ', '$\\theta$')
    text = text.replace('ι', '$\\iota$')
    text = text.replace('κ', '$\\kappa$')
    text = text.replace('λ', '$\\lambda$')
    text = text.replace('μ', '$\\mu$')
    text = text.replace('ν', '$\\nu$')
    text = text.replace('ξ', '$\\xi$')
    text = text.replace('ο', '$\\omicron$')
    text = text.replace('π', '$\\pi$')
    text = text.replace('ρ', '$\\rho$')
    text = text.replace('σ', '$\\sigma$')
    text = text.replace('τ', '$\\tau$')
    text = text.replace('υ', '$\\upsilon$')
    text = text.replace('φ', '$\\phi$')
    text = text.replace('χ', '$\\chi$')
    text = text.replace('ψ', '$\\psi$')
    text = text.replace('ω', '$\\omega$')
    
    return text


def convert_markdown_to_latex(markdown_text: str) -> str:
    """Convert basic markdown to LaTeX syntax with proper Beamer frame structure."""
    lines = markdown_text.split('\n')
    latex_lines = []
    
    current_frame = False
    frame_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Convert markdown images to LaTeX (only if they're our custom extracted images)
        if line.startswith('![](') and line.endswith(')'):
            # Extract image path
            img_path = line[4:-1]  # Remove ![]( and )
            # Only process our custom extracted images (page_X_img_Y.png format)
            if 'page_' in img_path and '_img_' in img_path:
                # Convert to proper image path (images are copied to images/ subdirectory)
                img_filename = os.path.basename(img_path)
                latex_lines.append(f"\\includegraphics[width=0.8\\textwidth]{{images/{img_filename}}}")
            # Skip pymupdf4llm images (Paper-Presentation-... format)
            continue
        
        # Convert markdown bold to LaTeX (handle multiple bold sections)
        line = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', line)
        
        # Fix LaTeX special characters
        line = line.replace('&', '\\&')  # Escape ampersands
        line = line.replace('%', '\\%')  # Escape percent signs
        line = line.replace('$', '\\$')  # Escape dollar signs
        line = line.replace('#', '\\#')  # Escape hash signs
        line = line.replace('^', '\\textasciicircum{}')  # Escape carets
        line = line.replace('_', '\\_')  # Escape underscores
        line = line.replace('{', '\\{')  # Escape braces
        line = line.replace('}', '\\}')  # Escape braces
        line = line.replace('~', '\\textasciitilde{}')  # Escape tildes
        
        # Fix Unicode characters
        line = line.replace('−', '-')  # Unicode minus to regular minus
        line = line.replace('–', '--')  # En dash to double hyphen
        line = line.replace('—', '---')  # Em dash to triple hyphen
        line = line.replace('"', '``')  # Smart quotes
        line = line.replace('"', "''")  # Smart quotes
        line = line.replace(''', "'")  # Smart apostrophe
        line = line.replace(''', "'")  # Smart apostrophe
        
        # Fix Greek letters (common in mathematical text)
        line = line.replace('α', '$\\alpha$')  # Greek alpha
        line = line.replace('β', '$\\beta$')   # Greek beta
        line = line.replace('γ', '$\\gamma$')  # Greek gamma
        line = line.replace('δ', '$\\delta$')  # Greek delta
        line = line.replace('ε', '$\\varepsilon$')  # Greek epsilon
        line = line.replace('ζ', '$\\zeta$')   # Greek zeta
        line = line.replace('η', '$\\eta$')    # Greek eta
        line = line.replace('θ', '$\\theta$')  # Greek theta
        line = line.replace('ι', '$\\iota$')   # Greek iota
        line = line.replace('κ', '$\\kappa$')  # Greek kappa
        line = line.replace('λ', '$\\lambda$') # Greek lambda
        line = line.replace('μ', '$\\mu$')     # Greek mu
        line = line.replace('ν', '$\\nu$')     # Greek nu
        line = line.replace('ξ', '$\\xi$')     # Greek xi
        line = line.replace('ο', '$\\omicron$') # Greek omicron
        line = line.replace('π', '$\\pi$')     # Greek pi
        line = line.replace('ρ', '$\\rho$')    # Greek rho
        line = line.replace('σ', '$\\sigma$')  # Greek sigma
        line = line.replace('τ', '$\\tau$')    # Greek tau
        line = line.replace('υ', '$\\upsilon$') # Greek upsilon
        line = line.replace('φ', '$\\phi$')    # Greek phi
        line = line.replace('χ', '$\\chi$')    # Greek chi
        line = line.replace('ψ', '$\\psi$')    # Greek psi
        line = line.replace('ω', '$\\omega$')  # Greek omega
        
        # Convert markdown headers to LaTeX sections
        if line.startswith('#'):
            # Close previous frame if open
            if current_frame:
                latex_lines.append("\\end{frame}")
                current_frame = False
            
            # Extract heading text
            heading_text = line.lstrip('#').strip()
            if heading_text:
                latex_lines.append(f"\\section{{{heading_text}}}")
                frame_count += 1
                latex_lines.append(f"\\begin{{frame}}{{Slide {frame_count}}}")
                current_frame = True
        else:
            # Regular content line
            if not current_frame:
                frame_count += 1
                latex_lines.append(f"\\begin{{frame}}{{Slide {frame_count}}}")
                current_frame = True
            
            if line:
                # Handle bibliography entries specially
                if line.startswith('\\bibitem{'):
                    # Fix ampersands in bibliography
                    line = line.replace('&', '\\&')
                latex_lines.append(line)
    
    # Close final frame if open
    if current_frame:
        latex_lines.append("\\end{frame}")
    
    return '\n'.join(latex_lines)
