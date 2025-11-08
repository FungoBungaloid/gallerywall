"""
Frame and Mat Configuration Data Models
"""
from dataclasses import dataclass, field
from typing import Optional


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
