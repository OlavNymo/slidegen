#!/usr/bin/env python3
"""
Setup script for PDF to LaTeX converter.
"""

import subprocess
import sys
import os


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def install_dependencies():
    """Install required Python packages."""
    try:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False


def check_latex():
    """Check if LaTeX is installed."""
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ LaTeX is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ LaTeX not found")
    print("Please install LaTeX:")
    print("  macOS: brew install --cask mactex")
    print("  Ubuntu: sudo apt-get install texlive-full")
    print("  Windows: Install MiKTeX")
    return False


def check_api_key():
    """Check if API key is set."""
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("✅ GEMINI_API_KEY is set")
        return True
    else:
        print("❌ GEMINI_API_KEY not set")
        print("Please set your Google AI Studio API key:")
        print("  export GEMINI_API_KEY='your_api_key_here'")
        return False


def main():
    """Run setup checks."""
    print("PDF to LaTeX Converter Setup")
    print("=" * 30)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("LaTeX", check_latex),
        ("API Key", check_api_key)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("✅ Setup complete! You can now run the converter.")
        print("\nUsage:")
        print("  python main.py input.pdf --api-key YOUR_API_KEY")
        print("  python test_conversion.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
