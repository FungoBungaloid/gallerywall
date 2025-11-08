# Gallery Wall Visualizer - Complete Technical Specification

## Project Overview

A standalone Windows desktop application for visualizing gallery wall arrangements. Users can photograph their walls, prepare and frame their artwork digitally, then experiment with different arrangements before committing to hanging anything.

**Target User**: Personal use, individual managing their own art collection and wall arrangements.

**Primary Goal**: Provide an intuitive tool to plan gallery walls with accurate scaling and realistic framing effects.

## Technology Stack

### Core Framework
- **Python 3.11+** - Primary language
- **CustomTkinter 5.2+** - Modern, clean GUI framework built on tkinter
- **Pillow (PIL) 10.0+** - Image processing and manipulation
- **NumPy 1.24+** - Numerical operations for transforms and image processing
- **OpenCV (cv2) 4.8+** - Advanced image operations (perspective correction)

### Additional Libraries
- **tkinterdnd2** - Drag-and-drop support for file loading
- **json** - Project file persistence (built-in)
- **pathlib** - File path handling (built-in)
- **dataclasses** - Clean data structures (built-in)

### Packaging
- **PyInstaller** - Create single-folder Windows distribution
- Target: Small folder structure with executable and necessary DLLs/data

### Rationale
Python provides excellent image processing libraries and CustomTkinter gives a modern, clean interface without the bloat of Electron. The canvas-based approach in tkinter is well-suited for drag-and-drop arrangement workspaces. While the packaging creates a folder structure, it's compact and professional enough for personal use.

## Application Architecture

### Project Structure
```
gallery_wall_app/
├── main.py                      # Application entry point
├── app.py                       # Main application class
├── config.py                    # Application configuration and constants
├── models/
│   ├── __init__.py
│   ├── wall.py                  # Wall data model
│   ├── artwork.py               # Artwork data model
│   ├── frame.py                 # Frame/mat configuration model
│   └── workspace.py             # Workspace arrangement model
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Main application window
│   ├── wall_setup.py            # Wall image/template setup screen
│   ├── art_editor.py            # Art preparation screen
│   ├── framing_studio.py        # Frame and mat configuration screen
│   └── arrangement_workspace.py # Main arrangement canvas
├── processors/
│   ├── __init__.py
│   ├── image_processor.py       # Image corrections and transforms
│   ├── frame_renderer.py        # Frame and mat rendering
│   └── export_renderer.py       # High-resolution export
├── utils/
│   ├── __init__.py
│   ├── perspective.py           # 4-point perspective correction
│   ├── measurements.py          # Unit conversion and scaling
│   └── file_manager.py          # Save/load project files
└── assets/
    ├── icons/                   # UI icons
    └── templates/               # Default frame profiles
```

## Data Models

### Wall Model
```python
@dataclass
class Wall:
    wall_id: str
    type: str  # "photo" or "template"
    
    # For photo type
    original_image_path: Optional[str]
    corrected_image: Optional[np.ndarray]
    corner_points: Optional[List[Tuple[float, float]]]  # 4 corners for correction
    
    # For template type
    color: str  # Hex color
    
    # Common properties
    real_width_cm: float
    real_height_cm: float
    real_width_inches: float
    real_height_inches: float
    
    created_date: str
    modified_date: str
```

### Artwork Model
```python
@dataclass
class Artwork:
    art_id: str
    name: str
    
    # Image data
    original_image_path: str
    edited_image: Optional[np.ndarray]  # Corrected, cropped version
    
    # Editing parameters (for re-editing)
    corner_points: Optional[List[Tuple[float, float]]]
    crop_box: Optional[Tuple[int, int, int, int]]  # x1, y1, x2, y2
    white_balance_adjustments: Optional[Dict]
    rotation_angle: float = 0.0
    
    # Real-world measurements
    real_width_cm: float
    real_height_cm: float
    real_width_inches: float
    real_height_inches: float
    
    # Frame configuration
    frame_config: Optional[FrameConfig]
    
    created_date: str
    modified_date: str
```

