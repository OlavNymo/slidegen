"""
LaTeX Generation Module
Wraps LLM-generated content in NTNU Beamer template and handles image references.
"""

import os
import shutil
from typing import Dict, Any


def generate_latex_document(latex_body: str, extracted_data: Dict[str, Any], output_dir: str) -> str:
    """
    Generate complete LaTeX document with NTNU theme.
    
    Args:
        latex_body: LaTeX body content from LLM
        extracted_data: Original extracted data for image references
        output_dir: Directory to save the LaTeX file and images
        
    Returns:
        Path to the generated .tex file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy images to output directory
    copy_images_to_output(extracted_data, output_dir)
    
    # Copy NTNU theme files to output directory
    copy_ntnu_theme_files(output_dir)
    
    # Generate complete LaTeX document
    latex_content = create_complete_latex_document(latex_body)
    
    # Save LaTeX file
    tex_file_path = os.path.join(output_dir, "presentation.tex")
    with open(tex_file_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    return tex_file_path


def create_complete_latex_document(latex_body: str) -> str:
    """Create complete LaTeX document with NTNU theme."""
    
    # NTNU Beamer template preamble
    preamble = r"""
\documentclass[aspectratio=169]{beamer}
\usepackage[english]{babel}
\usepackage{booktabs,listings}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{caption}

% NTNU Theme (basic version without opensans dependency)
\usetheme[slogan=english,mathfont=serif]{NTNU_basic}

% Title information (will be updated based on content)
\title[Generated Presentation]{Generated Presentation}
\subtitle{Converted from PDF}
\author{PDF to LaTeX Converter}
\date{\today}

\begin{document}
"""
    
    # Combine preamble with body and closing
    complete_document = preamble + latex_body + "\n\\end{document}"
    
    return complete_document


def copy_images_to_output(extracted_data: Dict[str, Any], output_dir: str) -> None:
    """Copy extracted images to output directory."""
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Copy custom extracted images
    for img_data in extracted_data.get("images", []):
        if os.path.exists(img_data["path"]):
            # Create new filename
            new_filename = f"page_{img_data['page']}_img_{img_data['index']}.png"
            new_path = os.path.join(images_dir, new_filename)
            
            # Copy image
            shutil.copy2(img_data["path"], new_path)
            
            # Update the path in the data for reference
            img_data["output_path"] = new_path
    
    # Also copy pymupdf4llm images (for fallback LaTeX)
    temp_images_dir = "temp_images"
    if os.path.exists(temp_images_dir):
        for filename in os.listdir(temp_images_dir):
            if filename.endswith('.png'):
                source_path = os.path.join(temp_images_dir, filename)
                dest_path = os.path.join(images_dir, filename)
                shutil.copy2(source_path, dest_path)


def copy_ntnu_theme_files(output_dir: str) -> None:
    """Copy NTNU theme files to output directory."""
    source_theme_dir = "beamerthementnu-master"
    
    theme_files = [
        "beamerthemeNTNU_basic.sty",
        "beamercolorthemeNTNU.sty",
        "beamerinnerthemeNTNUvertical.sty",
        "beamerouterthemeNTNUvertical.sty"
    ]
    
    for theme_file in theme_files:
        source_path = os.path.join(source_theme_dir, theme_file)
        if os.path.exists(source_path):
            dest_path = os.path.join(output_dir, theme_file)
            shutil.copy2(source_path, dest_path)
    
    # Copy logo images
    logo_files = [
        "ntnu_bredde_eng.png",
        "ntnu_bredde_eng_neg.png",
        "ntnu_alt_versjon_uten_slagord_neg.png"
    ]
    
    for logo_file in logo_files:
        source_path = os.path.join(source_theme_dir, logo_file)
        if os.path.exists(source_path):
            dest_path = os.path.join(output_dir, logo_file)
            shutil.copy2(source_path, dest_path)

