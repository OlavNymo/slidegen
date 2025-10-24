"""
Compilation Module
Handles LaTeX to PDF compilation using pdflatex.
"""

import subprocess
import os
import sys
from typing import Optional


def compile_latex_to_pdf(tex_file_path: str, output_dir: str) -> Optional[str]:
    """
    Compile LaTeX file to PDF using pdflatex.
    
    Args:
        tex_file_path: Path to the .tex file
        output_dir: Directory containing the .tex file and dependencies
        
    Returns:
        Path to the generated PDF file, or None if compilation failed
    """
    try:
        # Change to the output directory for compilation so images can be found
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        # Get just the filename for pdflatex (since we're in the output directory)
        tex_filename = os.path.basename(tex_file_path)
        
        # Run pdflatex from output directory
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if PDF was generated (LaTeX can return non-zero exit code due to warnings)
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        if os.path.exists(pdf_filename):
            return os.path.abspath(pdf_filename)
        
        # If no PDF was generated, print error
        print(f"LaTeX compilation failed:")
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        print("LaTeX compilation timed out")
        return None
    except FileNotFoundError:
        print("pdflatex not found. Please install LaTeX (e.g., TeX Live or MiKTeX)")
        return None
    except Exception as e:
        print(f"Error during LaTeX compilation: {str(e)}")
        return None
    finally:
        # Return to original directory
        os.chdir(original_cwd)


def check_latex_installation() -> bool:
    """Check if LaTeX is installed and available."""
    try:
        result = subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def cleanup_auxiliary_files(output_dir: str) -> None:
    """Clean up auxiliary LaTeX files."""
    aux_extensions = ['.aux', '.log', '.nav', '.out', '.snm', '.toc', '.vrb']
    
    for file in os.listdir(output_dir):
        if any(file.endswith(ext) for ext in aux_extensions):
            file_path = os.path.join(output_dir, file)
            try:
                os.remove(file_path)
            except OSError:
                pass  # Ignore errors when removing files
