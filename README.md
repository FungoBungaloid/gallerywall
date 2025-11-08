# Gallery Wall Visualizer

A desktop application for visualizing and planning gallery wall arrangements. Users can prepare their artwork digitally, add frames and mats, then experiment with different arrangements before committing to hanging anything.

## Features

- **Wall Setup**: Create wall templates with custom dimensions and colors
- **Art Preparation**: Import artwork images and set real-world dimensions
- **Framing Studio**: Configure frames and mats with customizable sizes, colors, and shadows
  - Live preview updates as you adjust settings
  - Color pickers for frames and mats
  - Shadow controls for realistic depth
  - Visual indicators for framed artwork
- **Arrangement Workspace**: Interactive canvas for creating gallery wall layouts
  - **Mousewheel zoom** - Zoom in/out with scroll wheel
  - **Space + drag panning** - Navigate large canvases easily
  - **Drag and drop** - Position artwork precisely
  - **Selection highlights** - Visual feedback for selected items
  - **Keyboard shortcuts** - Ctrl+S to save, Delete to remove, arrows to nudge
  - **Grid overlay** - Optional alignment grid
  - **Right-click context menu** - Quick actions
- **Export**: Save high-resolution images of your arrangements
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
   - **Mousewheel** to zoom in/out
   - **Space + drag** to pan around the canvas
   - **Click** to select artwork (shows blue highlight)
   - **Delete key** or right-click menu to remove selected artwork
   - **Arrow keys** to nudge selected artwork by 1cm
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

- **Ctrl+S** - Save project
- **Delete** or **Backspace** - Delete selected artwork
- **Space + Drag** - Pan canvas
- **Arrow Keys** - Nudge selected artwork (1cm increments)
- **Mouse Wheel** - Zoom in/out

## Current Limitations

This is an enhanced MVP (Minimum Viable Product) version with the following limitations:

- **Photo mode**: Wall photo import with perspective correction is not yet implemented
- **Advanced editing**: White balance adjustments and perspective correction for artwork are not yet available
- **Rotation**: Artwork rotation in workspace is not yet implemented
- **Advanced features**: Alignment tools, snapping, and multi-select are planned for future releases
- **Undo/Redo**: Not yet implemented (changes are immediate)

## Future Enhancements

Planned features for upcoming releases:

- Wall photo import with 4-point perspective correction
- Advanced artwork editing (white balance, rotation, cropping)
- Workspace guidelines and snapping
- Alignment and distribution tools
- Frame templates and bulk framing
- Multiple workspace variations
- Enhanced export options (custom DPI, measurement overlays)

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