### FrameConfig Model
```python
@dataclass
class MatConfig:
    top_width_cm: float
    bottom_width_cm: float
    left_width_cm: float
    right_width_cm: float
    color: str  # Hex color
    
@dataclass
class FrameConfig:
    # Mat configuration
    mat: Optional[MatConfig]
    
    # Frame configuration
    frame_width_cm: float
    frame_color: str  # Hex color
    
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
```

### Workspace Model
```python
@dataclass
class PlacedArtwork:
    artwork_id: str
    x: float  # Position in real-world units (cm)
    y: float
    rotation: float = 0.0  # Future enhancement
    z_index: int = 0  # Layering order

@dataclass
class Workspace:
    workspace_id: str
    name: str
    wall_id: str
    
    # Placed artwork
    placed_artworks: List[PlacedArtwork]
    
    # Grid and guides
    grid_enabled: bool = False
    grid_spacing_cm: float = 10.0
    guidelines: List[Tuple[str, float]]  # ("horizontal", y_pos) or ("vertical", x_pos)
    snap_to_grid: bool = False
    snap_to_guides: bool = True
    snap_tolerance_px: int = 10
    
    # View settings
    show_measurements: bool = False
    show_spacing_dimensions: bool = False
    zoom_level: float = 1.0
    pan_offset_x: float = 0.0
    pan_offset_y: float = 0.0
    
    created_date: str
    modified_date: str
```

## Feature Specifications

### 1. Wall Setup Module

**Screen**: Wall Setup Screen (initial or edit mode)

**Features**:
- Option to load photo or create template
- **Photo mode**:
  - File browser to select wall image
  - Display image with 4 draggable corner points
  - Real-time preview of perspective correction
  - Input fields for real-world wall dimensions (width/height in cm and inches with auto-conversion)
  - "Apply Correction" button
  - Option to adjust brightness/contrast of wall image
- **Template mode**:
  - Input fields for wall dimensions (cm and inches)
  - Color picker for wall color
  - Preview of solid color rectangle
- Save and proceed to next stage

**UI Layout**:
- Left panel: Controls (mode selection, dimension inputs, color picker, controls)
- Center: Large preview area with manipulation handles
- Bottom: Navigation buttons (Cancel, Save & Continue)

**Technical Notes**:
- Use OpenCV's `getPerspectiveTransform` and `warpPerspective` for 4-point correction
- Store both original and corrected images
- Corrected image should maintain aspect ratio based on real dimensions
- Create standard resolution (e.g., 2000px on longest side) for workspace use

### 2. Art Preparation Module

**Screen**: Art Editor Screen

**Features**:
- File browser to select folder of art images
- List view showing all imported art (thumbnails + names)
- Click art to edit in detail:
  - Main editing canvas with 4-point perspective correction
  - Crop tool with aspect ratio lock option
  - Rotation controls (90° increments + fine rotation slider)
  - Horizontal/vertical flip buttons
  - White balance adjustments:
    - Temperature slider (blue ← → yellow)
    - Tint slider (green ← → magenta)
    - Brightness slider
    - Contrast slider
    - Saturation slider
  - Reset to original button
  - Name input field
  - Real-world dimension inputs (width/height in cm and inches)
- Save individual art piece and return to list
- "Process All" view showing all prepared art

**UI Layout**:
- Left sidebar: List of artwork (scrollable)
- Center: Large editing canvas
- Right panel: Editing tools and measurements
- Bottom: Navigation (Back to List, Save, Delete)

**Technical Notes**:
- Store edited images as high-quality PNG or JPEG
- Maintain original images for re-editing
- Create both full-resolution edited version and thumbnail (e.g., 200px)
- Each artwork saved to app data directory with unique ID

### 3. Framing Studio Module

**Screen**: Framing Studio Screen

**Features**:
- List view of all prepared artwork
- Select artwork to configure framing:
  - Preview of artwork with live frame/mat rendering
  - Mat configuration:
    - Enable/disable mat
    - Width controls: 
      - "Uniform" mode: Single width input for all sides
      - "Custom" mode: Individual inputs for top, bottom, left, right
    - Color picker with common mat colors as presets (white, off-white, cream, black, grey)
  - Frame configuration:
    - Frame width input (cm)
    - Color picker with common frame colors as presets (black, white, natural wood, dark wood, gold, silver)
    - Frame style: Simple solid color for now (stretch: textures/patterns)
  - Shadow configuration:
    - Frame shadow: toggle, blur, opacity, offset X/Y
    - Mat shadow: toggle, blur, opacity, offset X/Y
    - Global "Light Direction" control (stretch goal): affects all shadow offsets
  - Preview zoom controls
