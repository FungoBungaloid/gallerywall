"""
Perspective Correction Utilities
"""
import numpy as np
import cv2
from typing import List, Tuple


def apply_perspective_correction(
    image: np.ndarray,
    corner_points: List[Tuple[float, float]],
    output_width: int,
    output_height: int
) -> np.ndarray:
    """
    Apply 4-point perspective correction to an image

    Args:
        image: Input image as numpy array
        corner_points: List of 4 (x, y) tuples representing corners
                      Order: top-left, top-right, bottom-right, bottom-left
        output_width: Desired output width in pixels
        output_height: Desired output height in pixels

    Returns:
        Corrected image as numpy array
    """
    if len(corner_points) != 4:
        raise ValueError("Exactly 4 corner points required for perspective correction")

    # Convert corner points to numpy array
    src_points = np.float32(corner_points)

    # Define destination points (rectangle)
    dst_points = np.float32([
        [0, 0],
        [output_width - 1, 0],
        [output_width - 1, output_height - 1],
        [0, output_height - 1]
    ])

    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    # Apply perspective warp
    corrected = cv2.warpPerspective(
        image,
        matrix,
        (output_width, output_height),
        flags=cv2.INTER_LANCZOS4
    )

    return corrected


def order_points(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Order points in a consistent manner: top-left, top-right, bottom-right, bottom-left

    Args:
        points: List of 4 (x, y) tuples in any order

    Returns:
        Ordered list of points
    """
    if len(points) != 4:
        return points

    # Convert to numpy array for easier manipulation
    pts = np.array(points, dtype=np.float32)

    # Sum and diff to find corners
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    # Top-left will have smallest sum
    # Bottom-right will have largest sum
    # Top-right will have smallest difference
    # Bottom-left will have largest difference
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = pts[np.argmin(s)]      # top-left
    ordered[2] = pts[np.argmax(s)]      # bottom-right
    ordered[1] = pts[np.argmin(diff)]   # top-right
    ordered[3] = pts[np.argmax(diff)]   # bottom-left

    return [(float(x), float(y)) for x, y in ordered]


def validate_quadrilateral(points: List[Tuple[float, float]]) -> bool:
    """
    Validate that 4 points form a valid quadrilateral

    Args:
        points: List of 4 (x, y) tuples

    Returns:
        True if valid quadrilateral, False otherwise
    """
    if len(points) != 4:
        return False

    # Check that points are not collinear
    # Calculate the area of the quadrilateral
    pts = np.array(points, dtype=np.float32)

    # Use the shoelace formula
    area = 0.0
    for i in range(4):
        j = (i + 1) % 4
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    area = abs(area) / 2.0

    # Area should be greater than some threshold
    return area > 1.0


def calculate_corrected_dimensions(
    corner_points: List[Tuple[float, float]],
    real_width_cm: float,
    real_height_cm: float,
    max_size: int = 2000
) -> Tuple[int, int]:
    """
    Calculate appropriate output dimensions for perspective correction
    based on real-world measurements

    Args:
        corner_points: List of 4 corner points
        real_width_cm: Real-world width in cm
        real_height_cm: Real-world height in cm
        max_size: Maximum dimension in pixels

    Returns:
        (width, height) tuple in pixels
    """
    aspect_ratio = real_width_cm / real_height_cm

    # Determine dimensions based on aspect ratio
    if aspect_ratio >= 1.0:
        # Landscape or square
        width = max_size
        height = int(max_size / aspect_ratio)
    else:
        # Portrait
        height = max_size
        width = int(max_size * aspect_ratio)

    return width, height
