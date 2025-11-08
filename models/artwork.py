"""
Artwork Data Model
"""
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from datetime import datetime
import numpy as np
from models.frame import FrameConfig


@dataclass
class Artwork:
    """Represents an individual artwork piece"""
    art_id: str
    name: str

    # Image data
    original_image_path: str
    edited_image: Optional[np.ndarray] = None  # Corrected, cropped version

    # Editing parameters (for re-editing)
    corner_points: Optional[List[Tuple[float, float]]] = None
    crop_box: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    white_balance_adjustments: Optional[Dict] = None
    rotation_angle: float = 0.0

    # Real-world measurements
    real_width_cm: float = 20.0
    real_height_cm: float = 25.0
    real_width_inches: float = 7.87
    real_height_inches: float = 9.84

    # Frame configuration
    frame_config: Optional[FrameConfig] = None

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
            'art_id': self.art_id,
            'name': self.name,
            'original_image_path': self.original_image_path,
            'corner_points': self.corner_points,
            'crop_box': self.crop_box,
            'white_balance_adjustments': self.white_balance_adjustments,
            'rotation_angle': self.rotation_angle,
            'real_width_cm': self.real_width_cm,
            'real_height_cm': self.real_height_cm,
            'real_width_inches': self.real_width_inches,
            'real_height_inches': self.real_height_inches,
            'frame_config': self.frame_config.to_dict() if self.frame_config else None,
            'created_date': self.created_date,
            'modified_date': self.modified_date
        }

    @staticmethod
    def from_dict(data: dict) -> 'Artwork':
        """Create Artwork from dictionary"""
        return Artwork(
            art_id=data['art_id'],
            name=data['name'],
            original_image_path=data['original_image_path'],
            corner_points=data.get('corner_points'),
            crop_box=tuple(data['crop_box']) if data.get('crop_box') else None,
            white_balance_adjustments=data.get('white_balance_adjustments'),
            rotation_angle=data.get('rotation_angle', 0.0),
            real_width_cm=data['real_width_cm'],
            real_height_cm=data['real_height_cm'],
            real_width_inches=data['real_width_inches'],
            real_height_inches=data['real_height_inches'],
            frame_config=FrameConfig.from_dict(data['frame_config']) if data.get('frame_config') else None,
            created_date=data['created_date'],
            modified_date=data['modified_date']
        )
