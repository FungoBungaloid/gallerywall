"""
High-Resolution Export Rendering
"""
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional
from models.workspace import Workspace, PlacedArtwork
from models.artwork import Artwork
from models.wall import Wall
from processors.frame_renderer import FrameRenderer
from utils.measurements import calculate_scale_factor, real_to_pixels


class ExportRenderer:
    """Handles high-resolution export of workspace arrangements"""

    @staticmethod
    def export_workspace(
        workspace: Workspace,
        wall: Wall,
        artworks: List[Artwork],
        artwork_images: dict,  # art_id -> np.ndarray
        output_width: int,
        output_height: int,
        output_path: str,
        format: str = 'PNG',
        quality: int = 95
    ) -> bool:
        """
        Export workspace to high-resolution image

        Args:
            workspace: Workspace to export
            wall: Wall model
            artworks: List of artwork models
            artwork_images: Dictionary mapping artwork IDs to images
            output_width: Output image width in pixels
            output_height: Output image height in pixels
            output_path: Path to save exported image
            format: Output format ('PNG' or 'JPEG')
            quality: JPEG quality (1-100)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate scale factor for export resolution
            scale = calculate_scale_factor(output_width, wall.real_width_cm, zoom=1.0)

            # Create canvas
            canvas = Image.new('RGBA', (output_width, output_height), (255, 255, 255, 0))

            # Render wall background
            if wall.type == "template":
                # Solid color background
                wall_bg = Image.new('RGB', (output_width, output_height), wall.color)
                canvas.paste(wall_bg, (0, 0))
            elif wall.type == "photo" and wall.corrected_image is not None:
                # Photo background - resize to fit
                from processors.image_processor import ImageProcessor
                wall_img = ImageProcessor.numpy_to_pil(wall.corrected_image)
                wall_img = wall_img.resize((output_width, output_height), Image.LANCZOS)
                canvas.paste(wall_img, (0, 0))

            # Render each placed artwork (sorted by z-index)
            placed_sorted = sorted(workspace.placed_artworks, key=lambda pa: pa.z_index)

            for placed in placed_sorted:
                artwork = next((a for a in artworks if a.art_id == placed.artwork_id), None)
                if not artwork:
                    continue

                artwork_image = artwork_images.get(placed.artwork_id)
                if artwork_image is None:
                    continue

                # Render framed artwork at export scale
                if artwork.frame_config:
                    framed = FrameRenderer.render_framed_artwork(
                        artwork_image,
                        artwork.real_width_cm,
                        artwork.real_height_cm,
                        artwork.frame_config,
                        scale
                    )
                else:
                    # No frame, just artwork
                    from processors.image_processor import ImageProcessor
                    art_pil = ImageProcessor.numpy_to_pil(artwork_image)
                    art_width_px = real_to_pixels(artwork.real_width_cm, scale)
                    art_height_px = real_to_pixels(artwork.real_height_cm, scale)
                    framed = art_pil.resize((art_width_px, art_height_px), Image.LANCZOS)
                    framed = framed.convert('RGBA')

                # Calculate position in pixels
                x_px = real_to_pixels(placed.x, scale)
                y_px = real_to_pixels(placed.y, scale)

                # Composite onto canvas
                canvas.paste(framed, (x_px, y_px), framed if framed.mode == 'RGBA' else None)

            # Convert to appropriate format and save
            if format.upper() == 'JPEG':
                # Convert RGBA to RGB for JPEG
                if canvas.mode == 'RGBA':
                    rgb_canvas = Image.new('RGB', canvas.size, (255, 255, 255))
                    rgb_canvas.paste(canvas, mask=canvas.split()[3])
                    canvas = rgb_canvas
                canvas.save(output_path, 'JPEG', quality=quality)
            else:
                canvas.save(output_path, 'PNG')

            return True

        except Exception as e:
            print(f"Error exporting workspace: {e}")
            return False

    @staticmethod
    def calculate_export_dimensions(
        wall_width_cm: float,
        wall_height_cm: float,
        target_dpi: int = 150
    ) -> Tuple[int, int]:
        """
        Calculate export dimensions based on DPI

        Args:
            wall_width_cm: Wall width in cm
            wall_height_cm: Wall height in cm
            target_dpi: Target DPI for export

        Returns:
            (width, height) in pixels
        """
        # Convert cm to inches
        width_inches = wall_width_cm / 2.54
        height_inches = wall_height_cm / 2.54

        # Calculate pixels
        width_px = int(width_inches * target_dpi)
        height_px = int(height_inches * target_dpi)

        return width_px, height_px
