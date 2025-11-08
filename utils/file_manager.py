"""
File Management and Project Persistence
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid


class FileManager:
    """Handles saving and loading project files"""

    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize file manager

        Args:
            project_path: Path to project file (.gwproj)
        """
        self.project_path = project_path
        self.app_data_dir = None

        if project_path:
            self._setup_app_data_dir()

    def _setup_app_data_dir(self):
        """Set up application data directory for storing images"""
        if not self.project_path:
            return

        # Create app data directory next to project file
        project_dir = os.path.dirname(self.project_path)
        project_name = Path(self.project_path).stem

        self.app_data_dir = os.path.join(project_dir, f"{project_name}_data")

        # Create directory structure
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, "walls"), exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, "artworks"), exist_ok=True)
        os.makedirs(os.path.join(self.app_data_dir, "frames"), exist_ok=True)

    def save_project(self, project_data: Dict) -> bool:
        """
        Save project to file

        Args:
            project_data: Project data dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.project_path:
            return False

        try:
            # Add metadata
            project_data['version'] = '1.0'
            project_data['app_data_dir'] = self.app_data_dir
            project_data['saved_date'] = datetime.now().isoformat()

            # Write to file
            with open(self.project_path, 'w') as f:
                json.dump(project_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    def load_project(self) -> Optional[Dict]:
        """
        Load project from file

        Returns:
            Project data dictionary or None if failed
        """
        if not self.project_path or not os.path.exists(self.project_path):
            return None

        try:
            with open(self.project_path, 'r') as f:
                project_data = json.load(f)

            # Update app data directory
            if 'app_data_dir' in project_data:
                self.app_data_dir = project_data['app_data_dir']

            return project_data
        except Exception as e:
            print(f"Error loading project: {e}")
            return None

    def get_wall_image_path(self, wall_id: str, image_type: str = "corrected") -> str:
        """
        Get path for wall image

        Args:
            wall_id: Wall ID
            image_type: Type of image ("original" or "corrected")

        Returns:
            Full path to image file
        """
        if not self.app_data_dir:
            return ""

        filename = f"{wall_id}_{image_type}.png"
        return os.path.join(self.app_data_dir, "walls", filename)

    def get_artwork_image_path(self, art_id: str, image_type: str = "edited") -> str:
        """
        Get path for artwork image

        Args:
            art_id: Artwork ID
            image_type: Type of image ("original", "edited", or "thumbnail")

        Returns:
            Full path to image file
        """
        if not self.app_data_dir:
            return ""

        filename = f"{art_id}_{image_type}.png"
        return os.path.join(self.app_data_dir, "artworks", filename)

    def get_frame_cache_path(self, art_id: str, zoom: float = 1.0) -> str:
        """
        Get path for cached framed artwork

        Args:
            art_id: Artwork ID
            zoom: Zoom level for cached image

        Returns:
            Full path to cache file
        """
        if not self.app_data_dir:
            return ""

        filename = f"{art_id}_framed_zoom{zoom:.1f}.png"
        return os.path.join(self.app_data_dir, "frames", filename)

    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID for entities"""
        return str(uuid.uuid4())

    @staticmethod
    def validate_image_file(file_path: str) -> bool:
        """
        Validate that a file is a supported image format

        Args:
            file_path: Path to image file

        Returns:
            True if valid image file, False otherwise
        """
        from config import SUPPORTED_IMAGE_FORMATS

        if not os.path.exists(file_path):
            return False

        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_IMAGE_FORMATS
