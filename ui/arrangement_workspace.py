"""
Arrangement Workspace Screen
"""
import customtkinter as ctk
from tkinter import Canvas, filedialog
from PIL import Image, ImageTk
import numpy as np
from models.workspace import Workspace, PlacedArtwork
from processors.frame_renderer import FrameRenderer
from processors.export_renderer import ExportRenderer
from utils.measurements import calculate_scale_factor, real_to_pixels, pixels_to_real
from utils.file_manager import FileManager
import config


class ArrangementWorkspaceScreen:
    """Screen for arranging artwork on the wall"""

    def __init__(self, app, parent):
        """
        Initialize arrangement workspace screen

        Args:
            app: Main application instance
            parent: Parent widget
        """
        self.app = app
        self.parent = parent

        # State
        self.scale = 1.0
        self.zoom = 1.0
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.canvas_items = {}  # placed_artwork -> canvas_id mapping
        self.rendered_frames = {}  # art_id -> PIL Image cache

        # Initialize workspace if needed
        if not self.app.current_workspace and self.app.current_wall:
            workspace_id = FileManager.generate_id()
            self.app.current_workspace = Workspace(
                workspace_id=workspace_id,
                name="Main Arrangement",
                wall_id=self.app.current_wall.wall_id
            )
            self.app.workspaces.append(self.app.current_workspace)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI"""
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Top toolbar
        toolbar = ctk.CTkFrame(main_frame, height=50)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)
        toolbar.pack_propagate(False)

        # Left sidebar
        left_panel = ctk.CTkFrame(main_frame, width=200)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Center canvas area
        canvas_frame = ctk.CTkFrame(main_frame)
        canvas_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self._setup_toolbar(toolbar)
        self._setup_sidebar(left_panel)
        self._setup_canvas(canvas_frame)

        # Initial render
        self._render_workspace()

    def _setup_toolbar(self, parent):
        """Set up toolbar"""
        # Save button
        btn_save = ctk.CTkButton(parent, text="Save Project", command=self._save_project, width=100)
        btn_save.pack(side="left", padx=5)

        # Export button
        btn_export = ctk.CTkButton(parent, text="Export Image", command=self._export_image, width=100)
        btn_export.pack(side="left", padx=5)

        # Zoom controls
        zoom_label = ctk.CTkLabel(parent, text="Zoom:")
        zoom_label.pack(side="left", padx=(20, 5))

        btn_zoom_out = ctk.CTkButton(parent, text="-", command=self._zoom_out, width=30)
        btn_zoom_out.pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(parent, text="100%", width=50)
        self.zoom_label.pack(side="left", padx=5)

        btn_zoom_in = ctk.CTkButton(parent, text="+", command=self._zoom_in, width=30)
        btn_zoom_in.pack(side="left", padx=2)

        # Grid toggle
        self.grid_var = ctk.BooleanVar(value=False)
        grid_check = ctk.CTkCheckBox(
            parent,
            text="Grid",
            variable=self.grid_var,
            command=self._toggle_grid
        )
        grid_check.pack(side="left", padx=20)

    def _setup_sidebar(self, parent):
        """Set up sidebar with artwork library"""
        title = ctk.CTkLabel(parent, text="Artwork Library", font=("Arial", 12, "bold"))
        title.pack(pady=10)

        # Scrollable artwork list
        list_frame = ctk.CTkScrollableFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        for artwork in self.app.artworks:
            item_frame = ctk.CTkFrame(list_frame)
            item_frame.pack(fill="x", pady=2, padx=2)

            name_label = ctk.CTkLabel(item_frame, text=artwork.name, anchor="w")
            name_label.pack(side="left", padx=5, fill="x", expand=True)

            btn_add = ctk.CTkButton(
                item_frame,
                text="+",
                width=30,
                command=lambda a=artwork: self._add_artwork_to_workspace(a)
            )
            btn_add.pack(side="right", padx=2)

        # Back button
        btn_back = ctk.CTkButton(parent, text="Back to Framing", command=self.app.show_framing_studio_screen)
        btn_back.pack(side="bottom", pady=10, padx=10)

    def _setup_canvas(self, parent):
        """Set up main canvas"""
        # Canvas for arrangement
        self.canvas = Canvas(
            parent,
            bg="#F0F0F0",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _add_artwork_to_workspace(self, artwork):
        """Add artwork to workspace at center"""
        if not self.app.current_workspace:
            return

        # Place at center of wall
        x = self.app.current_wall.real_width_cm / 2 - artwork.real_width_cm / 2
        y = self.app.current_wall.real_height_cm / 2 - artwork.real_height_cm / 2

        self.app.current_workspace.add_artwork(artwork.art_id, x, y)
        self._render_workspace()

    def _calculate_scale(self):
        """Calculate scale factor for current canvas size"""
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = config.DEFAULT_CANVAS_WIDTH

        self.scale = calculate_scale_factor(
            canvas_width,
            self.app.current_wall.real_width_cm,
            self.zoom
        )

    def _render_workspace(self):
        """Render the workspace"""
        if not self.app.current_workspace or not self.app.current_wall:
            return

        # Clear canvas
        self.canvas.delete("all")
        self.canvas_items.clear()

        # Calculate scale
        self._calculate_scale()

        # Render wall background
        wall_width_px = real_to_pixels(self.app.current_wall.real_width_cm, self.scale)
        wall_height_px = real_to_pixels(self.app.current_wall.real_height_cm, self.scale)

        self.canvas.config(width=wall_width_px, height=wall_height_px)
        self.canvas.create_rectangle(
            0, 0, wall_width_px, wall_height_px,
            fill=self.app.current_wall.color,
            outline=""
        )

        # Render grid if enabled
        if self.grid_var.get():
            self._render_grid()

        # Render placed artwork
        for placed in self.app.current_workspace.placed_artworks:
            self._render_placed_artwork(placed)

    def _render_grid(self):
        """Render grid lines"""
        if not self.app.current_wall:
            return

        wall_width_px = real_to_pixels(self.app.current_wall.real_width_cm, self.scale)
        wall_height_px = real_to_pixels(self.app.current_wall.real_height_cm, self.scale)
        grid_spacing_px = real_to_pixels(config.DEFAULT_GRID_SPACING_CM, self.scale)

        # Vertical lines
        x = grid_spacing_px
        while x < wall_width_px:
            self.canvas.create_line(
                x, 0, x, wall_height_px,
                fill=config.GRID_LINE_COLOR,
                width=config.GRID_LINE_WIDTH
            )
            x += grid_spacing_px

        # Horizontal lines
        y = grid_spacing_px
        while y < wall_height_px:
            self.canvas.create_line(
                0, y, wall_width_px, y,
                fill=config.GRID_LINE_COLOR,
                width=config.GRID_LINE_WIDTH
            )
            y += grid_spacing_px

    def _render_placed_artwork(self, placed: PlacedArtwork):
        """Render a placed artwork on canvas"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return

        artwork_image = self.app.artwork_images.get(placed.artwork_id)
        if artwork_image is None:
            return

        # Render framed artwork if not cached
        cache_key = f"{placed.artwork_id}_{self.zoom:.2f}"
        if cache_key not in self.rendered_frames:
            if artwork.frame_config:
                framed = FrameRenderer.render_framed_artwork(
                    artwork_image,
                    artwork.real_width_cm,
                    artwork.real_height_cm,
                    artwork.frame_config,
                    self.scale
                )
            else:
                # No frame, just artwork
                from processors.image_processor import ImageProcessor
                art_pil = ImageProcessor.numpy_to_pil(artwork_image)
                art_width_px = real_to_pixels(artwork.real_width_cm, self.scale)
                art_height_px = real_to_pixels(artwork.real_height_cm, self.scale)
                framed = art_pil.resize((art_width_px, art_height_px), Image.LANCZOS)

            self.rendered_frames[cache_key] = framed

        framed_img = self.rendered_frames[cache_key]

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(framed_img)

        # Calculate position
        x_px = real_to_pixels(placed.x, self.scale)
        y_px = real_to_pixels(placed.y, self.scale)

        # Create canvas item
        item_id = self.canvas.create_image(
            x_px, y_px,
            image=photo,
            anchor="nw",
            tags="artwork"
        )

        # Store reference to prevent garbage collection
        self.canvas_items[placed] = (item_id, photo)

    def _on_canvas_click(self, event):
        """Handle canvas click"""
        # Find clicked item
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        for item in reversed(items):
            # Find which placed artwork this is
            for placed, (canvas_id, _) in self.canvas_items.items():
                if canvas_id == item:
                    self.dragging_item = placed
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    return

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.dragging_item:
            # Calculate delta
            dx_px = event.x - self.drag_start_x
            dy_px = event.y - self.drag_start_y

            # Convert to real-world units
            dx_cm = pixels_to_real(dx_px, self.scale)
            dy_cm = pixels_to_real(dy_px, self.scale)

            # Update position
            self.dragging_item.x += dx_cm
            self.dragging_item.y += dy_cm

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            # Re-render
            self._render_workspace()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        self.dragging_item = None

    def _toggle_grid(self):
        """Toggle grid display"""
        self._render_workspace()

    def _zoom_in(self):
        """Zoom in"""
        self.zoom = min(self.zoom + config.ZOOM_STEP, config.MAX_ZOOM)
        self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
        self.rendered_frames.clear()  # Clear cache
        self._render_workspace()

    def _zoom_out(self):
        """Zoom out"""
        self.zoom = max(self.zoom - config.ZOOM_STEP, config.MIN_ZOOM)
        self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
        self.rendered_frames.clear()  # Clear cache
        self._render_workspace()

    def _save_project(self):
        """Save project"""
        self.app.save_project()

    def _export_image(self):
        """Export workspace to image"""
        if not self.app.current_workspace:
            return

        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")]
        )

        if not file_path:
            return

        # Determine format
        format = "PNG" if file_path.lower().endswith('.png') else "JPEG"

        # Export at high resolution (1920x1440 or based on wall aspect ratio)
        output_width = 1920
        aspect_ratio = self.app.current_wall.real_height_cm / self.app.current_wall.real_width_cm
        output_height = int(output_width * aspect_ratio)

        success = ExportRenderer.export_workspace(
            self.app.current_workspace,
            self.app.current_wall,
            self.app.artworks,
            self.app.artwork_images,
            output_width,
            output_height,
            file_path,
            format=format
        )

        if success:
            self.app._show_info(f"Image exported successfully to {file_path}")
        else:
            self.app._show_error("Failed to export image")
