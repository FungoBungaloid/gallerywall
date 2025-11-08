"""
Arrangement Workspace Screen - Full Featured Version
"""
import customtkinter as ctk
from tkinter import Canvas, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
from models.workspace import Workspace, PlacedArtwork
from processors.frame_renderer import FrameRenderer
from processors.export_renderer import ExportRenderer
from utils.measurements import calculate_scale_factor, real_to_pixels, pixels_to_real
from utils.file_manager import FileManager
from utils.undo_manager import UndoManager, Command
import config
import copy


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
        self.pan_offset_x = 20
        self.pan_offset_y = 20
        self.space_pressed = False

        self.canvas_items = {}  # placed_artwork -> (canvas_id, photo) mapping
        self.rendered_frames = {}  # cache key -> PIL Image
        self.selected_placed = []  # List of selected PlacedArtwork (for multi-select)

        # Guidelines
        self.guidelines = []  # List of (orientation, position) tuples
        self.dragging_guideline = None

        # Settings
        self.show_measurements = False
        self.snap_to_grid = False
        self.snap_to_guides = True
        self.snap_tolerance_cm = 2.0

        # Undo/Redo
        self.undo_manager = UndoManager(max_history=50)

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

        # Second toolbar for alignment tools
        toolbar2 = ctk.CTkFrame(main_frame, height=45)
        toolbar2.pack(side="top", fill="x", padx=5, pady=(0, 5))
        toolbar2.pack_propagate(False)

        # Left sidebar
        left_panel = ctk.CTkFrame(main_frame, width=200)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Center canvas area
        canvas_frame = ctk.CTkFrame(main_frame)
        canvas_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self._setup_toolbar(toolbar)
        self._setup_alignment_toolbar(toolbar2)
        self._setup_sidebar(left_panel)
        self._setup_canvas(canvas_frame)

        # Initial render
        self._render_workspace()

    def _setup_toolbar(self, parent):
        """Set up main toolbar"""
        # Save/Undo/Redo group
        btn_save = ctk.CTkButton(parent, text="💾 Save", command=self._save_project, width=80)
        btn_save.pack(side="left", padx=2)

        self.btn_undo = ctk.CTkButton(parent, text="↶ Undo", command=self._undo, width=80)
        self.btn_undo.pack(side="left", padx=2)

        self.btn_redo = ctk.CTkButton(parent, text="↷ Redo", command=self._redo, width=80)
        self.btn_redo.pack(side="left", padx=2)

        # Separator
        ctk.CTkLabel(parent, text="|", width=10).pack(side="left", padx=5)

        # Export button
        btn_export = ctk.CTkButton(parent, text="📤 Export", command=self._export_image, width=80)
        btn_export.pack(side="left", padx=2)

        # Delete button
        btn_delete = ctk.CTkButton(
            parent,
            text="🗑️ Delete",
            command=self._delete_selected,
            width=80,
            fg_color="#F44336"
        )
        btn_delete.pack(side="left", padx=2)

        # Separator
        ctk.CTkLabel(parent, text="|", width=10).pack(side="left", padx=5)

        # Zoom controls
        ctk.CTkLabel(parent, text="Zoom:", font=("Arial", 10)).pack(side="left", padx=(5, 2))

        ctk.CTkButton(parent, text="-", command=self._zoom_out, width=25).pack(side="left", padx=1)

        self.zoom_label = ctk.CTkLabel(parent, text="100%", width=45, font=("Arial", 10))
        self.zoom_label.pack(side="left", padx=2)

        ctk.CTkButton(parent, text="+", command=self._zoom_in, width=25).pack(side="left", padx=1)

        ctk.CTkButton(parent, text="Fit", command=self._zoom_fit, width=40).pack(side="left", padx=2)

        # Separator
        ctk.CTkLabel(parent, text="|", width=10).pack(side="left", padx=5)

        # View options
        self.grid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            parent,
            text="Grid",
            variable=self.grid_var,
            command=self._toggle_grid,
            width=60
        ).pack(side="left", padx=2)

        self.measurements_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            parent,
            text="Measure",
            variable=self.measurements_var,
            command=self._toggle_measurements,
            width=80
        ).pack(side="left", padx=2)

    def _setup_alignment_toolbar(self, parent):
        """Set up alignment and distribution toolbar"""
        ctk.CTkLabel(parent, text="Align:", font=("Arial", 10, "bold")).pack(side="left", padx=(5, 2))

        # Alignment buttons
        btn_align_left = ctk.CTkButton(parent, text="⫤ Left", command=lambda: self._align("left"), width=60)
        btn_align_left.pack(side="left", padx=1)

        btn_align_center = ctk.CTkButton(parent, text="⫿ Center", command=lambda: self._align("center_h"), width=70)
        btn_align_center.pack(side="left", padx=1)

        btn_align_right = ctk.CTkButton(parent, text="⫣ Right", command=lambda: self._align("right"), width=60)
        btn_align_right.pack(side="left", padx=1)

        btn_align_top = ctk.CTkButton(parent, text="⫦ Top", command=lambda: self._align("top"), width=60)
        btn_align_top.pack(side="left", padx=1)

        btn_align_middle = ctk.CTkButton(parent, text="⬌ Middle", command=lambda: self._align("center_v"), width=70)
        btn_align_middle.pack(side="left", padx=1)

        btn_align_bottom = ctk.CTkButton(parent, text="⫧ Bottom", command=lambda: self._align("bottom"), width=70)
        btn_align_bottom.pack(side="left", padx=1)

        # Separator
        ctk.CTkLabel(parent, text="|", width=10).pack(side="left", padx=5)

        # Distribution buttons
        ctk.CTkLabel(parent, text="Distribute:", font=("Arial", 10, "bold")).pack(side="left", padx=(5, 2))

        btn_dist_h = ctk.CTkButton(parent, text="⟷ Horizontal", command=lambda: self._distribute("horizontal"), width=90)
        btn_dist_h.pack(side="left", padx=1)

        btn_dist_v = ctk.CTkButton(parent, text="⟷ Vertical", command=lambda: self._distribute("vertical"), width=80)
        btn_dist_v.pack(side="left", padx=1)

        # Separator
        ctk.CTkLabel(parent, text="|", width=10).pack(side="left", padx=5)

        # Snapping options
        self.snap_grid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            parent,
            text="Snap Grid",
            variable=self.snap_grid_var,
            command=self._toggle_snap_grid,
            width=80
        ).pack(side="left", padx=2)

        self.snap_guides_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            parent,
            text="Snap Guides",
            variable=self.snap_guides_var,
            command=self._toggle_snap_guides,
            width=90
        ).pack(side="left", padx=2)

    def _setup_sidebar(self, parent):
        """Set up sidebar with artwork library"""
        # Workspace management section
        workspace_frame = ctk.CTkFrame(parent)
        workspace_frame.pack(fill="x", padx=5, pady=(5, 10))

        ctk.CTkLabel(workspace_frame, text="Workspace:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=(5, 2))

        # Workspace selector
        workspace_names = [w.name for w in self.app.workspaces] if self.app.workspaces else ["No workspaces"]
        current_name = self.app.current_workspace.name if self.app.current_workspace else ""

        self.workspace_var = ctk.StringVar(value=current_name if current_name else "")
        self.workspace_dropdown = ctk.CTkOptionMenu(
            workspace_frame,
            variable=self.workspace_var,
            values=workspace_names,
            command=self._on_workspace_changed,
            width=170
        )
        self.workspace_dropdown.pack(fill="x", padx=5, pady=2)

        # Workspace action buttons
        workspace_btn_frame = ctk.CTkFrame(workspace_frame)
        workspace_btn_frame.pack(fill="x", padx=5, pady=5)

        btn_new_workspace = ctk.CTkButton(
            workspace_btn_frame,
            text="➕",
            width=30,
            command=self._new_workspace,
            fg_color="#4CAF50"
        )
        btn_new_workspace.pack(side="left", padx=1)

        btn_duplicate_workspace = ctk.CTkButton(
            workspace_btn_frame,
            text="📋",
            width=30,
            command=self._duplicate_workspace
        )
        btn_duplicate_workspace.pack(side="left", padx=1)

        btn_rename_workspace = ctk.CTkButton(
            workspace_btn_frame,
            text="✏️",
            width=30,
            command=self._rename_workspace
        )
        btn_rename_workspace.pack(side="left", padx=1)

        btn_delete_workspace = ctk.CTkButton(
            workspace_btn_frame,
            text="🗑️",
            width=30,
            command=self._delete_workspace,
            fg_color="#F44336"
        )
        btn_delete_workspace.pack(side="left", padx=1)

        # Separator
        ctk.CTkFrame(parent, height=2, fg_color="gray").pack(fill="x", padx=10, pady=5)

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

                name_label = ctk.CTkLabel(item_frame, text=artwork.name, anchor="w", font=("Arial", 9))
                name_label.pack(side="left", padx=5, fill="x", expand=True)

                btn_add = ctk.CTkButton(
                    item_frame,
                    text="+",
                    width=30,
                    command=lambda a=artwork: self._add_artwork_to_workspace(a),
                    fg_color="#4CAF50"
                )
                btn_add.pack(side="right", padx=2)

        # Guidelines section
        guidelines_frame = ctk.CTkFrame(parent)
        guidelines_frame.pack(side="bottom", fill="x", pady=(10, 5), padx=10)

        ctk.CTkLabel(guidelines_frame, text="Guidelines:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 2))

        btn_h_guide = ctk.CTkButton(
            guidelines_frame,
            text="➕ Horizontal",
            command=lambda: self._add_guideline("horizontal"),
            width=120,
            height=25
        )
        btn_h_guide.pack(fill="x", pady=2)

        btn_v_guide = ctk.CTkButton(
            guidelines_frame,
            text="➕ Vertical",
            command=lambda: self._add_guideline("vertical"),
            width=120,
            height=25
        )
        btn_v_guide.pack(fill="x", pady=2)

        btn_clear_guides = ctk.CTkButton(
            guidelines_frame,
            text="Clear All",
            command=self._clear_guidelines,
            width=120,
            height=25,
            fg_color="#F44336"
        )
        btn_clear_guides.pack(fill="x", pady=2)

        # Info section
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        ctk.CTkLabel(info_frame, text="Selected:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 2))

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
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        # Right-click for context menu
        self.canvas.bind("<Button-3>", self._on_right_click)

        # Focus for keyboard events
        self.canvas.focus_set()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts"""
        # Undo/Redo
        self.parent.bind_all("<Control-z>", lambda e: self._undo())
        self.parent.bind_all("<Control-Z>", lambda e: self._undo())
        self.parent.bind_all("<Control-y>", lambda e: self._redo())
        self.parent.bind_all("<Control-Y>", lambda e: self._redo())
        self.parent.bind_all("<Control-Shift-z>", lambda e: self._redo())
        self.parent.bind_all("<Control-Shift-Z>", lambda e: self._redo())

        # Save
        self.parent.bind_all("<Control-s>", lambda e: self._save_project())
        self.parent.bind_all("<Control-S>", lambda e: self._save_project())

        # Delete
        self.parent.bind_all("<Delete>", lambda e: self._delete_selected())
        self.parent.bind_all("<BackSpace>", lambda e: self._delete_selected())

        # Select all
        self.parent.bind_all("<Control-a>", lambda e: self._select_all())
        self.parent.bind_all("<Control-A>", lambda e: self._select_all())

        # Space for panning
        self.parent.bind_all("<KeyPress-space>", self._on_space_press)
        self.parent.bind_all("<KeyRelease-space>", self._on_space_release)

        # Arrow keys for nudging
        self.canvas.bind("<Left>", lambda e: self._nudge_selected(-1, 0))
        self.canvas.bind("<Right>", lambda e: self._nudge_selected(1, 0))
        self.canvas.bind("<Up>", lambda e: self._nudge_selected(0, -1))
        self.canvas.bind("<Down>", lambda e: self._nudge_selected(0, 1))

        # Shift+Arrow for larger nudges
        self.canvas.bind("<Shift-Left>", lambda e: self._nudge_selected(-10, 0))
        self.canvas.bind("<Shift-Right>", lambda e: self._nudge_selected(10, 0))
        self.canvas.bind("<Shift-Up>", lambda e: self._nudge_selected(0, -10))
        self.canvas.bind("<Shift-Down>", lambda e: self._nudge_selected(0, 10))

    def _add_artwork_to_workspace(self, artwork):
        """Add artwork to workspace at center"""
        if not self.app.current_workspace:
            return

        # Calculate total dimensions including frame
        total_width_cm = artwork.real_width_cm
        total_height_cm = artwork.real_height_cm

        if artwork.frame_config:
            total_width_cm, total_height_cm = FrameRenderer.calculate_total_dimensions(
                artwork.real_width_cm,
                artwork.real_height_cm,
                artwork.frame_config
            )

        # Place at center of wall
        x = self.app.current_wall.real_width_cm / 2 - total_width_cm / 2
        y = self.app.current_wall.real_height_cm / 2 - total_height_cm / 2

        # Create command for undo
        def undo_add(data):
            self.app.current_workspace.remove_artwork(data['art_id'])
            self._render_workspace()

        def redo_add(data):
            self.app.current_workspace.add_artwork(data['art_id'], data['x'], data['y'])
            self._render_workspace()

        command = Command(
            name=f"Add {artwork.name}",
            undo_func=undo_add,
            redo_func=redo_add,
            undo_data={'art_id': artwork.art_id},
            redo_data={'art_id': artwork.art_id, 'x': x, 'y': y}
        )

        self.undo_manager.execute(command)
        self._update_undo_redo_buttons()

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
        if self.app.current_wall.type == "photo" and self.app.current_wall.corrected_image is not None:
            # Render wall photo as background
            self._render_wall_photo(offset_x, offset_y, wall_width_px, wall_height_px)
        else:
            # Render solid color background
            self.canvas.create_rectangle(
                offset_x, offset_y,
                offset_x + wall_width_px, offset_y + wall_height_px,
                fill=self.app.current_wall.color,
                outline="#999999",
                width=2,
                tags="wall"
            )

        # Render grid if enabled
        if self.grid_var.get():
            self._render_grid(offset_x, offset_y, wall_width_px, wall_height_px)

        # Render guidelines
        self._render_guidelines(offset_x, offset_y, wall_width_px, wall_height_px)

        # Render placed artwork
        for placed in self.app.current_workspace.placed_artworks:
            self._render_placed_artwork(placed, offset_x, offset_y)

        # Render measurements if enabled
        if self.measurements_var.get():
            self._render_measurements(offset_x, offset_y)

    def _render_wall_photo(self, offset_x, offset_y, wall_width_px, wall_height_px):
        """Render wall photo as background"""
        try:
            import cv2
            from PIL import Image, ImageTk

            # Convert wall image to PIL
            wall_img = cv2.cvtColor(self.app.current_wall.corrected_image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(wall_img)

            # Resize to fit canvas dimensions
            pil_img = pil_img.resize((int(wall_width_px), int(wall_height_px)), Image.Resampling.LANCZOS)

            # Store reference to prevent garbage collection
            if not hasattr(self, 'wall_photo_tk'):
                self.wall_photo_tk = {}

            self.wall_photo_tk[self.zoom] = ImageTk.PhotoImage(pil_img)

            # Create image on canvas
            self.canvas.create_image(
                offset_x, offset_y,
                image=self.wall_photo_tk[self.zoom],
                anchor="nw",
                tags="wall"
            )

            # Add border
            self.canvas.create_rectangle(
                offset_x, offset_y,
                offset_x + wall_width_px, offset_y + wall_height_px,
                outline="#999999",
                width=2,
                tags="wall"
            )

        except Exception as e:
            print(f"Error rendering wall photo: {e}")
            # Fallback to color rectangle
            self.canvas.create_rectangle(
                offset_x, offset_y,
                offset_x + wall_width_px, offset_y + wall_height_px,
                fill="#CCCCCC",
                outline="#999999",
                width=2,
                tags="wall"
            )

    def _render_grid(self, offset_x, offset_y, wall_width_px, wall_height_px):
        """Render grid lines"""
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

    def _render_guidelines(self, offset_x, offset_y, wall_width_px, wall_height_px):
        """Render draggable guidelines"""
        for i, (orientation, position_cm) in enumerate(self.guidelines):
            if orientation == "horizontal":
                y = offset_y + real_to_pixels(position_cm, self.scale)
                self.canvas.create_line(
                    offset_x, y,
                    offset_x + wall_width_px, y,
                    fill=config.GUIDE_LINE_COLOR,
                    width=config.GUIDE_LINE_WIDTH,
                    dash=config.GUIDE_DASH_PATTERN,
                    tags=("guideline", f"guide_{i}")
                )
            else:  # vertical
                x = offset_x + real_to_pixels(position_cm, self.scale)
                self.canvas.create_line(
                    x, offset_y,
                    x, offset_y + wall_height_px,
                    fill=config.GUIDE_LINE_COLOR,
                    width=config.GUIDE_LINE_WIDTH,
                    dash=config.GUIDE_DASH_PATTERN,
                    tags=("guideline", f"guide_{i}")
                )

    def _render_measurements(self, offset_x, offset_y):
        """Render measurements between artwork pieces"""
        # Show spacing between selected artwork and edges/other pieces
        if len(self.selected_placed) > 0:
            for placed in self.selected_placed:
                artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
                if not artwork:
                    continue

                # Get artwork dimensions
                width_cm, height_cm = FrameRenderer.calculate_total_dimensions(
                    artwork.real_width_cm,
                    artwork.real_height_cm,
                    artwork.frame_config
                )

                x1_cm = placed.x
                y1_cm = placed.y
                x2_cm = x1_cm + width_cm
                y2_cm = y1_cm + height_cm

                # Distance to left edge
                self._draw_measurement_line(
                    offset_x, offset_y + real_to_pixels(y1_cm + height_cm/2, self.scale),
                    offset_x + real_to_pixels(x1_cm, self.scale), offset_y + real_to_pixels(y1_cm + height_cm/2, self.scale),
                    f"{x1_cm:.1f}cm"
                )

                # Distance to top edge
                self._draw_measurement_line(
                    offset_x + real_to_pixels(x1_cm + width_cm/2, self.scale), offset_y,
                    offset_x + real_to_pixels(x1_cm + width_cm/2, self.scale), offset_y + real_to_pixels(y1_cm, self.scale),
                    f"{y1_cm:.1f}cm"
                )

    def _draw_measurement_line(self, x1, y1, x2, y2, text):
        """Draw a measurement line with text"""
        # Draw line
        self.canvas.create_line(x1, y1, x2, y2, fill="#FF6B6B", width=1, tags="measurement")

        # Draw end markers
        self.canvas.create_line(x1-3, y1-3, x1+3, y1+3, fill="#FF6B6B", width=1, tags="measurement")
        self.canvas.create_line(x1-3, y1+3, x1+3, y1-3, fill="#FF6B6B", width=1, tags="measurement")
        self.canvas.create_line(x2-3, y2-3, x2+3, y2+3, fill="#FF6B6B", width=1, tags="measurement")
        self.canvas.create_line(x2-3, y2+3, x2+3, y2-3, fill="#FF6B6B", width=1, tags="measurement")

        # Draw text
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        self.canvas.create_text(cx, cy - 10, text=text, fill="#FF6B6B", font=("Arial", 9, "bold"), tags="measurement")

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
        if placed in self.selected_placed:
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
            self._on_pan_start(event)
            return

        # Check if clicking on a guideline
        items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        guideline_items = [i for i in items if "guideline" in self.canvas.gettags(i)]

        if guideline_items:
            # Start dragging guideline
            tags = self.canvas.gettags(guideline_items[0])
            guide_tag = [t for t in tags if t.startswith("guide_")][0]
            guide_idx = int(guide_tag.split("_")[1])
            self.dragging_guideline = guide_idx
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            return

        # Find clicked artwork - use larger search area
        items = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        artwork_items = [i for i in items if "artwork" in self.canvas.gettags(i)]

        # If not found with small area, try checking all artwork positions directly
        if not artwork_items:
            offset_x = self.pan_offset_x
            offset_y = self.pan_offset_y

            for placed in self.app.current_workspace.placed_artworks:
                artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
                if not artwork:
                    continue

                # Calculate artwork dimensions and position
                if artwork.frame_config:
                    width_cm, height_cm = FrameRenderer.calculate_total_dimensions(
                        artwork.real_width_cm,
                        artwork.real_height_cm,
                        artwork.frame_config
                    )
                else:
                    width_cm = artwork.real_width_cm
                    height_cm = artwork.real_height_cm

                x_px = offset_x + real_to_pixels(placed.x, self.scale)
                y_px = offset_y + real_to_pixels(placed.y, self.scale)
                w_px = real_to_pixels(width_cm, self.scale)
                h_px = real_to_pixels(height_cm, self.scale)

                # Check if click is within artwork bounds
                if (x_px <= event.x <= x_px + w_px and y_px <= event.y <= y_px + h_px):
                    # Check for Ctrl key (multi-select)
                    if event.state & 0x0004:  # Ctrl is held
                        if placed in self.selected_placed:
                            self.selected_placed.remove(placed)
                        else:
                            self.selected_placed.append(placed)
                    else:
                        self.selected_placed = [placed]

                    self.dragging_item = placed
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    self._update_selection_info()
                    self._render_workspace()
                    return

        elif artwork_items:
            # Get the topmost artwork item
            item = artwork_items[-1]

            # Find which placed artwork this is
            for placed, (canvas_id, _) in self.canvas_items.items():
                if canvas_id == item:
                    # Check for Ctrl key (multi-select)
                    if event.state & 0x0004:  # Ctrl is held
                        if placed in self.selected_placed:
                            self.selected_placed.remove(placed)
                        else:
                            self.selected_placed.append(placed)
                    else:
                        self.selected_placed = [placed]

                    self.dragging_item = placed
                    self.drag_start_x = event.x
                    self.drag_start_y = event.y
                    self._update_selection_info()
                    self._render_workspace()
                    return

        # Clicked on empty space - deselect all
        self.selected_placed = []
        self._update_selection_info()
        self._render_workspace()

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.panning:
            self._on_pan_drag(event)
            return

        if self.dragging_guideline is not None:
            # Drag guideline
            orientation, _ = self.guidelines[self.dragging_guideline]

            if orientation == "horizontal":
                delta_y = event.y - self.drag_start_y
                new_pos_cm = pixels_to_real(event.y - self.pan_offset_y, self.scale)
                new_pos_cm = max(0, min(new_pos_cm, self.app.current_wall.real_height_cm))
                self.guidelines[self.dragging_guideline] = (orientation, new_pos_cm)
            else:
                delta_x = event.x - self.drag_start_x
                new_pos_cm = pixels_to_real(event.x - self.pan_offset_x, self.scale)
                new_pos_cm = max(0, min(new_pos_cm, self.app.current_wall.real_width_cm))
                self.guidelines[self.dragging_guideline] = (orientation, new_pos_cm)

            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self._render_workspace()
            return

        if self.dragging_item:
            # Calculate delta in pixels
            dx_px = event.x - self.drag_start_x
            dy_px = event.y - self.drag_start_y

            # Convert to real-world units (scale is pixels per cm)
            dx_cm = dx_px / self.scale if self.scale > 0 else 0
            dy_cm = dy_px / self.scale if self.scale > 0 else 0

            # Move all selected items
            for placed in self.selected_placed:
                placed.x += dx_cm
                placed.y += dy_cm

                # Apply snapping
                self._apply_snapping(placed)

                # Clamp to wall bounds
                self._clamp_to_wall(placed)

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            # Re-render
            self._render_workspace()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        if self.panning:
            self._on_pan_end(event)
        elif self.dragging_item:
            # Create undo command for the move
            # This is simplified - a full implementation would store initial positions
            self.dragging_item = None
        self.dragging_guideline = None

    def _apply_snapping(self, placed: PlacedArtwork):
        """Apply snapping to grid and guides"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return

        width_cm, height_cm = FrameRenderer.calculate_total_dimensions(
            artwork.real_width_cm,
            artwork.real_height_cm,
            artwork.frame_config
        )

        # Snap to grid
        if self.snap_grid_var.get():
            grid_size = config.DEFAULT_GRID_SPACING_CM
            placed.x = round(placed.x / grid_size) * grid_size
            placed.y = round(placed.y / grid_size) * grid_size

        # Snap to guidelines
        if self.snap_guides_var.get():
            tolerance = self.snap_tolerance_cm

            for orientation, pos in self.guidelines:
                if orientation == "horizontal":
                    # Check top, middle, and bottom of artwork
                    if abs(placed.y - pos) < tolerance:
                        placed.y = pos
                    elif abs(placed.y + height_cm/2 - pos) < tolerance:
                        placed.y = pos - height_cm/2
                    elif abs(placed.y + height_cm - pos) < tolerance:
                        placed.y = pos - height_cm
                else:  # vertical
                    # Check left, center, and right of artwork
                    if abs(placed.x - pos) < tolerance:
                        placed.x = pos
                    elif abs(placed.x + width_cm/2 - pos) < tolerance:
                        placed.x = pos - width_cm/2
                    elif abs(placed.x + width_cm - pos) < tolerance:
                        placed.x = pos - width_cm

    def _clamp_to_wall(self, placed: PlacedArtwork):
        """Clamp artwork position to wall bounds"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return

        # Calculate artwork total size
        total_width, total_height = FrameRenderer.calculate_total_dimensions(
            artwork.real_width_cm,
            artwork.real_height_cm,
            artwork.frame_config
        )

        # Clamp
        placed.x = max(0, min(placed.x, self.app.current_wall.real_width_cm - total_width))
        placed.y = max(0, min(placed.y, self.app.current_wall.real_height_cm - total_height))

    def _align(self, direction: str):
        """Align selected artwork"""
        if len(self.selected_placed) < 2:
            return

        # Calculate reference position
        if direction == "left":
            ref_x = min(p.x for p in self.selected_placed)
            for placed in self.selected_placed:
                placed.x = ref_x
        elif direction == "right":
            # Align right edges
            max_right = max(
                p.x + self._get_artwork_width(p)
                for p in self.selected_placed
            )
            for placed in self.selected_placed:
                placed.x = max_right - self._get_artwork_width(placed)
        elif direction == "center_h":
            # Align horizontal centers
            avg_center = sum(p.x + self._get_artwork_width(p)/2 for p in self.selected_placed) / len(self.selected_placed)
            for placed in self.selected_placed:
                placed.x = avg_center - self._get_artwork_width(placed)/2
        elif direction == "top":
            ref_y = min(p.y for p in self.selected_placed)
            for placed in self.selected_placed:
                placed.y = ref_y
        elif direction == "bottom":
            max_bottom = max(
                p.y + self._get_artwork_height(p)
                for p in self.selected_placed
            )
            for placed in self.selected_placed:
                placed.y = max_bottom - self._get_artwork_height(placed)
        elif direction == "center_v":
            avg_center = sum(p.y + self._get_artwork_height(p)/2 for p in self.selected_placed) / len(self.selected_placed)
            for placed in self.selected_placed:
                placed.y = avg_center - self._get_artwork_height(placed)/2

        self._render_workspace()

    def _distribute(self, direction: str):
        """Distribute selected artwork evenly"""
        if len(self.selected_placed) < 3:
            return

        if direction == "horizontal":
            # Sort by x position
            sorted_placed = sorted(self.selected_placed, key=lambda p: p.x)

            # Calculate total space and gaps
            left_most = sorted_placed[0].x
            right_most = sorted_placed[-1].x + self._get_artwork_width(sorted_placed[-1])
            total_width = sum(self._get_artwork_width(p) for p in sorted_placed)
            available_space = right_most - left_most - total_width
            gap = available_space / (len(sorted_placed) - 1)

            # Distribute
            current_x = left_most
            for placed in sorted_placed:
                placed.x = current_x
                current_x += self._get_artwork_width(placed) + gap
        else:  # vertical
            # Sort by y position
            sorted_placed = sorted(self.selected_placed, key=lambda p: p.y)

            # Calculate total space and gaps
            top_most = sorted_placed[0].y
            bottom_most = sorted_placed[-1].y + self._get_artwork_height(sorted_placed[-1])
            total_height = sum(self._get_artwork_height(p) for p in sorted_placed)
            available_space = bottom_most - top_most - total_height
            gap = available_space / (len(sorted_placed) - 1)

            # Distribute
            current_y = top_most
            for placed in sorted_placed:
                placed.y = current_y
                current_y += self._get_artwork_height(placed) + gap

        self._render_workspace()

    def _get_artwork_width(self, placed: PlacedArtwork) -> float:
        """Get total width of placed artwork including frame"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return 0
        width, _ = FrameRenderer.calculate_total_dimensions(
            artwork.real_width_cm,
            artwork.real_height_cm,
            artwork.frame_config
        )
        return width

    def _get_artwork_height(self, placed: PlacedArtwork) -> float:
        """Get total height of placed artwork including frame"""
        artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
        if not artwork:
            return 0
        _, height = FrameRenderer.calculate_total_dimensions(
            artwork.real_width_cm,
            artwork.real_height_cm,
            artwork.frame_config
        )
        return height

    def _add_guideline(self, orientation: str):
        """Add a new guideline"""
        if orientation == "horizontal":
            # Add at vertical center
            position = self.app.current_wall.real_height_cm / 2
        else:
            # Add at horizontal center
            position = self.app.current_wall.real_width_cm / 2

        self.guidelines.append((orientation, position))
        self._render_workspace()

    def _clear_guidelines(self):
        """Clear all guidelines"""
        self.guidelines.clear()
        self._render_workspace()

    def _toggle_grid(self):
        """Toggle grid display"""
        self._render_workspace()

    def _toggle_measurements(self):
        """Toggle measurements display"""
        self.show_measurements = self.measurements_var.get()
        self._render_workspace()

    def _toggle_snap_grid(self):
        """Toggle snap to grid"""
        self.snap_to_grid = self.snap_grid_var.get()

    def _toggle_snap_guides(self):
        """Toggle snap to guides"""
        self.snap_to_guides = self.snap_guides_var.get()

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
            self._zoom_in()
        elif event.num == 5 or event.delta < 0:
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
                    if placed not in self.selected_placed:
                        self.selected_placed = [placed]
                        self._update_selection_info()
                        self._render_workspace()

                    # Show context menu
                    import tkinter as tk
                    menu = tk.Menu(self.canvas, tearoff=0)
                    menu.add_command(label="Delete", command=self._delete_selected)
                    menu.add_separator()
                    menu.add_command(label="Bring to Front", command=lambda: self._bring_to_front())
                    menu.add_command(label="Send to Back", command=lambda: self._send_to_back())
                    menu.post(event.x_root, event.y_root)
                    break

    def _bring_to_front(self):
        """Bring selected artwork to front"""
        if not self.selected_placed:
            return
        max_z = max(p.z_index for p in self.app.current_workspace.placed_artworks)
        for placed in self.selected_placed:
            placed.z_index = max_z + 1
        self._render_workspace()

    def _send_to_back(self):
        """Send selected artwork to back"""
        if not self.selected_placed:
            return
        min_z = min(p.z_index for p in self.app.current_workspace.placed_artworks)
        for placed in self.selected_placed:
            placed.z_index = min_z - 1
        self._render_workspace()

    def _delete_selected(self):
        """Delete selected artwork from workspace"""
        if not self.selected_placed:
            return

        # Create undo command
        deleted_items = [(p.artwork_id, copy.deepcopy(p)) for p in self.selected_placed]

        def undo_delete(data):
            for art_id, placed_copy in data:
                # Re-add the artwork
                new_placed = PlacedArtwork(
                    artwork_id=placed_copy.artwork_id,
                    x=placed_copy.x,
                    y=placed_copy.y,
                    rotation=placed_copy.rotation,
                    z_index=placed_copy.z_index
                )
                self.app.current_workspace.placed_artworks.append(new_placed)
            self._render_workspace()

        def redo_delete(data):
            for art_id, _ in data:
                self.app.current_workspace.remove_artwork(art_id)
            self._render_workspace()

        command = Command(
            name=f"Delete {len(deleted_items)} item(s)",
            undo_func=undo_delete,
            redo_func=redo_delete,
            undo_data=deleted_items,
            redo_data=deleted_items
        )

        self.undo_manager.execute(command)
        self.selected_placed = []
        self._update_selection_info()
        self._update_undo_redo_buttons()

    def _select_all(self):
        """Select all artwork"""
        self.selected_placed = list(self.app.current_workspace.placed_artworks)
        self._update_selection_info()
        self._render_workspace()

    def _nudge_selected(self, dx, dy):
        """Nudge selected artwork by arrow keys"""
        if not self.selected_placed:
            return

        for placed in self.selected_placed:
            placed.x += dx
            placed.y += dy
            self._clamp_to_wall(placed)

        self._render_workspace()

    def _update_selection_info(self):
        """Update selection info in sidebar"""
        if len(self.selected_placed) == 0:
            self.info_label.configure(text="None", text_color="gray")
        elif len(self.selected_placed) == 1:
            placed = self.selected_placed[0]
            artwork = next((a for a in self.app.artworks if a.art_id == placed.artwork_id), None)
            if artwork:
                info_text = f"{artwork.name}\nPosition: ({placed.x:.1f}, {placed.y:.1f}) cm"
                self.info_label.configure(text=info_text, text_color="white")
        else:
            self.info_label.configure(text=f"{len(self.selected_placed)} items selected", text_color="white")

    def _zoom_in(self):
        """Zoom in"""
        old_zoom = self.zoom
        self.zoom = min(self.zoom + config.ZOOM_STEP, config.MAX_ZOOM)

        if old_zoom != self.zoom:
            self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
            self.rendered_frames.clear()
            self._render_workspace()

    def _zoom_out(self):
        """Zoom out"""
        old_zoom = self.zoom
        self.zoom = max(self.zoom - config.ZOOM_STEP, config.MIN_ZOOM)

        if old_zoom != self.zoom:
            self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")
            self.rendered_frames.clear()
            self._render_workspace()

    def _zoom_fit(self):
        """Fit wall to canvas"""
        self.zoom = 1.0
        self.pan_offset_x = 20
        self.pan_offset_y = 20
        self.zoom_label.configure(text="100%")
        self.rendered_frames.clear()
        self._render_workspace()

    def _undo(self):
        """Undo last action"""
        if self.undo_manager.undo():
            self._update_undo_redo_buttons()

    def _redo(self):
        """Redo last undone action"""
        if self.undo_manager.redo():
            self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        """Update undo/redo button states"""
        if self.undo_manager.can_undo():
            self.btn_undo.configure(state="normal", text=f"↶ Undo")
        else:
            self.btn_undo.configure(state="disabled", text="↶ Undo")

        if self.undo_manager.can_redo():
            self.btn_redo.configure(state="normal", text=f"↷ Redo")
        else:
            self.btn_redo.configure(state="disabled", text="↷ Redo")

    def _on_workspace_changed(self, workspace_name: str):
        """Handle workspace selection change"""
        # Find the workspace
        for workspace in self.app.workspaces:
            if workspace.name == workspace_name:
                # Save current workspace state first
                if self.app.current_workspace:
                    self.app.current_workspace.grid_enabled = self.grid_var.get()
                    self.app.current_workspace.grid_spacing_cm = config.DEFAULT_GRID_SPACING_CM
                    self.app.current_workspace.guidelines = self.guidelines.copy()
                    self.app.current_workspace.show_measurements = self.show_measurements
                    self.app.current_workspace.zoom_level = self.zoom
                    self.app.current_workspace.pan_offset_x = self.pan_offset_x
                    self.app.current_workspace.pan_offset_y = self.pan_offset_y

                # Switch to new workspace
                self.app.switch_workspace(workspace)

                # Restore workspace state
                self.grid_var.set(workspace.grid_enabled)
                self.guidelines = workspace.guidelines.copy() if workspace.guidelines else []
                self.show_measurements = workspace.show_measurements
                self.zoom = workspace.zoom_level
                self.pan_offset_x = workspace.pan_offset_x
                self.pan_offset_y = workspace.pan_offset_y

                # Clear selection and undo history
                self.selected_placed = []
                self.undo_manager.clear()

                # Re-render
                self._render_workspace()
                self._update_undo_redo_buttons()
                break

    def _new_workspace(self):
        """Create a new workspace"""
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "New Workspace",
            "Enter a name for the new workspace:",
            parent=self.parent
        )

        if not name:
            return

        # Create new workspace
        new_workspace = self.app.create_new_workspace(name)

        # Refresh dropdown
        self._refresh_workspace_list()
        self.workspace_var.set(new_workspace.name)

        # Clear and render
        self.selected_placed = []
        self.guidelines = []
        self.undo_manager.clear()
        self._render_workspace()
        self._update_undo_redo_buttons()

    def _duplicate_workspace(self):
        """Duplicate current workspace"""
        if not self.app.current_workspace:
            return

        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Duplicate Workspace",
            "Enter a name for the duplicated workspace:",
            parent=self.parent,
            initialvalue=f"{self.app.current_workspace.name} (Copy)"
        )

        if not name:
            return

        # Duplicate workspace
        new_workspace = self.app.duplicate_workspace(self.app.current_workspace, name)

        # Refresh dropdown
        self._refresh_workspace_list()
        self.workspace_var.set(new_workspace.name)

        self.app._show_info(f"Workspace duplicated as '{name}'")

    def _rename_workspace(self):
        """Rename current workspace"""
        if not self.app.current_workspace:
            return

        from tkinter import simpledialog

        new_name = simpledialog.askstring(
            "Rename Workspace",
            "Enter a new name for the workspace:",
            parent=self.parent,
            initialvalue=self.app.current_workspace.name
        )

        if not new_name:
            return

        # Rename
        self.app.rename_workspace(self.app.current_workspace, new_name)

        # Refresh dropdown
        self._refresh_workspace_list()
        self.workspace_var.set(new_name)

        self.app._show_info(f"Workspace renamed to '{new_name}'")

    def _delete_workspace(self):
        """Delete current workspace"""
        if not self.app.current_workspace:
            return

        if len(self.app.workspaces) == 1:
            self.app._show_error("Cannot delete the last workspace")
            return

        from tkinter import messagebox

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete workspace '{self.app.current_workspace.name}'?\n\nThis cannot be undone."
        ):
            return

        # Delete
        if self.app.delete_workspace(self.app.current_workspace):
            # Refresh dropdown
            self._refresh_workspace_list()
            if self.app.current_workspace:
                self.workspace_var.set(self.app.current_workspace.name)

            # Clear and render
            self.selected_placed = []
            self.undo_manager.clear()
            self._render_workspace()
            self._update_undo_redo_buttons()

            self.app._show_info("Workspace deleted")

    def _refresh_workspace_list(self):
        """Refresh workspace dropdown list"""
        if hasattr(self, 'workspace_dropdown'):
            workspace_names = [w.name for w in self.app.workspaces] if self.app.workspaces else ["No workspaces"]
            self.workspace_dropdown.configure(values=workspace_names)

    def _save_project(self):
        """Save project"""
        # Save current workspace state before saving
        if self.app.current_workspace:
            self.app.current_workspace.grid_enabled = self.grid_var.get()
            self.app.current_workspace.grid_spacing_cm = config.DEFAULT_GRID_SPACING_CM
            self.app.current_workspace.guidelines = self.guidelines.copy()
            self.app.current_workspace.show_measurements = self.show_measurements
            self.app.current_workspace.zoom_level = self.zoom
            self.app.current_workspace.pan_offset_x = self.pan_offset_x
            self.app.current_workspace.pan_offset_y = self.pan_offset_y

        self.app.save_project()

    def _export_image(self):
        """Export workspace to image with enhanced options"""
        if not self.app.current_workspace:
            return

        # Show export options dialog
        dialog = ExportDialog(self.parent, self.app.current_wall)
        self.parent.wait_window(dialog.dialog)

        if not dialog.result:
            return  # User cancelled

        # Get export settings
        settings = dialog.result

        # Ask for file path
        default_ext = ".png" if settings['format'] == "PNG" else ".jpg"
        filetypes = [
            ("PNG Image", "*.png"),
            ("JPEG Image", "*.jpg *.jpeg")
        ] if settings['format'] == "PNG" else [
            ("JPEG Image", "*.jpg *.jpeg"),
            ("PNG Image", "*.png")
        ]

        file_path = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=default_ext,
            filetypes=filetypes
        )

        if not file_path:
            return

        # Get dimensions
        output_width = settings['width']
        output_height = settings['height']

        # Export
        success = ExportRenderer.export_workspace(
            self.app.current_workspace,
            self.app.current_wall,
            self.app.artworks,
            self.app.artwork_images,
            output_width,
            output_height,
            file_path,
            format=settings['format'],
            quality=settings['quality']
        )

        if success:
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            self.app._show_info(
                f"Image exported successfully!\n\n"
                f"Resolution: {output_width}x{output_height}\n"
                f"Format: {settings['format']}\n"
                f"Size: {file_size_mb:.1f} MB"
            )
        else:
            self.app._show_error("Failed to export image")



