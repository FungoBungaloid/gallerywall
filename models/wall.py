"""
Wall Data Model
"""
from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime
import numpy as np


@dataclass
class Wall:
    """Represents a wall surface for gallery arrangement"""
    wall_id: str
    type: str  # "photo" or "template"

    # For photo type
    original_image_path: Optional[str] = None
    corrected_image: Optional[np.ndarray] = None
    corner_points: Optional[List[Tuple[float, float]]] = None  # 4 corners for correction
    rect_bounds: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height) of wall rect in corrected image

    # For template type
    color: str = "#FFFFFF"  # Hex color

    # Common properties
    real_width_cm: float = 200.0
    real_height_cm: float = 150.0
    real_width_inches: float = 78.74
    real_height_inches: float = 59.06

    created_date: str = ""
    modified_date: str = ""

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.modified_date:
            self.modified_date = datetime.now().isoformat()

    def update_dimensions_from_cm(self, width_cm: float, height_cm: float):
        """Update dimensions given cm values, auto-convert to inches"""
        self.real_width_cm = width_cm
        self.real_height_cm = height_cm
        self.real_width_inches = width_cm / 2.54
        self.real_height_inches = height_cm / 2.54
        self.modified_date = datetime.now().isoformat()

    def update_dimensions_from_inches(self, width_inches: float, height_inches: float):
        """Update dimensions given inch values, auto-convert to cm"""
        self.real_width_inches = width_inches
        self.real_height_inches = height_inches
        self.real_width_cm = width_inches * 2.54
        self.real_height_cm = height_inches * 2.54
        self.modified_date = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'wall_id': self.wall_id,
            'type': self.type,
            'original_image_path': self.original_image_path,
            'corner_points': self.corner_points,
            'rect_bounds': self.rect_bounds,
            'color': self.color,
            'real_width_cm': self.real_width_cm,
            'real_height_cm': self.real_height_cm,
            'real_width_inches': self.real_width_inches,
            'real_height_inches': self.real_height_inches,
            'created_date': self.created_date,
            'modified_date': self.modified_date
        }

    @staticmethod
    def from_dict(data: dict) -> 'Wall':
        """Create Wall from dictionary"""
        rect_bounds = data.get('rect_bounds')
        if rect_bounds and isinstance(rect_bounds, list):
            rect_bounds = tuple(rect_bounds)

        return Wall(
            wall_id=data['wall_id'],
            type=data['type'],
            original_image_path=data.get('original_image_path'),
            corner_points=data.get('corner_points'),
            rect_bounds=rect_bounds,
            color=data.get('color', '#FFFFFF'),
            real_width_cm=data['real_width_cm'],
            real_height_cm=data['real_height_cm'],
            real_width_inches=data['real_width_inches'],
            real_height_inches=data['real_height_inches'],
            created_date=data['created_date'],
            modified_date=data['modified_date']
        )
