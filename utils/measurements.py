"""
Unit Conversion and Scaling Utilities
"""


def cm_to_inches(cm: float) -> float:
    """Convert centimeters to inches"""
    return cm / 2.54


def inches_to_cm(inches: float) -> float:
    """Convert inches to centimeters"""
    return inches * 2.54


def real_to_pixels(cm: float, scale: float) -> int:
    """
    Convert real-world cm to canvas pixels

    Args:
        cm: Real-world measurement in centimeters
        scale: Scale factor (pixels per cm at current zoom)

    Returns:
        Pixel value
    """
    return int(cm * scale)


def pixels_to_real(pixels: int, scale: float) -> float:
    """
    Convert canvas pixels to real-world cm

    Args:
        pixels: Pixel measurement
        scale: Scale factor (pixels per cm at current zoom)

    Returns:
        Real-world measurement in centimeters
    """
    return pixels / scale if scale > 0 else 0.0


def calculate_scale_factor(canvas_width_px: int, real_width_cm: float, zoom: float = 1.0) -> float:
    """
    Calculate the scale factor for converting between real-world and pixel coordinates

    Args:
        canvas_width_px: Canvas width in pixels
        real_width_cm: Real-world width in centimeters
        zoom: Current zoom level (1.0 = 100%)

    Returns:
        Scale factor (pixels per cm)
    """
    if real_width_cm <= 0:
        return 1.0
    return (canvas_width_px / real_width_cm) * zoom


def validate_dimension(value: float, min_val: float = 0.1, max_val: float = 1000.0) -> bool:
    """
    Validate that a dimension is within reasonable bounds

    Args:
        value: Dimension to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        True if valid, False otherwise
    """
    return min_val <= value <= max_val


def calculate_aspect_ratio(width: float, height: float) -> float:
    """
    Calculate aspect ratio (width / height)

    Args:
        width: Width dimension
        height: Height dimension

    Returns:
        Aspect ratio
    """
    return width / height if height > 0 else 1.0
