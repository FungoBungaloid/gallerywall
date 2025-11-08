# Gallery Wall Visualizer

A desktop application for visualizing and planning gallery wall arrangements. Users can prepare their artwork digitally, add frames and mats, then experiment with different arrangements before committing to hanging anything.

## Features

- **Wall Setup**: Create wall templates with custom dimensions and colors, OR import wall photos with 4-point perspective correction
  - Interactive corner dragging for perspective correction
  - Live preview of original and corrected photos
  - Support for JPEG, PNG, BMP wall photos
- **Art Preparation**: Import artwork images with full visual preview and set real-world dimensions
  - Thumbnail previews in sidebar
  - Large image preview when editing
  - Auto-calculated dimensions maintaining aspect ratio
  - Delete artwork functionality
- **Framing Studio**: Configure frames and mats with customizable sizes, colors, and shadows
  - Live preview updates as you adjust settings
  - Color pickers for frames and mats
  - Shadow controls for realistic depth
  - Visual indicators for framed artwork
  - **Frame templates system** - Save and reuse frame configurations
  - Bulk apply templates to all artworks
- **Arrangement Workspace**: Professional-grade interactive canvas for creating gallery wall layouts
  - **Multi-select** - Ctrl+Click to select multiple artworks, Ctrl+A to select all
  - **Undo/Redo** - Full history with Ctrl+Z and Ctrl+Y (50 action limit)
  - **Alignment tools** - Align left/center/right/top/middle/bottom across selected artworks
  - **Distribution tools** - Evenly distribute spacing horizontally or vertically
  - **Draggable guidelines** - Add horizontal/vertical guides and drag to reposition
  - **Smart snapping** - Snap to grid (10cm) and guidelines (2cm tolerance) with visual feedback
  - **Measurements mode** - Show distances from edges and between artworks
  - **Mousewheel zoom** - Zoom in/out with scroll wheel
  - **Space + drag panning** - Navigate large canvases easily
  - **Drag and drop** - Position artwork precisely
  - **Selection highlights** - Visual feedback for selected items
  - **Keyboard shortcuts** - Full keyboard control (see shortcuts section below)
  - **Grid overlay** - Optional alignment grid with configurable spacing
  - **Z-order control** - Bring to front or send to back via right-click
  - **Right-click context menu** - Quick access to all actions
  - **Multiple workspace variations** - Create, duplicate, rename, and switch between different arrangements
- **Export**: Save high-resolution images of your arrangements
  - Enhanced export dialog with format selection (PNG/JPEG)
  - DPI presets (72/150/300) or custom dimensions
  - JPEG quality control
  - Live preview of file size and resolution
- **Project Management**: Save and load your gallery wall projects with all artwork and configurations

## Requirements

- Python 3.11 or higher
- Operating System: Windows, macOS, or Linux (primary target is Windows)

## Installation

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd gallerywall
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### Workflow

1. **Start a New Project**
   - Click "New Project" on the welcome screen

2. **Set Up Your Wall**
   - Choose "Color Template" mode
   - Set wall dimensions in cm or inches (auto-converts)
   - Select a wall color
   - Click "Save & Continue"

3. **Import and Prepare Artwork**
   - Click "Import Artwork" to select your artwork images
   - For each piece, click "Edit" to:
     - Set the artwork name
     - Enter real-world dimensions (width and height in cm or inches)
   - Click "Save Changes"
   - When done, click "Continue"

4. **Configure Framing**
   - Select an artwork from the list
   - Enable mat if desired and set width
   - Choose mat and frame colors
   - Set frame width
   - Click "Apply to Artwork"
   - Repeat for all artwork pieces
   - Click "Continue"

5. **Arrange Your Gallery Wall**
   - Click the "+" button next to artwork in the library to add it to the wall
   - **Click and drag** artwork pieces to position them
   - **Ctrl+Click** to select multiple artworks, **Ctrl+A** to select all
   - Use **alignment tools** to align selected artworks (left/center/right/top/middle/bottom)
   - Use **distribution tools** to evenly space 3+ selected artworks
   - Add **guidelines** (horizontal/vertical) and drag them to reposition
   - Enable **snap to grid** or **snap to guides** for precise positioning
   - Toggle **measurements mode** to see distances and spacing
   - **Mousewheel** to zoom in/out
   - **Space + drag** to pan around the canvas
   - **Arrow keys** to nudge selected artwork by 1cm (**Shift+Arrow** for 10cm)
   - **Delete key** or right-click menu to remove selected artwork
   - **Ctrl+Z/Ctrl+Y** for undo/redo
   - Right-click for context menu with bring to front/send to back
   - Toggle **Grid** for alignment assistance
   - Click **"💾 Save"** to save your work (or press Ctrl+S)
   - Click **"📤 Export"** to create a high-resolution image

