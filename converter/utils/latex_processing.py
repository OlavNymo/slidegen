"""
Utilities for LaTeX processing and validation.
"""

import re
import os
from typing import List


def clean_latex_response(latex_content: str) -> str:
    """Normalize and sanitize LaTeX body returned by the LLM."""
    if not latex_content:
        return ""
    
    print("clean_latex_response called")
    
    # Remove markdown code fences
    if latex_content.startswith('```latex'):
        latex_content = latex_content.replace('```latex', '').replace('```', '').strip()
    
    # Remove document structure if present
    if '\\begin{document}' in latex_content:
        start_idx = latex_content.find('\\begin{document}') + len('\\begin{document}')
        end_idx = latex_content.find('\\end{document}')
        if end_idx > start_idx:
            latex_content = latex_content[start_idx:end_idx].strip()
    
    # Remove any remaining document markers
    if latex_content.strip().startswith('\\begin{document}'):
        latex_content = latex_content.replace('\\begin{document}', '', 1).strip()
    
    # Remove any trailing \end{document} markers
    latex_content = re.sub(r'\\end\{document\}.*$', '', latex_content, flags=re.MULTILINE)
    
    # Fix misplaced \centering commands - they should be inside frames
    latex_content = re.sub(r'\\centering\s*\n\s*\\includegraphics', r'\\centering\n\\includegraphics', latex_content)
    
    # Ensure \centering is properly placed within frames
    latex_content = re.sub(r'\\centering\s*\n\s*\\includegraphics([^}]+)\}\s*\n\s*\\end\{frame\}', 
                           r'\\centering\n\\includegraphics\1}\n\\end{frame}', latex_content)
    
    # Fix malformed math environments
    latex_content = _fix_math_environments(latex_content)
    
    # Fix Unicode characters that cause LaTeX errors
    latex_content = _fix_unicode_characters(latex_content)
    
    # Fix common LaTeX syntax issues
    latex_content = _fix_latex_syntax(latex_content)
    
    # Fix image paths - ensure they reference the images/ subdirectory
    latex_content = _fix_image_paths(latex_content)
    
    # Ensure proper brace matching
    latex_content = _fix_brace_matching(latex_content)
    
    return latex_content