class ExportDialog:
    """Dialog for export options"""

    def __init__(self, parent, wall):
        """Initialize export dialog"""
        self.result = None
        self.wall = wall

        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Export Options")
        self.dialog.geometry("400x550")
        self.dialog.resizable(False, False)

        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI"""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(main_frame, text="Export Settings", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 20))

        # Format selection
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(format_frame, text="Format:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)

        self.format_var = ctk.StringVar(value="PNG")
        format_options = ctk.CTkFrame(format_frame)
        format_options.pack(fill="x", padx=5)

        ctk.CTkRadioButton(
            format_options,
            text="PNG (Lossless)",
            variable=self.format_var,
            value="PNG",
            command=self._on_format_changed
        ).pack(side="left", padx=5)

        ctk.CTkRadioButton(
            format_options,
            text="JPEG (Smaller file)",
            variable=self.format_var,
            value="JPEG",
            command=self._on_format_changed
        ).pack(side="left", padx=5)

        # Quality slider (for JPEG)
        self.quality_frame = ctk.CTkFrame(format_frame)
        self.quality_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(self.quality_frame, text="JPEG Quality:", font=("Arial", 10)).pack(anchor="w", padx=5)

        self.quality_var = ctk.IntVar(value=95)
        self.quality_slider = ctk.CTkSlider(
            self.quality_frame,
            from_=60,
            to=100,
            variable=self.quality_var,
            number_of_steps=40
        )
        self.quality_slider.pack(fill="x", padx=5)

        self.quality_label = ctk.CTkLabel(self.quality_frame, text="95%", font=("Arial", 9))
        self.quality_label.pack(anchor="e", padx=5)

        self.quality_slider.configure(command=self._on_quality_changed)
        self.quality_frame.pack_forget()  # Hide initially for PNG

        # Resolution settings
        size_frame = ctk.CTkFrame(main_frame)
        size_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(size_frame, text="Resolution:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)

        dim_inputs = ctk.CTkFrame(size_frame)
        dim_inputs.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(dim_inputs, text="Width:", width=50).pack(side="left", padx=2)
        self.width_var = ctk.IntVar(value=3840)
        width_entry = ctk.CTkEntry(dim_inputs, textvariable=self.width_var, width=100)
        width_entry.pack(side="left", padx=2)
        width_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        ctk.CTkLabel(dim_inputs, text="px    Height:", width=80).pack(side="left", padx=5)
        self.height_var = ctk.IntVar(value=2160)
        height_entry = ctk.CTkEntry(dim_inputs, textvariable=self.height_var, width=100)
        height_entry.pack(side="left", padx=2)
        height_entry.bind("<KeyRelease>", lambda e: self._update_preview())

        ctk.CTkLabel(dim_inputs, text="px").pack(side="left", padx=2)

        # Preview info
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="x", pady=15)

        ctk.CTkLabel(preview_frame, text="Export Preview:", font=("Arial", 11, "bold")).pack(anchor="w", padx=5)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Resolution: 3840 x 2160\nEstimated size: ~8 MB",
            font=("Arial", 10),
            anchor="w",
            justify="left"
        )
        self.preview_label.pack(anchor="w", padx=10, pady=5)

        self._update_preview()

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Export",
            command=self._export,
            width=120,
            fg_color="#4CAF50"
        ).pack(side="right", padx=5)

    def _on_format_changed(self):
        """Handle format change"""
        if self.format_var.get() == "JPEG":
            self.quality_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.quality_frame.pack_forget()
        self._update_preview()

    def _on_quality_changed(self, value):
        """Handle quality slider change"""
        self.quality_label.configure(text=f"{int(value)}%")
        self._update_preview()

    def _update_preview(self):
        """Update preview information"""
        # Get dimensions
        try:
            width = self.width_var.get()
            height = self.height_var.get()
        except:
            width = 3840
            height = 2160

        if width <= 0 or height <= 0:
            width = 3840
            height = 2160

        # Estimate file size (rough approximation)
        pixels = width * height
        if self.format_var.get() == "PNG":
            estimated_mb = pixels * 3 / (1024 * 1024)  # ~3 bytes per pixel for PNG
        else:
            quality_factor = self.quality_var.get() / 100.0
            estimated_mb = pixels * 0.5 * quality_factor / (1024 * 1024)  # JPEG compression

        self.preview_label.configure(
            text=f"Resolution: {width} x {height} px\n"
                 f"Aspect ratio: {width/height:.2f}\n"
                 f"Estimated size: ~{estimated_mb:.1f} MB"
        )

    def _cancel(self):
        """Cancel export"""
        self.result = None
        self.dialog.destroy()

    def _export(self):
        """Confirm export"""
        # Get final dimensions
        width = self.width_var.get()
        height = self.height_var.get()

        self.result = {
            "format": self.format_var.get(),
            "quality": self.quality_var.get(),
            "width": width,
            "height": height
        }
        self.dialog.destroy()