### Project Files

- Projects are saved with `.gwproj` extension
- A data folder is created next to your project file containing:
  - Original and processed artwork images
  - Wall images (if using photo mode)
  - Cached rendered frames

## Project Structure

```
gallerywall/
├── main.py                      # Application entry point
├── app.py                       # Main application class
├── config.py                    # Configuration and constants
├── models/                      # Data models
│   ├── wall.py
│   ├── artwork.py
│   ├── frame.py
│   └── workspace.py
├── ui/                          # User interface screens
│   ├── wall_setup.py
│   ├── art_editor.py
│   ├── framing_studio.py
│   └── arrangement_workspace.py
├── processors/                  # Image processing
│   ├── image_processor.py
│   ├── frame_renderer.py
│   └── export_renderer.py
├── utils/                       # Utility functions
│   ├── measurements.py
│   ├── perspective.py
│   ├── undo_manager.py
│   └── file_manager.py
└── assets/                      # Icons and templates
```

## Configuration

You can customize various settings in `config.py`:

- Canvas dimensions
- Zoom limits
- Grid settings
- Default shadow parameters
- Color presets for mats and frames
- Supported image formats

## Troubleshooting

### Application won't start
- Ensure Python 3.11+ is installed: `python --version`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for error messages in the console

### Images not loading
- Ensure image files are in supported formats (JPG, PNG, BMP, TIFF)
- Check that file paths are accessible
- Verify images aren't corrupted

### Poor performance with many artworks
- Try reducing the number of artworks in a single workspace
- Lower the zoom level
- Close and reopen the application to clear cache

### Export fails
- Ensure you have write permissions to the export location
- Check available disk space
- Try exporting at a lower resolution

## Keyboard Shortcuts

### General
- **Ctrl+S** - Save project
- **Ctrl+Z** - Undo last action
- **Ctrl+Y** - Redo last undone action

### Selection
- **Click** - Select single artwork
- **Ctrl+Click** - Add/remove artwork from selection
- **Ctrl+A** - Select all artworks

### Movement
- **Drag** - Move selected artwork(s)
- **Arrow Keys** - Nudge selected artwork by 1cm
- **Shift+Arrow Keys** - Nudge selected artwork by 10cm
- **Delete** or **Backspace** - Remove selected artwork

### Canvas Navigation
- **Space + Drag** - Pan canvas
- **Middle Mouse + Drag** - Pan canvas (alternative)
- **Mouse Wheel** - Zoom in/out

## Current Limitations

This is a professional-grade application with most core features implemented. Remaining limitations:

- **Advanced artwork editing**: White balance adjustments and perspective correction for individual artworks are not yet available
- **Artwork rotation**: Rotation of placed artwork in workspace is not yet implemented
- **Advanced export options**: Measurement overlays on exported images not yet available

## Future Enhancements

Planned features for upcoming releases:

- Advanced artwork editing (white balance sliders, contrast, saturation)
- Perspective correction for individual artwork photos
- Artwork rotation in workspace (90° and free rotation)
- Measurement overlays on exported images
- Frame cost calculator (price per linear unit)
- AR preview via phone camera
- Non-rectangular artwork support (circles, ovals)
- Lighting simulation for gallery planning
- Batch import with naming patterns
- Cloud sync or export options

## Development

### Running Tests

```bash
# Unit tests (to be implemented)
python -m pytest tests/
```

### Building for Distribution

```bash
# Using PyInstaller (Windows example)
pyinstaller --name="GalleryWallApp" \
            --windowed \
            --onedir \
            --add-data "assets;assets" \
            main.py
```

## License

See the complete technical specification in `CLAUDE.md` for detailed implementation details.

## Support

For issues, questions, or feature requests, please open an issue in the project repository.

## Credits

Built with:
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI framework
- [Pillow](https://python-pillow.org/) - Image processing
- [OpenCV](https://opencv.org/) - Advanced image operations
- [NumPy](https://numpy.org/) - Numerical operations
