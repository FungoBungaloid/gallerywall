"""
Frame and Mat Rendering
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Optional, Tuple
from models.frame import FrameConfig, MatConfig
from utils.measurements import real_to_pixels


class FrameRenderer:
    """Renders frames and mats around artwork"""

    @staticmethod
    def render_framed_artwork(
        artwork_image: np.ndarray,
        artwork_width_cm: float,
        artwork_height_cm: float,
        frame_config: FrameConfig,
        scale: float
    ) -> Image.Image:
        """
        Render artwork with frame and mat

        Args:
            artwork_image: Artwork image as numpy array (BGR)
            artwork_width_cm: Real-world artwork width in cm
            artwork_height_cm: Real-world artwork height in cm
            frame_config: Frame configuration
            scale: Scale factor (pixels per cm)

        Returns:
            Framed artwork as PIL Image (RGBA)
        """
        # Convert artwork to PIL RGB
        from processors.image_processor import ImageProcessor
        artwork_pil = ImageProcessor.numpy_to_pil(artwork_image)

        # Calculate artwork dimensions in pixels
        art_width_px = real_to_pixels(artwork_width_cm, scale)
        art_height_px = real_to_pixels(artwork_height_cm, scale)

        # Resize artwork to correct pixel dimensions
        artwork_pil = artwork_pil.resize((art_width_px, art_height_px), Image.LANCZOS)

        # Build layers from inside out
        current_layer = artwork_pil.convert('RGBA')

        # Add mat if configured
        if frame_config.mat:
            current_layer = FrameRenderer._add_mat(
                current_layer,
                frame_config.mat,
                frame_config.mat_shadow_enabled,
                frame_config.mat_shadow_blur,
                frame_config.mat_shadow_opacity,
                frame_config.mat_shadow_offset_x,
                frame_config.mat_shadow_offset_y,
                scale
            )

        # Add frame
        current_layer = FrameRenderer._add_frame(
            current_layer,
            frame_config.frame_width_cm,
            frame_config.frame_color,
            frame_config.frame_shadow_enabled,
            frame_config.frame_shadow_blur,
            frame_config.frame_shadow_opacity,
            frame_config.frame_shadow_offset_x,
            frame_config.frame_shadow_offset_y,
            scale
        )

        return current_layer

    @staticmethod
    def _add_mat(
        image: Image.Image,
        mat_config: MatConfig,
        shadow_enabled: bool,
        shadow_blur: float,
        shadow_opacity: float,
        shadow_offset_x: float,
        shadow_offset_y: float,
        scale: float
    ) -> Image.Image:
        """Add mat border around image with inner shadow"""
        # Calculate mat widths in pixels
        top_px = real_to_pixels(mat_config.top_width_cm, scale)
        bottom_px = real_to_pixels(mat_config.bottom_width_cm, scale)
        left_px = real_to_pixels(mat_config.left_width_cm, scale)
        right_px = real_to_pixels(mat_config.right_width_cm, scale)

        # Calculate new dimensions
        new_width = image.width + left_px + right_px
        new_height = image.height + top_px + bottom_px

        # Create mat layer
        mat_layer = Image.new('RGBA', (new_width, new_height), FrameRenderer._hex_to_rgba(mat_config.color))

        # Paste artwork onto mat
        mat_layer.paste(image, (left_px, top_px), image)

        # Add inset shadow (mat edge shadow on artwork) if enabled
        if shadow_enabled and shadow_blur > 0:
            # Create an inset shadow effect
            shadow_size = int(shadow_blur * 3)

            # Create shadow overlay
            shadow_overlay = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_overlay)

            # Draw semi-transparent black rectangles for each edge shadow
            alpha = int(255 * shadow_opacity)

            # Top shadow
            if top_px > 0:
                for i in range(shadow_size):
                    fade = int(alpha * (1 - i / shadow_size))
                    shadow_draw.rectangle(
                        [left_px, top_px + i, left_px + image.width, top_px + i + 1],
                        fill=(0, 0, 0, fade)
                    )

            # Left shadow
            if left_px > 0:
                for i in range(shadow_size):
                    fade = int(alpha * (1 - i / shadow_size))
                    shadow_draw.rectangle(
                        [left_px + i, top_px, left_px + i + 1, top_px + image.height],
                        fill=(0, 0, 0, fade)
                    )

            # Right shadow
            if right_px > 0:
                for i in range(shadow_size):
                    fade = int(alpha * (1 - i / shadow_size))
                    shadow_draw.rectangle(
                        [left_px + image.width - i - 1, top_px, left_px + image.width - i, top_px + image.height],
                        fill=(0, 0, 0, fade)
                    )

            # Bottom shadow
            if bottom_px > 0:
                for i in range(shadow_size):
                    fade = int(alpha * (1 - i / shadow_size))
                    shadow_draw.rectangle(
                        [left_px, top_px + image.height - i - 1, left_px + image.width, top_px + image.height - i],
                        fill=(0, 0, 0, fade)
                    )

            # Apply blur to soften
            shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(radius=shadow_blur / 2))

            # Composite shadow onto mat
            mat_layer = Image.alpha_composite(mat_layer, shadow_overlay)

        return mat_layer

    @staticmethod
    def _add_frame(
        image: Image.Image,
        frame_width_cm: float,
        frame_color: str,
        shadow_enabled: bool,
        shadow_blur: float,
        shadow_opacity: float,
        shadow_offset_x: float,
        shadow_offset_y: float,
        scale: float
    ) -> Image.Image:
        """Add frame border around image with inner shadow"""
        # Calculate frame width in pixels
        frame_px = real_to_pixels(frame_width_cm, scale)

        # Calculate new dimensions
        new_width = image.width + (frame_px * 2)
        new_height = image.height + (frame_px * 2)

        # Create frame layer
        frame_layer = Image.new('RGBA', (new_width, new_height), FrameRenderer._hex_to_rgba(frame_color))

        # Paste image onto frame
        frame_layer.paste(image, (frame_px, frame_px), image)

        # Add inset shadow (frame edge shadow on mat/artwork) if enabled
        if shadow_enabled and shadow_blur > 0:
            shadow_size = int(shadow_blur * 3)

            # Create shadow overlay
            shadow_overlay = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_overlay)

            # Draw semi-transparent black rectangles for inset shadow
            alpha = int(255 * shadow_opacity)

            # Top shadow
            for i in range(shadow_size):
                fade = int(alpha * (1 - i / shadow_size))
                shadow_draw.rectangle(
                    [frame_px, frame_px + i, frame_px + image.width, frame_px + i + 1],
                    fill=(0, 0, 0, fade)
                )

            # Left shadow
            for i in range(shadow_size):
                fade = int(alpha * (1 - i / shadow_size))
                shadow_draw.rectangle(
                    [frame_px + i, frame_px, frame_px + i + 1, frame_px + image.height],
                    fill=(0, 0, 0, fade)
                )

            # Right shadow
            for i in range(shadow_size):
                fade = int(alpha * (1 - i / shadow_size))
                shadow_draw.rectangle(
                    [frame_px + image.width - i - 1, frame_px, frame_px + image.width - i, frame_px + image.height],
                    fill=(0, 0, 0, fade)
                )

            # Bottom shadow
            for i in range(shadow_size):
                fade = int(alpha * (1 - i / shadow_size))
                shadow_draw.rectangle(
                    [frame_px, frame_px + image.height - i - 1, frame_px + image.width, frame_px + image.height - i],
                    fill=(0, 0, 0, fade)
                )

            # Apply blur to soften
            shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(radius=shadow_blur / 2))

            # Composite shadow onto frame
            frame_layer = Image.alpha_composite(frame_layer, shadow_overlay)

        # Add drop shadow (outer shadow for entire framed piece) if enabled
        if shadow_enabled:
            # Create larger canvas for drop shadow
            shadow_canvas = Image.new('RGBA',
                                     (new_width + int(shadow_blur * 4),
                                      new_height + int(shadow_blur * 4)),
                                     (0, 0, 0, 0))

            # Create shadow
            shadow_img = Image.new('RGBA', (new_width, new_height), (0, 0, 0, int(255 * shadow_opacity * 0.6)))

            # Position shadow with offset
            shadow_x = int(shadow_blur * 2 + shadow_offset_x)
            shadow_y = int(shadow_blur * 2 + shadow_offset_y)
            shadow_canvas.paste(shadow_img, (shadow_x, shadow_y))

            # Blur shadow
            shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

            # Composite frame on top of shadow
            frame_x = int(shadow_blur * 2)
            frame_y = int(shadow_blur * 2)
            shadow_canvas.paste(frame_layer, (frame_x, frame_y), frame_layer)

            return shadow_canvas
        else:
            return frame_layer

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, alpha)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return (r, g, b, a)
        else:
            return (255, 255, 255, alpha)

    @staticmethod
    def calculate_total_dimensions(
        artwork_width_cm: float,
        artwork_height_cm: float,
        frame_config: Optional[FrameConfig]
    ) -> Tuple[float, float]:
        """
        Calculate total dimensions including frame and mat

        Args:
            artwork_width_cm: Artwork width in cm
            artwork_height_cm: Artwork height in cm
            frame_config: Frame configuration (optional)

        Returns:
            (total_width_cm, total_height_cm)
        """
        total_width = artwork_width_cm
        total_height = artwork_height_cm

        if frame_config:
            # Add mat if present
            if frame_config.mat:
                total_width += frame_config.mat.left_width_cm + frame_config.mat.right_width_cm
                total_height += frame_config.mat.top_width_cm + frame_config.mat.bottom_width_cm

            # Add frame
            total_width += frame_config.frame_width_cm * 2
            total_height += frame_config.frame_width_cm * 2

        return total_width, total_height
