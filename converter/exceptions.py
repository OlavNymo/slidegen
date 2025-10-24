"""
Custom exceptions for the converter module.
"""


class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass


class APIError(ConversionError):
    """Exception raised for API-related errors."""
    pass


class ValidationError(ConversionError):
    """Exception raised for validation errors."""
    pass


class ImageProcessingError(ConversionError):
    """Exception raised for image processing errors."""
    pass


class LatexGenerationError(ConversionError):
    """Exception raised for LaTeX generation errors."""
    pass
