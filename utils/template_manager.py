"""
Frame Template Management
"""
import json
from pathlib import Path
from typing import List, Optional
from models.frame import FrameTemplate, FrameConfig


class TemplateManager:
    """Manages frame templates - saving, loading, and applying"""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager

        Args:
            templates_dir: Directory to store templates (defaults to ~/.gallerywall/templates)
        """
        if templates_dir is None:
            # Default to user's home directory
            home = Path.home()
            templates_dir = home / ".gallerywall" / "templates"

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.templates_dir / "frame_templates.json"

    def save_template(self, template: FrameTemplate) -> bool:
        """
        Save a frame template

        Args:
            template: Template to save

        Returns:
            True if successful, False otherwise
        """
        try:
            templates = self.load_all_templates()

            # Check if template with this ID already exists
            existing_idx = None
            for idx, t in enumerate(templates):
                if t.template_id == template.template_id:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                # Update existing template
                templates[existing_idx] = template
            else:
                # Add new template
                templates.append(template)

            # Save to file
            templates_data = [t.to_dict() for t in templates]
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving template: {e}")
            return False

    def load_all_templates(self) -> List[FrameTemplate]:
        """
        Load all saved templates

        Returns:
            List of FrameTemplate objects
        """
        if not self.templates_file.exists():
            return []

        try:
            with open(self.templates_file, 'r') as f:
                templates_data = json.load(f)

            templates = [FrameTemplate.from_dict(data) for data in templates_data]
            return templates

        except Exception as e:
            print(f"Error loading templates: {e}")
            return []

    def get_template_by_id(self, template_id: str) -> Optional[FrameTemplate]:
        """
        Get a specific template by ID

        Args:
            template_id: Template ID

        Returns:
            FrameTemplate if found, None otherwise
        """
        templates = self.load_all_templates()
        for template in templates:
            if template.template_id == template_id:
                return template
        return None

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template

        Args:
            template_id: Template ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            templates = self.load_all_templates()
            templates = [t for t in templates if t.template_id != template_id]

            # Save updated list
            templates_data = [t.to_dict() for t in templates]
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error deleting template: {e}")
            return False

    def apply_template_to_artworks(self, template_id: str, artworks: list) -> bool:
        """
        Apply a template to multiple artworks

        Args:
            template_id: Template ID to apply
            artworks: List of Artwork objects to apply template to

        Returns:
            True if successful, False otherwise
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return False

        try:
            for artwork in artworks:
                # Create a deep copy of the frame config
                artwork.frame_config = FrameConfig.from_dict(
                    template.frame_config.to_dict()
                )
            return True

        except Exception as e:
            print(f"Error applying template: {e}")
            return False
