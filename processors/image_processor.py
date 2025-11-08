"""
Image Processing and Transformations
"""
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageEnhance
from typing import Tuple, Optional


class ImageProcessor:
    """Handles image corrections and transformations"""

    @staticmethod
    def load_image(file_path: str) -> Optional[np.ndarray]:
        """
        Load an image from file

        Args:
            file_path: Path to image file

        Returns:
            Image as numpy array (BGR) or None if failed
        """
        try:
            img = cv2.imread(file_path)
            if img is None:
                # Try with PIL
                pil_img = Image.open(file_path)
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    @staticmethod
    def save_image(image: np.ndarray, file_path: str) -> bool:
        """
        Save an image to file

        Args:
            image: Image as numpy array
            file_path: Path to save image

        Returns:
            True if successful, False otherwise
        """
        try:
            cv2.imwrite(file_path, image)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    @staticmethod
    def resize_image(image: np.ndarray, max_dimension: int = 2000) -> np.ndarray:
        """
        Resize image maintaining aspect ratio

        Args:
            image: Input image
            max_dimension: Maximum dimension (width or height)

        Returns:
            Resized image
        """
        height, width = image.shape[:2]

        if max(height, width) <= max_dimension:
            return image

        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        return resized

    @staticmethod
    def crop_image(image: np.ndarray, crop_box: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Crop image to specified rectangle

        Args:
            image: Input image
            crop_box: (x1, y1, x2, y2) crop coordinates

        Returns:
            Cropped image
        """
        x1, y1, x2, y2 = crop_box
        return image[y1:y2, x1:x2]

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image by specified angle

        Args:
            image: Input image
            angle: Rotation angle in degrees (positive = counterclockwise)

        Returns:
            Rotated image
        """
        height, width = image.shape[:2]
        center = (width / 2, height / 2)

        # Get rotation matrix
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new dimensions to fit rotated image
        cos = np.abs(matrix[0, 0])
        sin = np.abs(matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))

        # Adjust rotation matrix for new dimensions
        matrix[0, 2] += (new_width / 2) - center[0]
        matrix[1, 2] += (new_height / 2) - center[1]

        # Perform rotation
        rotated = cv2.warpAffine(image, matrix, (new_width, new_height),
                                 flags=cv2.INTER_LANCZOS4,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(255, 255, 255))
        return rotated

    @staticmethod
    def flip_image(image: np.ndarray, horizontal: bool = True) -> np.ndarray:
        """
        Flip image horizontally or vertically

        Args:
            image: Input image
            horizontal: If True, flip horizontally; otherwise vertically

        Returns:
            Flipped image
        """
        if horizontal:
            return cv2.flip(image, 1)
        else:
            return cv2.flip(image, 0)

    @staticmethod
    def adjust_white_balance(
        image: np.ndarray,
        temperature: float = 0.0,
        tint: float = 0.0,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0
    ) -> np.ndarray:
        """
        Adjust white balance and color properties

        Args:
            image: Input image (BGR)
            temperature: Temperature adjustment (-100 to 100, blue to yellow)
            tint: Tint adjustment (-100 to 100, green to magenta)
            brightness: Brightness adjustment (-100 to 100)
            contrast: Contrast multiplier (0.5 to 2.0)
            saturation: Saturation multiplier (0.0 to 2.0)

        Returns:
            Adjusted image
        """
        # Convert to RGB for PIL processing
        rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        # Apply brightness
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(pil_img)
            factor = 1.0 + (brightness / 100.0)
            pil_img = enhancer.enhance(factor)

        # Apply contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(contrast)

        # Apply saturation
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(pil_img)
            pil_img = enhancer.enhance(saturation)

        # Convert back to numpy array
        result = np.array(pil_img)

        # Apply temperature and tint in LAB color space
        if temperature != 0 or tint != 0:
            lab = cv2.cvtColor(result, cv2.COLOR_RGB2LAB).astype(np.float32)

            # Temperature: adjust B channel (blue-yellow)
            if temperature != 0:
                lab[:, :, 2] += temperature * 0.5

            # Tint: adjust A channel (green-magenta)
            if tint != 0:
                lab[:, :, 1] += tint * 0.5

            # Clip values and convert back
            lab = np.clip(lab, 0, 255).astype(np.uint8)
            result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        # Convert back to BGR for OpenCV
        bgr_result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        return bgr_result

    @staticmethod
    def numpy_to_pil(image: np.ndarray) -> Image.Image:
        """Convert numpy array (BGR) to PIL Image (RGB)"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    @staticmethod
    def pil_to_numpy(image: Image.Image) -> np.ndarray:
        """Convert PIL Image (RGB) to numpy array (BGR)"""
        rgb = np.array(image)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
