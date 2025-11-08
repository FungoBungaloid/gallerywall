"""
Workspace Data Model
"""
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime


@dataclass
class PlacedArtwork:
    """Represents an artwork placed in the workspace"""
    artwork_id: str
    x: float  # Position in real-world units (cm)
    y: float
    rotation: float = 0.0  # Future enhancement
    z_index: int = 0  # Layering order

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'artwork_id': self.artwork_id,
            'x': self.x,
            'y': self.y,
            'rotation': self.rotation,
            'z_index': self.z_index
        }

    @staticmethod
    def from_dict(data: dict) -> 'PlacedArtwork':
        """Create PlacedArtwork from dictionary"""
        return PlacedArtwork(
            artwork_id=data['artwork_id'],
            x=data['x'],
            y=data['y'],
            rotation=data.get('rotation', 0.0),
            z_index=data.get('z_index', 0)
        )


@dataclass
class Workspace:
    """Represents a gallery wall arrangement workspace"""
    workspace_id: str
    name: str
    wall_id: str

    # Placed artwork
    placed_artworks: List[PlacedArtwork] = field(default_factory=list)

    # Grid and guides
    grid_enabled: bool = False
    grid_spacing_cm: float = 10.0
    guidelines: List[Tuple[str, float]] = field(default_factory=list)  # ("horizontal", y_pos) or ("vertical", x_pos)
    snap_to_grid: bool = False
    snap_to_guides: bool = True
    snap_tolerance_px: int = 10

    # View settings
    show_measurements: bool = False
    show_spacing_dimensions: bool = False
    zoom_level: float = 1.0
    pan_offset_x: float = 0.0
    pan_offset_y: float = 0.0

    created_date: str = ""
    modified_date: str = ""

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.modified_date:
            self.modified_date = datetime.now().isoformat()

    def add_artwork(self, artwork_id: str, x: float, y: float) -> PlacedArtwork:
        """Add a new artwork to the workspace"""
        placed = PlacedArtwork(
            artwork_id=artwork_id,
            x=x,
            y=y,
            z_index=len(self.placed_artworks)
        )
        self.placed_artworks.append(placed)
        self.modified_date = datetime.now().isoformat()
        return placed

    def remove_artwork(self, artwork_id: str):
        """Remove an artwork from the workspace"""
        self.placed_artworks = [
            pa for pa in self.placed_artworks
            if pa.artwork_id != artwork_id
        ]
        self.modified_date = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'workspace_id': self.workspace_id,
            'name': self.name,
            'wall_id': self.wall_id,
            'placed_artworks': [pa.to_dict() for pa in self.placed_artworks],
            'grid_enabled': self.grid_enabled,
            'grid_spacing_cm': self.grid_spacing_cm,
            'guidelines': self.guidelines,
            'snap_to_grid': self.snap_to_grid,
            'snap_to_guides': self.snap_to_guides,
            'snap_tolerance_px': self.snap_tolerance_px,
            'show_measurements': self.show_measurements,
            'show_spacing_dimensions': self.show_spacing_dimensions,
            'zoom_level': self.zoom_level,
            'pan_offset_x': self.pan_offset_x,
            'pan_offset_y': self.pan_offset_y,
            'created_date': self.created_date,
            'modified_date': self.modified_date
        }

    @staticmethod
    def from_dict(data: dict) -> 'Workspace':
        """Create Workspace from dictionary"""
        return Workspace(
            workspace_id=data['workspace_id'],
            name=data['name'],
            wall_id=data['wall_id'],
            placed_artworks=[PlacedArtwork.from_dict(pa) for pa in data.get('placed_artworks', [])],
            grid_enabled=data.get('grid_enabled', False),
            grid_spacing_cm=data.get('grid_spacing_cm', 10.0),
            guidelines=data.get('guidelines', []),
            snap_to_grid=data.get('snap_to_grid', False),
            snap_to_guides=data.get('snap_to_guides', True),
            snap_tolerance_px=data.get('snap_tolerance_px', 10),
            show_measurements=data.get('show_measurements', False),
            show_spacing_dimensions=data.get('show_spacing_dimensions', False),
            zoom_level=data.get('zoom_level', 1.0),
            pan_offset_x=data.get('pan_offset_x', 0.0),
            pan_offset_y=data.get('pan_offset_y', 0.0),
            created_date=data['created_date'],
            modified_date=data['modified_date']
        )
