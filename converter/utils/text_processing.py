"""
Utilities for text processing and LaTeX conversion.
"""

import re
import os


def convert_text_to_latex(text: str) -> str:
    """Convert plain text to LaTeX with proper escaping."""
    if not text:
        return ""
    
    # Convert markdown bold to LaTeX
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    
    # Handle math expressions - don't escape inside $...$
    text = _handle_math_expressions(text)
    
    # Escape LaTeX special characters (but not inside math mode)
    text = _escape_latex_characters_smart(text)
    
    # Fix Unicode characters
    text = _fix_unicode_characters(text)
    
    # Fix Greek letters
    text = _fix_greek_letters(text)
    
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
        line = _escape_latex_characters(line)
        
        # Fix Unicode characters
        line = _fix_unicode_characters(line)
        
        # Fix Greek letters (common in mathematical text)
        line = _fix_greek_letters(line)
        
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


def _handle_math_expressions(text: str) -> str:
    """Handle math expressions properly."""
    # Don't process text that's already in math mode
    return text


def _escape_latex_characters_smart(text: str) -> str:
    """Escape LaTeX special characters, but not inside math mode."""
    # Split text into math and non-math parts
    parts = re.split(r'(\$[^$]*\$)', text)
    result = []
    
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Non-math part
            result.append(_escape_latex_characters(part))
        else:  # Math part - don't escape
            result.append(part)
    
    return ''.join(result)


def _escape_latex_characters(text: str) -> str:
    """Escape LaTeX special characters."""
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('^', '\\textasciicircum{}')
    text = text.replace('_', '\\_')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('~', '\\textasciitilde{}')
    return text


def _fix_unicode_characters(text: str) -> str:
    """Fix Unicode characters to LaTeX equivalents."""
    text = text.replace('−', '-')  # Unicode minus (U+2212)
    text = text.replace('–', '--')  # En dash
    text = text.replace('—', '---')  # Em dash
    text = text.replace('"', '``')  # Left double quotation mark
    text = text.replace('"', "''")  # Right double quotation mark
    text = text.replace('…', '...')  # Horizontal ellipsis
    text = text.replace('°', '$^\\circ$')  # Degree symbol
    text = text.replace('×', '$\\times$')  # Multiplication sign
    text = text.replace('÷', '$\\div$')  # Division sign
    text = text.replace('±', '$\\pm$')  # Plus-minus sign
    text = text.replace('≤', '$\\leq$')  # Less than or equal to
    text = text.replace('≥', '$\\geq$')  # Greater than or equal to
    text = text.replace('≠', '$\\neq$')  # Not equal to
    text = text.replace('≈', '$\\approx$')  # Approximately equal to
    text = text.replace('∞', '$\\infty$')  # Infinity
    text = text.replace('∑', '$\\sum$')  # Summation
    text = text.replace('∏', '$\\prod$')  # Product
    text = text.replace('∫', '$\\int$')  # Integral
    text = text.replace('∂', '$\\partial$')  # Partial derivative
    text = text.replace('∇', '$\\nabla$')  # Nabla
    text = text.replace('√', '$\\sqrt{}$')  # Square root
    text = text.replace('∆', '$\\Delta$')  # Delta
    text = text.replace('∈', '$\\in$')  # Element of
    text = text.replace('∉', '$\\notin$')  # Not an element of
    text = text.replace('⊂', '$\\subset$')  # Subset of
    text = text.replace('⊃', '$\\supset$')  # Superset of
    text = text.replace('∪', '$\\cup$')  # Union
    text = text.replace('∩', '$\\cap$')  # Intersection
    text = text.replace('∅', '$\\emptyset$')  # Empty set
    text = text.replace('→', '$\\rightarrow$')  # Right arrow
    text = text.replace('←', '$\\leftarrow$')  # Left arrow
    text = text.replace('↔', '$\\leftrightarrow$')  # Left-right arrow
    text = text.replace('⇒', '$\\Rightarrow$')  # Double right arrow
    text = text.replace('⇐', '$\\Leftarrow$')  # Double left arrow
    text = text.replace('⇔', '$\\Leftrightarrow$')  # Double left-right arrow
    return text


def _fix_greek_letters(text: str) -> str:
    """Fix Greek letters to LaTeX equivalents."""
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