- Save framing configuration
- "Copy framing to..." feature to apply same config to multiple pieces
- Template system: Save/load frame configurations as named templates

**UI Layout**:
- Left sidebar: Artwork list
- Center: Large preview with zoom controls
- Right panel: All framing controls organized in collapsible sections
- Bottom: Navigation (Back, Save, Apply to Workspace)

**Technical Notes**:
- Render frames and mats as separate layers
- Use PIL's ImageFilter for shadow blur
- Shadows should respect layer order: frame shadow on mat, mat shadow on art
- Cache rendered frames for performance (invalidate on config change)
- Calculate pixel dimensions from real-world measurements and artwork DPI

### 4. Arrangement Workspace Module

**Screen**: Workspace Canvas

**Features**:
- Canvas displaying wall with accurate scaling
- Toolbar:
  - New workspace / Open workspace / Save / Save As
  - Add artwork (multi-select from prepared art list)
  - Remove selected artwork
  - Duplicate arrangement (create variation)
  - Grid toggle, spacing control
  - Guideline tools (add horizontal/vertical guides)
  - Snap controls (grid, guides, tolerance)
  - Show measurements toggle
  - Zoom in/out, fit to window, 100%
  - Export image
- Artwork manipulation:
  - Click to select (highlight border)
  - Drag to reposition
  - Display real-time measurements when dragging
  - Snap to grid/guides with visual feedback
  - Multi-select (Ctrl+click) for grouped movement
  - Align tools: align left/center/right/top/middle/bottom
  - Distribute tools: space evenly horizontally/vertically
  - Spacing adjustment: Set specific gap between selected pieces
  - Right-click context menu: bring forward, send backward, remove
- Measurement display mode:
  - Show dimension lines between frames
  - Show distance from edges
  - Show center alignment guides
- Undo/redo system (Ctrl+Z, Ctrl+Y)

**UI Layout**:
- Top: Main toolbar with all tools
- Left sidebar: Workspace selector (list of saved workspaces), artwork library (mini)
- Center: Scrollable/pannable canvas with zoom
- Right sidebar: Properties panel showing selected artwork details, position, alignment tools
- Bottom: Status bar showing current zoom, cursor position in real-world units

**Technical Notes**:
- Canvas should be rendered at appropriate scale (real-world cm to pixels)
- Maintain aspect ratios strictly based on real measurements
- Render artwork with frames in correct scale
- Mouse wheel zoom centered on cursor position
- Pan with middle-mouse or space+drag
- Snap calculations in real-world units, converted to pixels for rendering
- Guidelines stored as real-world positions
- Double-click artwork to jump to framing editor

### 5. Export Module

**Features**:
- Export dialog with options:
  - Output resolution: preset options (1920x1080, 3840x2160, print quality) or custom
  - DPI setting for print (150, 300 dpi)
  - Format: PNG or JPEG
  - Quality slider for JPEG
  - Color space: sRGB or Adobe RGB
  - Include filename/watermark toggle (stretch)
- Preview of export dimensions
- Save location browser
- Progress bar for high-resolution renders

