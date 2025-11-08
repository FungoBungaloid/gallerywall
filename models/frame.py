"""
Frame and Mat Configuration Data Models
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class MatConfig:
    """Configuration for artwork matting"""
    top_width_cm: float
    bottom_width_cm: float
    left_width_cm: float
    right_width_cm: float
    color: str  # Hex color

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'top_width_cm': self.top_width_cm,
            'bottom_width_cm': self.bottom_width_cm,
            'left_width_cm': self.left_width_cm,
            'right_width_cm': self.right_width_cm,
            'color': self.color
        }

    @staticmethod
    def from_dict(data: dict) -> 'MatConfig':
        """Create MatConfig from dictionary"""
        return MatConfig(
            top_width_cm=data['top_width_cm'],
            bottom_width_cm=data['bottom_width_cm'],
            left_width_cm=data['left_width_cm'],
            right_width_cm=data['right_width_cm'],
            color=data['color']
        )


@dataclass
class FrameConfig:
    """Complete frame configuration including mat and shadows"""
    # Mat configuration
    mat: Optional[MatConfig] = None

    # Frame configuration
    frame_width_cm: float = 2.0
    frame_color: str = "#000000"  # Hex color

    # Shadow settings
    frame_shadow_enabled: bool = True
    frame_shadow_blur: float = 5.0  # pixels
    frame_shadow_opacity: float = 0.3
    frame_shadow_offset_x: float = 2.0
    frame_shadow_offset_y: float = 2.0

    mat_shadow_enabled: bool = True
    mat_shadow_blur: float = 3.0
    mat_shadow_opacity: float = 0.2
    mat_shadow_offset_x: float = 1.0
    mat_shadow_offset_y: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'mat': self.mat.to_dict() if self.mat else None,
            'frame_width_cm': self.frame_width_cm,
            'frame_color': self.frame_color,
            'frame_shadow_enabled': self.frame_shadow_enabled,
            'frame_shadow_blur': self.frame_shadow_blur,
            'frame_shadow_opacity': self.frame_shadow_opacity,
            'frame_shadow_offset_x': self.frame_shadow_offset_x,
            'frame_shadow_offset_y': self.frame_shadow_offset_y,
            'mat_shadow_enabled': self.mat_shadow_enabled,
            'mat_shadow_blur': self.mat_shadow_blur,
            'mat_shadow_opacity': self.mat_shadow_opacity,
            'mat_shadow_offset_x': self.mat_shadow_offset_x,
            'mat_shadow_offset_y': self.mat_shadow_offset_y
        }

    @staticmethod
    def from_dict(data: dict) -> 'FrameConfig':
        """Create FrameConfig from dictionary"""
        return FrameConfig(
            mat=MatConfig.from_dict(data['mat']) if data.get('mat') else None,
            frame_width_cm=data.get('frame_width_cm', 2.0),
            frame_color=data.get('frame_color', '#000000'),
            frame_shadow_enabled=data.get('frame_shadow_enabled', True),
            frame_shadow_blur=data.get('frame_shadow_blur', 5.0),
            frame_shadow_opacity=data.get('frame_shadow_opacity', 0.3),
            frame_shadow_offset_x=data.get('frame_shadow_offset_x', 2.0),
            frame_shadow_offset_y=data.get('frame_shadow_offset_y', 2.0),
            mat_shadow_enabled=data.get('mat_shadow_enabled', True),
            mat_shadow_blur=data.get('mat_shadow_blur', 3.0),
            mat_shadow_opacity=data.get('mat_shadow_opacity', 0.2),
            mat_shadow_offset_x=data.get('mat_shadow_offset_x', 1.0),
            mat_shadow_offset_y=data.get('mat_shadow_offset_y', 1.0)
        )


@dataclass
class FrameTemplate:
    """Saved frame configuration template for reuse"""
    template_id: str
    name: str
    description: str
    frame_config: FrameConfig
    created_date: str
    modified_date: str

    def __post_init__(self):
        """Initialize with defaults if needed"""
        if not self.template_id:
            self.template_id = str(uuid.uuid4())
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.modified_date:
            self.modified_date = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'frame_config': self.frame_config.to_dict(),
            'created_date': self.created_date,
            'modified_date': self.modified_date
        }

    @staticmethod
    def from_dict(data: dict) -> 'FrameTemplate':
        """Create FrameTemplate from dictionary"""
        return FrameTemplate(
            template_id=data.get('template_id', str(uuid.uuid4())),
            name=data['name'],
            description=data.get('description', ''),
            frame_config=FrameConfig.from_dict(data['frame_config']),
            created_date=data.get('created_date', datetime.now().isoformat()),
            modified_date=data.get('modified_date', datetime.now().isoformat())
        )
