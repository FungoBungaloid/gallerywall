"""
Gallery Wall Visualizer - Configuration and Constants
"""

# Application Info
APP_NAME = "Gallery Wall Visualizer"
APP_VERSION = "1.0.0"
DEFAULT_PROJECT_NAME = "Untitled Gallery"

# Canvas settings
DEFAULT_CANVAS_WIDTH = 1200
DEFAULT_CANVAS_HEIGHT = 800
MIN_ZOOM = 0.1
MAX_ZOOM = 5.0
ZOOM_STEP = 0.1

# Grid settings
DEFAULT_GRID_SPACING_CM = 10.0
GRID_LINE_COLOR = "#CCCCCC"
GRID_LINE_WIDTH = 1

# Guideline settings
GUIDE_LINE_COLOR = "#FF5722"
GUIDE_LINE_WIDTH = 2
GUIDE_DASH_PATTERN = (10, 5)

# Snap settings
DEFAULT_SNAP_TOLERANCE_PX = 10

# Rendering settings
THUMBNAIL_SIZE = 200
WORKSPACE_PREVIEW_QUALITY = "MEDIUM"  # DRAFT, MEDIUM, HIGH
EXPORT_QUALITY = "HIGH"
CACHE_ENABLED = True

# Shadow defaults (increased for better visibility)
DEFAULT_FRAME_SHADOW_BLUR = 8.0
DEFAULT_FRAME_SHADOW_OPACITY = 0.5
DEFAULT_MAT_SHADOW_BLUR = 5.0
DEFAULT_MAT_SHADOW_OPACITY = 0.4

# Color presets
MAT_COLOR_PRESETS = [
    ("White", "#FFFFFF"),
    ("Off-White", "#F8F8F0"),
    ("Cream", "#FFFDD0"),
    ("Light Grey", "#D3D3D3"),
    ("Black", "#000000"),
]

FRAME_COLOR_PRESETS = [
    ("Black", "#000000"),
    ("White", "#FFFFFF"),
    ("Natural Wood", "#D2B48C"),
    ("Dark Wood", "#654321"),
    ("Gold", "#FFD700"),
    ("Silver", "#C0C0C0"),
]

# File settings
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
PROJECT_FILE_EXTENSION = ".gwproj"
AUTO_SAVE_INTERVAL_SECONDS = 120

# UI settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
PANEL_WIDTH = 300

# UI Color scheme
BG_COLOR = "#F5F5F5"
PANEL_COLOR = "#FFFFFF"
ACCENT_COLOR = "#2196F3"
TEXT_COLOR = "#212121"
BORDER_COLOR = "#E0E0E0"