**Technical Notes**:
- Render at requested resolution from scratch (don't upscale canvas)
- Recalculate all frame renderings at target resolution
- Use high-quality resampling (Lanczos) for artwork images
- Render shadows at appropriate scale
- May need to render in tiles for very large exports to manage memory

## Image Processing Pipeline

### Perspective Correction (4-Point)
1. User places 4 corner points on image
2. Calculate perspective transform matrix using cv2.getPerspectiveTransform
3. Define output dimensions based on real-world measurements
4. Apply warpPerspective with high-quality interpolation
5. Store transform parameters for re-editing

### White Balance Adjustment
1. Convert image to LAB color space
2. Adjust L channel for brightness
3. Adjust A and B channels for temperature and tint
4. Convert back to RGB
5. Apply contrast using curve adjustment
6. Apply saturation in HSV space

### Frame Rendering
1. Start with artwork image at calculated pixel dimensions
2. Add mat if configured:
   - Create border with specified widths on each side
   - Fill with mat color
   - Apply inner shadow (from mat onto art):
     - Create shadow mask from art rectangle
     - Apply Gaussian blur
     - Composite with opacity
3. Add frame:
   - Create border with specified width
   - Fill with frame color
   - Apply drop shadow (from frame onto mat/art):
     - Create shadow mask from frame rectangle
     - Apply offset and Gaussian blur
     - Composite with opacity onto layer below
4. Composite all layers maintaining alpha channels

### Rendering Optimizations
- Cache rendered frames at workspace resolution
- Regenerate only when configuration changes
- Use lower-resolution previews during dragging
- Render at full resolution only for export

## Workspace Rendering Pipeline

1. Calculate pixel scale: real_world_cm → canvas_pixels based on zoom
2. Render wall background (photo or solid color) scaled to canvas
3. For each placed artwork (sorted by z-index):
   - Get cached rendered frame or generate if needed
   - Scale to current zoom level
   - Calculate position in canvas coordinates
   - Composite onto canvas
4. If show_measurements enabled:
   - Draw dimension lines and labels
   - Draw spacing measurements
5. If guidelines enabled:
   - Draw guidelines as dashed lines
6. If grid enabled:
   - Draw grid at specified spacing
7. Draw selection indicators for selected artwork

## Unit Conversion and Scaling

### Core Conversion Functions
- `cm_to_inches(cm: float) → float`: cm / 2.54
- `inches_to_cm(inches: float) → float`: inches * 2.54
- `real_to_pixels(cm: float, scale: float) → int`: Scale based on canvas zoom and display size
- `pixels_to_real(pixels: int, scale: float) → float`: Inverse of above

### Scale Calculation
- Define reference scale: e.g., 100 cm wall width = 800 canvas pixels at zoom 1.0
- scale_factor = canvas_pixels / real_world_cm * zoom_level
- All rendering uses this scale factor for positioning and sizing

### Input Validation
- Accept both metric and imperial inputs
- Auto-convert and update both fields when one changes
- Validate positive non-zero dimensions
- Validate reasonable ranges (e.g., artwork 1cm to 500cm)

## File Management and Persistence

### Project File Structure
```json
{
  "version": "1.0",
  "project_name": "Living Room Gallery",
  "app_data_dir": "/path/to/app_data/project_uuid/",
  "walls": [
    {
      "wall_id": "uuid",
      "type": "photo",
      "data": { ... }
    }
  ],
  "artworks": [
    {
      "art_id": "uuid",
      "name": "Sunset Photo",
      "image_path": "relative/path/to/edited_image.png",
      "data": { ... }
    }
  ],
  "workspaces": [
    {
      "workspace_id": "uuid",
      "name": "Option A",
      "wall_id": "uuid",
      "data": { ... }
    }
  ]
}
```

### File Locations
- **User projects**: User chooses where to save .gwproj files
- **App data directory**: %APPDATA%/GalleryWallApp/ or next to .gwproj file
  - project_uuid/
    - walls/
      - wall_uuid_original.jpg
      - wall_uuid_corrected.png
    - artworks/
      - art_uuid_original.jpg
      - art_uuid_edited.png
      - art_uuid_thumbnail.png
    - frames/
      - art_uuid_framed_cache_zoom1.0.png

### Save/Load Operations
- Auto-save workspace state every 2 minutes
- Explicit save writes full project JSON
- Load validates all referenced files exist
- Option to "pack" project: copy all image files into project folder for portability

## User Interface Design Guidelines

### Visual Style
- **Color scheme**: Light mode default with professional, minimal palette
  - Background: Light grey (#F5F5F5)
  - Panels: White (#FFFFFF)
  - Accent: Blue (#2196F3)
  - Text: Dark grey (#212121)
  - Borders: Light grey (#E0E0E0)
- **Typography**: 
  - Headers: 14pt bold
  - Body: 11pt regular
  - Labels: 10pt regular
- **Spacing**: Generous padding, 8px grid system
- **Controls**: Modern, flat design with subtle hover effects

### Interaction Patterns
- **Drag-and-drop**: Visual feedback (cursor change, highlight drop zones)
- **Keyboard shortcuts**: Standard conventions (Ctrl+S, Ctrl+Z, Delete, etc.)
- **Multi-select**: Ctrl+click for add/remove, Shift+click for range
- **Context menus**: Right-click for common operations
- **Tooltips**: Hover descriptions for all toolbar buttons
- **Modal dialogs**: For confirmations and file operations
- **Progress indicators**: For long operations (loading, exporting)

### Accessibility
- Keyboard navigation for all features
- Clear focus indicators
- Sufficient color contrast for text
- Descriptive labels and tooltips

## Testing Strategy

### Unit Testing
- Test utility functions (conversions, perspective transforms)
- Test data model validation
- Test file save/load roundtrip

### Integration Testing
- Test complete workflow: wall setup → art prep → framing → arrangement → export
- Test undo/redo system
- Test workspace save/load with missing files
- Test export at various resolutions

### Manual Testing Checklist
- Load photos of various sizes and aspect ratios
- Test with many artwork pieces (20+) for performance
- Test with extreme zoom levels
- Test guideline snapping accuracy
- Verify measurement accuracy at various scales
- Test export image quality and dimensions
- Test on different Windows versions (10, 11)

## Implementation Priorities

### Phase 1: Core Functionality (MVP)
1. Basic UI framework with navigation between screens
2. Wall template creation (solid color)
3. Art import and basic editing (perspective correction, crop)
4. Simple framing (uniform mat, basic frame, solid colors)
5. Basic workspace with drag-and-drop placement
6. Save/load project files
7. Basic export (PNG at fixed resolution)

### Phase 2: Essential Features
1. Wall photo import with perspective correction
2. Advanced art editing (white balance, rotation, flip)
3. Custom mat widths (non-uniform)
4. Frame and mat shadows
5. Workspace grid and basic guidelines
6. Snap to grid and guides
7. Show measurements mode
8. Undo/redo system
9. Export with resolution options

### Phase 3: Polish and Enhancements
1. Zoom and pan in workspace
2. Multi-select and alignment tools
3. Distribute spacing tools
4. Workspace variations (duplicate/branch)
5. Frame templates and copy framing
6. Batch operations where applicable
7. Improved export options (DPI, formats)
8. Performance optimization and caching

### Phase 4: Stretch Goals
1. Light direction for consistent shadows
2. Non-rectangular artwork support
3. Multiple artworks in one frame (multi-mat)
4. Angled wall support (perspective on final render)
5. 3D room view (very ambitious)
6. Furniture/scale reference objects
7. Batch import with naming patterns
8. Export with measurement overlays
9. Frame texture/pattern support
10. Cloud sync or export gallery plans

## Known Limitations and Constraints

### Technical Limitations
- Windows-only (no cross-platform support planned)
- Requires reasonably modern hardware (4GB+ RAM recommended)
- Large image files (>4000px) may require processing time
- Very high resolution exports (>8K) may require significant memory
- No multi-monitor optimized layout

### Feature Limitations
- Rectangular artwork only (initially)
- Planar wall surfaces only (no corners or angled walls)
- No 3D perspective or room view
- Frame styles limited to solid colors (no realistic textures)
- No collaboration or cloud features
- No print ordering integration
- No AR preview

### Workflow Limitations
- User must photograph wall front-on with good lighting
- User must measure artwork accurately
- No automatic artwork detection or measurement from photos
- No built-in image editing beyond basic corrections

## Packaging and Distribution

### Build Process
1. Create virtual environment with all dependencies
2. Generate requirements.txt
3. Use PyInstaller with custom spec file:
   ```bash
   pyinstaller --name="GalleryWallApp" \
               --windowed \
               --onedir \
               --icon=app_icon.ico \
               --add-data "assets;assets" \
               main.py
   ```
4. Test packaged application
5. Create installer (optional: use Inno Setup)

### Distribution Package Contents
```
GalleryWallApp/
├── GalleryWallApp.exe
├── _internal/           # Python runtime and dependencies
│   ├── python311.dll
│   ├── [other DLLs and dependencies]
│   └── ...
└── assets/
    ├── icons/
    └── templates/
```

### Installation
- Extract folder to Program Files or user location
- Run GalleryWallApp.exe
- First run creates %APPDATA%/GalleryWallApp/ directory
- No additional installation or configuration required

## Configuration and Settings

### Application Config (config.py)
```python
# Paths
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

# Shadow defaults
DEFAULT_FRAME_SHADOW_BLUR = 5.0
DEFAULT_FRAME_SHADOW_OPACITY = 0.3
DEFAULT_MAT_SHADOW_BLUR = 3.0
DEFAULT_MAT_SHADOW_OPACITY = 0.2

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
```

## Error Handling and Validation

### Input Validation
- Validate all dimension inputs (positive, reasonable ranges)
- Validate file paths exist and are accessible
- Validate image files are readable formats
- Validate perspective correction points form valid quadrilateral

### Error Messages
- User-friendly error dialogs with actionable messages
- Avoid technical jargon where possible
- Provide suggestions for resolution when applicable
- Log detailed errors to file for debugging

### Recovery Strategies
- Auto-save backup before destructive operations
- Graceful degradation if assets missing
- Default values if config file corrupted
- Catch exceptions at UI level to prevent crashes

## Future Enhancement Ideas

### Short-term Improvements
- Keyboard shortcuts overlay (press ? to display)
- Recent projects list on startup
- Quick frame style swapper (try different frames on same art)
- Measurement export (CSV of all frame positions and dimensions)
- Print guide generation (actual-size positioning template)

### Medium-term Additions
- Custom frame textures/patterns via image upload
- Shadow direction/intensity control per workspace
- Non-rectangular artwork support (circles, ovals, irregular shapes)
- Multi-artwork in single frame configuration
- Frame cost calculator (based on user-input price per linear cm/inch)
- Artwork collection manager (tags, categories, locations)

### Long-term Possibilities
- 3D room preview with perspective
- Corner/multi-wall support
- Mobile companion app for photographing walls and artwork
- AR preview via phone camera
- Frame vendor integration for purchasing
- Community gallery wall sharing
- AI-powered arrangement suggestions
- Export to scale for professional framers
- Lighting simulation for gallery planning

---

## Development Notes for Claude Code

### Key Implementation Points

1. **Start with data models**: Implement all dataclasses first with validation
2. **Build UI screens incrementally**: Start with basic layout, add functionality iteratively
3. **Image processing pipeline**: Test perspective correction thoroughly with various images
4. **Caching strategy**: Implement frame rendering cache early for good performance
5. **Unit conversions**: Centralize all conversion logic to avoid errors
6. **Undo/redo**: Use command pattern or state snapshots
7. **File I/O**: Robust error handling for missing files or corrupted data

### Testing Approach

- Create test images of various sizes and formats
- Test with extreme cases (very small/large artwork, unusual ratios)
- Verify measurement accuracy with known dimensions
- Test workspace save/load with complex arrangements
- Performance test with 20+ artworks in workspace

### Code Quality

- Use type hints throughout
- Document all public methods
- Keep classes focused (single responsibility)
- Separate UI logic from business logic
- Use configuration constants rather than magic numbers
- Add comments for complex algorithms (perspective transform, shadow rendering)

### User Experience Priorities

1. **Speed**: Fast loading, responsive dragging, quick preview updates
2. **Accuracy**: Precise measurements, accurate scaling, reliable exports
3. **Clarity**: Clear labels, intuitive controls, helpful tooltips
4. **Forgiveness**: Undo/redo, non-destructive editing, auto-save

---

## Summary for Quick Reference

**What it does**: Desktop app for planning gallery wall arrangements with accurate scaling and framing visualization.

**Key workflows**: 
1. Set up wall (photo or template)
2. Prepare artwork (crop, correct, measure)
3. Configure framing (mats and frames)
4. Arrange on wall with guides and snapping
5. Export high-resolution image

**Technology**: Python 3.11+, CustomTkinter, Pillow, NumPy, OpenCV, PyInstaller

**Platform**: Windows 10/11, standalone folder distribution

**Priorities**: Core workflow first, then polish, then stretch goals

**Files**: .gwproj (JSON) + image assets in app data directory

---

This specification provides everything needed to build a complete, functional gallery wall visualization application. Start with Phase 1 (MVP) to get core functionality working, then iterate through additional phases to add polish and advanced features.