def validate_frame_structure(latex_content: str) -> str:
    """Ensure proper frame structure and fix common issues."""
    # Count begin and end frames
    begin_frames = len(re.findall(r'\\begin\{frame\}', latex_content))
    end_frames = len(re.findall(r'\\end\{frame\}', latex_content))
    
    if begin_frames != end_frames:
        print(f"Warning: Frame mismatch - {begin_frames} begin frames, {end_frames} end frames")
    
    # Fix common frame issues
    # Remove any \centering that's not inside a frame
    lines = latex_content.split('\n')
    fixed_lines = []
    in_frame = False
    
    for line in lines:
        if '\\begin{frame}' in line:
            in_frame = True
        elif '\\end{frame}' in line:
            in_frame = False
        
        # Only allow \centering inside frames
        if '\\centering' in line and not in_frame:
            print(f"Warning: Removed \\centering outside frame: {line.strip()}")
            continue
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def remove_duplicate_images(latex_content: str) -> str:
    """Remove duplicate image references, keeping only the first occurrence of each image."""
    seen_images = set()
    lines = latex_content.split('\n')
    filtered_lines = []
    duplicates_removed = 0
    
    for line in lines:
        # Check if this line contains an includegraphics command
        if '\\includegraphics' in line:
            # Extract the image filename
            match = re.search(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', line)
            if match:
                image_path = match.group(1)
                image_filename = os.path.basename(image_path)
                
                if image_filename in seen_images:
                    duplicates_removed += 1
                    if duplicates_removed <= 10:  # Limit warning messages
                        print(f"Warning: Removed duplicate image reference: {image_filename}")
                    continue  # Skip this duplicate line
                else:
                    seen_images.add(image_filename)
        
        filtered_lines.append(line)
    
    if duplicates_removed > 10:
        print(f"Warning: Removed {duplicates_removed} duplicate image references total")
    
    return '\n'.join(filtered_lines)


def validate_and_fix_image_references(latex_content: str, available_images: List[str]) -> str:
    """Remove references to non-existent images and fix image paths."""
    # Get list of available image filenames
    available_filenames = [os.path.basename(img) for img in available_images]
    
    # Find all image references
    image_refs = re.findall(r'\\includegraphics\[([^\]]*)\]\{([^}]+)\}', latex_content)
    
    for size, path in image_refs:
        # Extract just the filename from the path
        filename = os.path.basename(path)
        
        # If the image doesn't exist, remove the entire includegraphics line
        if filename not in available_filenames:
            # Remove the entire line containing this image reference
            pattern = r'\\includegraphics\[[^\]]*\]\{[^}]*' + re.escape(filename) + r'[^}]*\}'
            latex_content = re.sub(pattern, '', latex_content)
            print(f"Warning: Removed reference to non-existent image: {filename}")
    
    return latex_content


def _fix_unicode_characters(latex_content: str) -> str:
    """Fix Unicode characters that cause LaTeX errors."""
    latex_content = latex_content.replace('−', '-')  # Unicode minus (U+2212)
    latex_content = latex_content.replace('–', '--')  # En dash
    latex_content = latex_content.replace('—', '---')  # Em dash
    return latex_content


def _fix_latex_syntax(latex_content: str) -> str:
    """Fix common LaTeX syntax issues."""
    # Fix misplaced & characters outside math mode
    latex_content = re.sub(r'([^$])\&([^$])', r'\1\\&\2', latex_content)
    
    # Fix mismatched list environments
    # Replace \begin{enumerate} that should be \begin{itemize}
    latex_content = re.sub(r'\\begin\{enumerate\}', r'\\begin{itemize}', latex_content)
    latex_content = re.sub(r'\\end\{enumerate\}', r'\\end{itemize}', latex_content)
    
    # Ensure every \begin{frame} has a matching \end{frame}
    begin_frames = len(re.findall(r'\\begin\{frame\}', latex_content))
    end_frames = len(re.findall(r'\\end\{frame\}', latex_content))
    
    if begin_frames != end_frames:
        raise ValueError(f"Frame mismatch: {begin_frames} begin frames, {end_frames} end frames")
    
    return latex_content


def _fix_math_environments(latex_content: str) -> str:
    """Fix malformed math environments."""
    # Fix malformed align* environments that contain text
    # Pattern: \begin{align*} ... \text{...} ... \end{align*}
    def fix_align_environment(match):
        content = match.group(1)
        # If the content contains \text{...}, it's likely malformed
        if '\\text{' in content:
            # Extract the math part and text parts separately
            parts = content.split('\\\\')
            math_parts = []
            text_parts = []
            
            for part in parts:
                if '\\text{' in part:
                    text_parts.append(part.strip())
                else:
                    math_parts.append(part.strip())
            
            # If we have both math and text, separate them
            if math_parts and text_parts:
                result = []
                if math_parts:
                    result.append('\\begin{align*}\n' + ' \\\\\n'.join(math_parts) + '\n\\end{align*}\n')
                if text_parts:
                    result.append('\n'.join(text_parts))
                return '\n'.join(result)
        
        return match.group(0)
    
    # Apply the fix
    latex_content = re.sub(r'\\begin\{align\*\}(.*?)\\end\{align\*\}', fix_align_environment, latex_content, flags=re.DOTALL)
    
    return latex_content


def _fix_brace_matching(latex_content: str) -> str:
    """Ensure proper brace matching."""
    # Count braces
    open_braces = latex_content.count('{')
    close_braces = latex_content.count('}')
    
    # Ensure proper brace matching
    if open_braces != close_braces:
        raise ValueError(f"Brace mismatch: {open_braces} open braces, {close_braces} close braces")
    
    return latex_content


def _fix_image_paths(latex_content: str) -> str:
    """Fix image paths to reference the images/ subdirectory."""
    # Fix double images/ paths - this is the main issue
    original_content = latex_content
    
    # Count double images paths before fixing
    double_paths_before = len(re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content))
    
    if double_paths_before > 0:
        print(f"Found {double_paths_before} double image paths to fix")
        # Show first few examples
        examples = re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content)[:3]
        for size, filename in examples:
            print(f"  Example: \\includegraphics[{size}]{{images/images/{filename}}}")
    
    # Test the replacement on a sample
    if double_paths_before > 0:
        sample = re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content)[0]
        print(f"  Sample before: \\includegraphics[{sample[0]}]{{images/images/{sample[1]}}}")
    
    latex_content = re.sub(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', 
                           r'\\includegraphics[\1]{images/\2}', 
                           latex_content)
    
    # Test the replacement on the same sample
    if double_paths_before > 0:
        sample_after = re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content)
        print(f"  Sample after: {len(sample_after)} double paths remaining")
    
    # Also fix any other double path patterns
    latex_content = re.sub(r'\\includegraphics\[([^\]]*)\]\{([^}]*)/images/([^}]+)\}', 
                           r'\\includegraphics[\1]{images/\3}', 
                           latex_content)
    
    # Handle images without images/ prefix
    latex_content = re.sub(r'\\includegraphics\[([^\]]*)\]\{([^}]*page_\d+_img_\d+\.png[^}]*)\}', 
                           r'\\includegraphics[\1]{images/\2}', 
                           latex_content)
    
    # Handle images that already have images/ prefix but wrong format
    latex_content = re.sub(r'\\includegraphics\[([^\]]*)\]\{([^}]*output/[^}]*page_\d+_img_\d+\.png[^}]*)\}', 
                           r'\\includegraphics[\1]{images/\2}', 
                           latex_content)
    
    # Count double images paths after fixing
    double_paths_after = len(re.findall(r'\\includegraphics\[([^\]]*)\]\{images/images/([^}]+)\}', latex_content))
    
    # Debug: check if any changes were made
    if double_paths_before > 0:
        fixed_count = double_paths_before - double_paths_after
        print(f"Fixed {fixed_count} double image paths in LaTeX")
    
    return latex_content
