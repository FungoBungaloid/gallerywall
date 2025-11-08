"""
Perspective Correction Utilities
"""
import numpy as np
import cv2
from typing import List, Tuple


def apply_perspective_correction_full_image(
    image: np.ndarray,
    corner_points: List[Tuple[float, float]],
    rect_width: int,
    rect_height: int
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Apply perspective correction to entire image while preserving context.

    This transforms the entire image based on the 4 corner points, but instead of
    cropping to just the rectangle, it preserves the full transformed image with
    whitespace/padding as needed.

    Args:
        image: Input image as numpy array
        corner_points: List of 4 (x, y) tuples representing the wall corners
                      Order: top-left, top-right, bottom-right, bottom-left
        rect_width: Desired width of the corrected rectangle (in pixels)
        rect_height: Desired height of the corrected rectangle (in pixels)

    Returns:
        Tuple of (corrected_image, rect_bounds) where rect_bounds is (x, y, width, height)
        of the corrected rectangle within the output image
    """
    if len(corner_points) != 4:
        raise ValueError("Exactly 4 corner points required for perspective correction")

    # Convert corner points to numpy array
    src_points = np.float32(corner_points)

    # Define destination points for the rectangle (starting at origin)
    dst_rect_points = np.float32([
        [0, 0],
        [rect_width - 1, 0],
        [rect_width - 1, rect_height - 1],
        [0, rect_height - 1]
    ])

    # Calculate perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_rect_points)

    # Get original image corners
    h, w = image.shape[:2]
    image_corners = np.float32([
        [0, 0],
        [w - 1, 0],
        [w - 1, h - 1],
        [0, h - 1]
    ])

    # Transform all corners of the original image to see where they end up
    # Add homogeneous coordinate
    corners_homogeneous = np.hstack([image_corners, np.ones((4, 1))])
    transformed_corners = matrix @ corners_homogeneous.T

    # Convert from homogeneous coordinates
    transformed_corners = transformed_corners[:2, :] / transformed_corners[2, :]
    transformed_corners = transformed_corners.T

    # Find bounding box of transformed image
    min_x = np.min(transformed_corners[:, 0])
    max_x = np.max(transformed_corners[:, 0])
    min_y = np.min(transformed_corners[:, 1])
    max_y = np.max(transformed_corners[:, 1])

    # Calculate output size (with some padding)
    padding = 10
    output_width = int(np.ceil(max_x - min_x)) + 2 * padding
    output_height = int(np.ceil(max_y - min_y)) + 2 * padding

    # Adjust the transform matrix to shift everything into positive coordinates
    offset_x = padding - min_x
    offset_y = padding - min_y

    translation_matrix = np.array([
        [1, 0, offset_x],
        [0, 1, offset_y],
        [0, 0, 1]
    ], dtype=np.float32)

    final_matrix = translation_matrix @ matrix

    # Apply perspective warp to entire image
    corrected = cv2.warpPerspective(
        image,
        final_matrix,
        (output_width, output_height),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)  # White padding
    )

    # Calculate where the corrected rectangle is in the output image
    rect_x = int(offset_x)
    rect_y = int(offset_y)

    return corrected, (rect_x, rect_y, rect_width, rect_height)


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
