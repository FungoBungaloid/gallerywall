"""
Arrangement Workspace Screen - Enhanced Version
"""
import customtkinter as ctk
from tkinter import Canvas, filedialog
from PIL import Image, ImageTk, ImageDraw
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
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.space_pressed = False

        self.canvas_items = {}  # placed_artwork -> (canvas_id, photo) mapping
        self.rendered_frames = {}  # cache key -> PIL Image
        self.selected_placed = None  # Currently selected PlacedArtwork

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
        self._bind_keyboard_shortcuts()

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

        # Center canvas area with scrollbars
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
        btn_save = ctk.CTkButton(parent, text="💾 Save", command=self._save_project, width=100)
        btn_save.pack(side="left", padx=5)

        # Export button
        btn_export = ctk.CTkButton(parent, text="📤 Export", command=self._export_image, width=100)
        btn_export.pack(side="left", padx=5)

        # Separator
        sep = ctk.CTkLabel(parent, text="|", width=20)
        sep.pack(side="left", padx=5)

        # Delete button
        btn_delete = ctk.CTkButton(
            parent,
            text="🗑️ Delete",
            command=self._delete_selected,
            width=100,
            fg_color="#F44336"
        )
        btn_delete.pack(side="left", padx=5)

        # Separator
        sep = ctk.CTkLabel(parent, text="|", width=20)
        sep.pack(side="left", padx=5)

        # Zoom controls
        zoom_label = ctk.CTkLabel(parent, text="Zoom:")
        zoom_label.pack(side="left", padx=(20, 5))

        btn_zoom_out = ctk.CTkButton(parent, text="-", command=self._zoom_out, width=30)
        btn_zoom_out.pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(parent, text="100%", width=50)
        self.zoom_label.pack(side="left", padx=5)

        btn_zoom_in = ctk.CTkButton(parent, text="+", command=self._zoom_in, width=30)
        btn_zoom_in.pack(side="left", padx=2)

        btn_fit = ctk.CTkButton(parent, text="Fit", command=self._zoom_fit, width=50)
        btn_fit.pack(side="left", padx=5)

        # Grid toggle
        self.grid_var = ctk.BooleanVar(value=False)
        grid_check = ctk.CTkCheckBox(
            parent,
            text="Grid",
            variable=self.grid_var,
            command=self._toggle_grid
        )
        grid_check.pack(side="left", padx=20)

        # Help text
        help_text = ctk.CTkLabel(
            parent,
            text="💡 Mouse wheel: zoom | Space+drag: pan | Del: delete | Ctrl+S: save",
            font=("Arial", 10),
            text_color="gray"
        )
        help_text.pack(side="right", padx=10)

    def _setup_sidebar(self, parent):
        """Set up sidebar with artwork library"""
        title = ctk.CTkLabel(parent, text="Artwork Library", font=("Arial", 12, "bold"))
        title.pack(pady=10)

        # Scrollable artwork list
        list_frame = ctk.CTkScrollableFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        if len(self.app.artworks) == 0:
            info = ctk.CTkLabel(list_frame, text="No artwork imported yet", text_color="gray")
            info.pack(pady=20)
        else:
            for artwork in self.app.artworks:
                item_frame = ctk.CTkFrame(list_frame)
                item_frame.pack(fill="x", pady=2, padx=2)

                name_label = ctk.CTkLabel(item_frame, text=artwork.name, anchor="w", font=("Arial", 10))
                name_label.pack(side="left", padx=5, fill="x", expand=True)

                btn_add = ctk.CTkButton(
                    item_frame,
                    text="+",
                    width=30,
                    command=lambda a=artwork: self._add_artwork_to_workspace(a),
                    fg_color="#4CAF50"
                )
                btn_add.pack(side="right", padx=2)

        # Info section
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        info_title = ctk.CTkLabel(info_frame, text="Selected:", font=("Arial", 10, "bold"))
        info_title.pack(anchor="w", pady=(5, 2))

        self.info_label = ctk.CTkLabel(
            info_frame,
            text="None",
            font=("Arial", 9),
            anchor="w",
            text_color="gray"
        )
        self.info_label.pack(anchor="w", pady=2)

        # Back button
        btn_back = ctk.CTkButton(parent, text="← Back", command=self.app.show_framing_studio_screen)
        btn_back.pack(side="bottom", pady=5, padx=10)

    def _setup_canvas(self, parent):
        """Set up main canvas"""
        # Canvas for arrangement
        self.canvas = Canvas(
            parent,
            bg="#E8E8E8",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Middle mouse button for panning
        self.canvas.bind("<Button-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)

        # Mousewheel for zoom
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows/Mac
        self.canvas.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down

        # Right-click for context menu
        self.canvas.bind("<Button-3>", self._on_right_click)

        # Focus for keyboard events
        self.canvas.focus_set()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts"""
        # Global shortcuts
        self.parent.bind_all("<Control-s>", lambda e: self._save_project())
        self.parent.bind_all("<Control-S>", lambda e: self._save_project())
        self.parent.bind_all("<Delete>", lambda e: self._delete_selected())
        self.parent.bind_all("<BackSpace>", lambda e: self._delete_selected())

        # Space for panning
        self.parent.bind_all("<KeyPress-space>", self._on_space_press)
        self.parent.bind_all("<KeyRelease-space>", self._on_space_release)

        # Arrow keys for nudging
        self.canvas.bind("<Left>", lambda e: self._nudge_selected(-1, 0))
        self.canvas.bind("<Right>", lambda e: self._nudge_selected(1, 0))
        self.canvas.bind("<Up>", lambda e: self._nudge_selected(0, -1))
        self.canvas.bind("<Down>", lambda e: self._nudge_selected(0, 1))

    def _add_artwork_to_workspace(self, artwork):
        """Add artwork to workspace at center"""
        if not self.app.current_workspace:
            return

        # Calculate total dimensions including frame
        total_width_cm = artwork.real_width_cm
        total_height_cm = artwork.real_height_cm

        if artwork.frame_config:
            from processors.frame_renderer import FrameRenderer
            total_width_cm, total_height_cm = FrameRenderer.calculate_total_dimensions(
                artwork.real_width_cm,
                artwork.real_height_cm,
                artwork.frame_config
            )

        # Place at center of wall
        x = self.app.current_wall.real_width_cm / 2 - total_width_cm / 2
        y = self.app.current_wall.real_height_cm / 2 - total_height_cm / 2

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

        # Calculate canvas size
        wall_width_px = real_to_pixels(self.app.current_wall.real_width_cm, self.scale)
        wall_height_px = real_to_pixels(self.app.current_wall.real_height_cm, self.scale)

        # Apply panning offset
        offset_x = self.pan_offset_x
        offset_y = self.pan_offset_y

        # Render wall background
        self.canvas.create_rectangle(
            offset_x, offset_y,
            offset_x + wall_width_px, offset_y + wall_height_px,
            fill=self.app.current_wall.color,
            outline="#AAAAAA",
            width=2,
            tags="wall"
        )

        # Render grid if enabled
        if self.grid_var.get():
            self._render_grid(offset_x, offset_y, wall_width_px, wall_height_px)

        # Render placed artwork
        for placed in self.app.current_workspace.placed_artworks:
            self._render_placed_artwork(placed, offset_x, offset_y)

    def _render_grid(self, offset_x, offset_y, wall_width_px, wall_height_px):
        """Render grid lines"""
        if not self.app.current_wall:
            return

        grid_spacing_px = real_to_pixels(config.DEFAULT_GRID_SPACING_CM, self.scale)

        # Vertical lines
        x = grid_spacing_px
        while x < wall_width_px:
            self.canvas.create_line(
                offset_x + x, offset_y,
                offset_x + x, offset_y + wall_height_px,
                fill=config.GRID_LINE_COLOR,
                width=config.GRID_LINE_WIDTH,
                tags="grid"
            )
            x += grid_spacing_px

        # Horizontal lines
        y = grid_spacing_px
        while y < wall_height_px:
            self.canvas.create_line(
                offset_x, offset_y + y,
                offset_x + wall_width_px, offset_y + y,
                fill=config.GRID_LINE_COLOR,
                width=config.GRID_LINE_WIDTH,
                tags="grid"
            )
            y += grid_spacing_px

    def _render_placed_artwork(self, placed: PlacedArtwork, offset_x: int, offset_y: int):
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

        # Add selection highlight if selected
        if placed == self.selected_placed:
            # Create a copy with selection border
            highlighted = framed_img.copy()
            draw = ImageDraw.Draw(highlighted)
            w, h = highlighted.size
            # Draw thick selection border
            for i in range(4):
                draw.rectangle([i, i, w-1-i, h-1-i], outline="#2196F3", width=1)
            framed_img = highlighted

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(framed_img)

        # Calculate position
        x_px = offset_x + real_to_pixels(placed.x, self.scale)
        y_px = offset_y + real_to_pixels(placed.y, self.scale)

        # Create canvas item
        item_id = self.canvas.create_image(
            x_px, y_px,
            image=photo,
            anchor="nw",
            tags=("artwork", f"placed_{id(placed)}")
        )

        # Store reference to prevent garbage collection
        self.canvas_items[placed] = (item_id, photo)

    def _on_canvas_click(self, event):
        """Handle canvas click"""
        if self.space_pressed:
            # Start panning
            self._on_pan_start(event)
            return

        # Find clicked item
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)

        # Find artwork items (exclude wall and grid)
        artwork_items = [i for i in items if "artwork" in self.canvas.gettags(i)]

        if artwork_items:
            # Get the topmost artwork item
            item = artwork_items[-1]

            # Find which placed artwork this is
            for placed, (canvas_id, _) in self.canvas_items.items():
                if canvas_id == item:
                    self.selected_placed = placed
                    self.dragging_item = placed
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    self._update_selection_info()
                    self._render_workspace()  # Re-render to show selection
                    return

        # Clicked on empty space - deselect
        self.selected_placed = None
        self._update_selection_info()
        self._render_workspace()

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.panning:
            self._on_pan_drag(event)
            return

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

            # Clamp to wall bounds
            self._clamp_to_wall(self.dragging_item)

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            # Re-render
            self._render_workspace()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        if self.panning:
            self._on_pan_end(event)
        self.dragging_item = None

    def _clamp_to_wall(self, placed: PlacedArtwork):
        """Clamp artwork position to wall bounds"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return

        # Calculate artwork total size
        total_width = artwork.real_width_cm
        total_height = artwork.real_height_cm

        if artwork.frame_config:
            from processors.frame_renderer import FrameRenderer
            total_width, total_height = FrameRenderer.calculate_total_dimensions(
                artwork.real_width_cm,
                artwork.real_height_cm,
                artwork.frame_config
            )

        # Clamp
        placed.x = max(0, min(placed.x, self.app.current_wall.real_width_cm - total_width))
        placed.y = max(0, min(placed.y, self.app.current_wall.real_height_cm - total_height))

    def _on_pan_start(self, event):
        """Start panning"""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.configure(cursor="fleur")

    def _on_pan_drag(self, event):
        """Handle panning drag"""
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y

            self.pan_offset_x += dx
            self.pan_offset_y += dy

            self.pan_start_x = event.x
            self.pan_start_y = event.y

            self._render_workspace()

    def _on_pan_end(self, event):
        """End panning"""
        self.panning = False
        self.canvas.configure(cursor="")

    def _on_space_press(self, event):
        """Handle space key press"""
        self.space_pressed = True
        self.canvas.configure(cursor="hand1")

    def _on_space_release(self, event):
        """Handle space key release"""
        self.space_pressed = False
        if not self.panning:
            self.canvas.configure(cursor="")

    def _on_mousewheel(self, event):
        """Handle mousewheel for zooming"""
        # Determine scroll direction
        if event.num == 4 or event.delta > 0:
            # Scroll up - zoom in
            self._zoom_in()
        elif event.num == 5 or event.delta < 0:
            # Scroll down - zoom out
            self._zoom_out()

    def _on_right_click(self, event):
        """Handle right-click context menu"""
        # Find clicked item
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        artwork_items = [i for i in items if "artwork" in self.canvas.gettags(i)]

        if artwork_items:
            # Find which placed artwork this is
            for placed, (canvas_id, _) in self.canvas_items.items():
                if canvas_id == artwork_items[-1]:
                    self.selected_placed = placed
                    self._update_selection_info()
                    self._render_workspace()

                    # Show context menu
                    import tkinter as tk
                    menu = tk.Menu(self.canvas, tearoff=0)
                    menu.add_command(label="Delete", command=self._delete_selected)
                    menu.post(event.x_root, event.y_root)
                    break

    def _delete_selected(self):
        """Delete selected artwork from workspace"""
        if self.selected_placed:
            self.app.current_workspace.remove_artwork(self.selected_placed.artwork_id)
            self.selected_placed = None
            self._update_selection_info()
            self._render_workspace()

    def _nudge_selected(self, dx, dy):
        """Nudge selected artwork by arrow keys"""
        if self.selected_placed:
            # Nudge by 1cm
            self.selected_placed.x += dx
            self.selected_placed.y += dy
            self._clamp_to_wall(self.selected_placed)
            self._render_workspace()

    def _update_selection_info(self):
        """Update selection info in sidebar"""
        if self.selected_placed:
            artwork = next((a for a in self.app.artworks if a.art_id == self.selected_placed.artwork_id), None)
            if artwork:
                info_text = f"{artwork.name}\nPosition: ({self.selected_placed.x:.1f}, {self.selected_placed.y:.1f}) cm"
                self.info_label.configure(text=info_text, text_color="white")
            else:
                self.info_label.configure(text="None", text_color="gray")
        else:
            self.info_label.configure(text="None", text_color="gray")

    def _toggle_grid(self):
        """Toggle grid display"""
        self._render_workspace()

    def _zoom_in(self):
        """Zoom in"""
        old_zoom = self.zoom
        self.zoom = min(self.zoom + config.ZOOM_STEP, config.MAX_ZOOM)

        if old_zoom != self.zoom:
            self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
            self.rendered_frames.clear()  # Clear cache
            self._render_workspace()

    def _zoom_out(self):
        """Zoom out"""
        old_zoom = self.zoom
        self.zoom = max(self.zoom - config.ZOOM_STEP, config.MIN_ZOOM)

        if old_zoom != self.zoom:
            self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
            self.rendered_frames.clear()  # Clear cache
            self._render_workspace()

    def _zoom_fit(self):
        """Fit wall to canvas"""
        self.zoom = 1.0
        self.pan_offset_x = 20
        self.pan_offset_y = 20
        self.zoom_label.configure(text="100%")
        self.rendered_frames.clear()
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
            self.app._show_info(f"Image exported successfully!")
        else:
            self.app._show_error("Failed to export image")
