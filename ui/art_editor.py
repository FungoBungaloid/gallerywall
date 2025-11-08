"""
Art Editor Screen - Enhanced with Advanced Editing Tools
"""
import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import os
import cv2
import numpy as np
from models.artwork import Artwork
from processors.image_processor import ImageProcessor
from utils.file_manager import FileManager
from utils.perspective import apply_perspective_correction
import config


class ArtEditorScreen:
    """Screen for importing and editing artwork"""

    def __init__(self, app, parent):
        """
        Initialize art editor screen

        Args:
            app: Main application instance
            parent: Parent widget
        """
        self.app = app
        self.parent = parent

        # State
        self.selected_artwork = None
        self.thumbnail_images = {}  # art_id -> PhotoImage for thumbnails
        self.preview_image = None  # Current preview PhotoImage

        # Editing state
        self.original_photo = None  # Current artwork being edited (numpy array)
        self.edited_photo = None  # With perspective/crop applied
        self.corner_points = None  # For perspective correction
        self.crop_box = None  # (x1, y1, x2, y2) for crop
        self.dragging_point = None
        self.dragging_crop = None  # 'nw', 'ne', 'sw', 'se', 'move', None

        # White balance adjustments
        self.wb_temperature = 0.0  # -100 to 100
        self.wb_tint = 0.0  # -100 to 100
        self.wb_brightness = 0.0  # -100 to 100
        self.wb_contrast = 0.0  # -100 to 100
        self.wb_saturation = 0.0  # -100 to 100

        # Canvas state
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0

        # Edit mode
        self.edit_mode = "perspective"  # 'perspective', 'crop', 'adjust'

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI"""
        # Main layout
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Left sidebar (artwork list)
        left_panel = ctk.CTkFrame(main_frame, width=280)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        left_panel.pack_propagate(False)

        # Center/right (editing area)
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self._setup_artwork_list(left_panel)
        self._setup_info_panel(right_panel)

    def _setup_artwork_list(self, parent):
        """Set up artwork list sidebar"""
        title = ctk.CTkLabel(parent, text="Artwork", font=("Arial", 16, "bold"))
        title.pack(pady=(10, 5))

        # Import button
        btn_import = ctk.CTkButton(
            parent,
            text="📁 Import Artwork",
            command=self._import_artwork,
            height=35
        )
        btn_import.pack(pady=10, padx=10, fill="x")

        # Artwork list (scrollable)
        self.artwork_list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.artwork_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._refresh_artwork_list()

        # Bottom buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        btn_back = ctk.CTkButton(btn_frame, text="← Back", command=self.app.show_wall_setup_screen, width=100)
        btn_back.pack(side="left", pady=5, padx=2)

        btn_next = ctk.CTkButton(
            btn_frame,
            text="Continue →",
            command=self._continue_to_framing,
            fg_color="#4CAF50",
            width=100
        )
        btn_next.pack(side="right", pady=5, padx=2)

    def _setup_info_panel(self, parent):
        """Set up info/editing panel"""
        self.info_panel = parent

        # Welcome message
        welcome = ctk.CTkLabel(
            parent,
            text="Import artwork to get started\n\nClick 'Import Artwork' to add images",
            font=("Arial", 14),
            text_color="gray"
        )
        welcome.pack(expand=True)

    def _import_artwork(self):
        """Import artwork files"""
        file_paths = filedialog.askopenfilenames(
            title="Select Artwork Images",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("JPEG Images", "*.jpg *.jpeg"),
                ("PNG Images", "*.png"),
                ("All Files", "*.*")
            ]
        )

        if file_paths:
            imported_count = 0
            for file_path in file_paths:
                if self._add_artwork(file_path):
                    imported_count += 1

            self._refresh_artwork_list()

            if imported_count > 0:
                self.app._show_info(f"Successfully imported {imported_count} artwork(s)!")
            else:
                self.app._show_error("Failed to import any images. Please check the file formats.")

    def _add_artwork(self, file_path: str) -> bool:
        """
        Add artwork to collection

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load image
            image = ImageProcessor.load_image(file_path)
            if image is None:
                print(f"Failed to load image: {file_path}")
                return False

            # Create artwork model
            art_id = FileManager.generate_id()
            name = os.path.splitext(os.path.basename(file_path))[0]

            # Get image dimensions for default size
            height, width = image.shape[:2]
            aspect_ratio = width / height

            # Default to 20cm width, calculate height proportionally
            default_width_cm = 20.0
            default_height_cm = default_width_cm / aspect_ratio

            artwork = Artwork(
                art_id=art_id,
                name=name,
                original_image_path=file_path,
                real_width_cm=default_width_cm,
                real_height_cm=default_height_cm,
                real_width_inches=default_width_cm / 2.54,
                real_height_inches=default_height_cm / 2.54
            )

            self.app.artworks.append(artwork)
            self.app.artwork_images[art_id] = image

            # Create thumbnail
            self._create_thumbnail(art_id, image)

            return True

        except Exception as e:
            print(f"Error adding artwork: {e}")
            return False

    def _create_thumbnail(self, art_id: str, image: np.ndarray, size: int = 60):
        """Create thumbnail for artwork"""
        try:
            # Convert to PIL
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            # Create thumbnail maintaining aspect ratio
            pil_img.thumbnail((size, size), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_img)
            self.thumbnail_images[art_id] = photo

        except Exception as e:
            print(f"Error creating thumbnail: {e}")

    def _refresh_artwork_list(self):
        """Refresh the artwork list display"""
        # Clear existing items
        for widget in self.artwork_list_frame.winfo_children():
            widget.destroy()

        if len(self.app.artworks) == 0:
            info = ctk.CTkLabel(
                self.artwork_list_frame,
                text="No artwork imported yet",
                text_color="gray",
                font=("Arial", 10)
            )
            info.pack(pady=20)
            return

        # Add artwork items with thumbnails
        for artwork in self.app.artworks:
            item_frame = ctk.CTkFrame(self.artwork_list_frame, fg_color="#2B2B2B", height=70)
            item_frame.pack(fill="x", pady=3, padx=2)
            item_frame.pack_propagate(False)

            # Thumbnail
            if artwork.art_id in self.thumbnail_images:
                thumb_label = ctk.CTkLabel(
                    item_frame,
                    image=self.thumbnail_images[artwork.art_id],
                    text=""
                )
                thumb_label.pack(side="left", padx=5, pady=5)

            # Info container
            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5)

            name_label = ctk.CTkLabel(
                info_frame,
                text=artwork.name,
                anchor="w",
                font=("Arial", 10, "bold")
            )
            name_label.pack(anchor="w", pady=(5, 2))

            dim_label = ctk.CTkLabel(
                info_frame,
                text=f"{artwork.real_width_cm:.1f} x {artwork.real_height_cm:.1f} cm",
                anchor="w",
                font=("Arial", 8),
                text_color="gray"
            )
            dim_label.pack(anchor="w")

            # Edit button
            edit_btn = ctk.CTkButton(
                item_frame,
                text="✏️ Edit",
                width=70,
                height=30,
                command=lambda a=artwork: self._edit_artwork(a),
                fg_color="#1F6AA5"
            )
            edit_btn.pack(side="right", padx=5, pady=5)

    def _edit_artwork(self, artwork: Artwork):
        """Edit artwork with full editing tools"""
        self.selected_artwork = artwork

        # Load original image
        if artwork.art_id in self.app.artwork_images:
            self.original_photo = self.app.artwork_images[artwork.art_id].copy()
        else:
            self.app._show_error("Image not found for this artwork")
            return

        # Initialize editing state
        height, width = self.original_photo.shape[:2]

        # Load saved editing state or initialize defaults
        if artwork.corner_points and len(artwork.corner_points) == 4:
            self.corner_points = artwork.corner_points.copy()
        else:
            # Default corners (full image)
            margin = 20
            self.corner_points = [
                (margin, margin),  # Top-left
                (width - margin, margin),  # Top-right
                (width - margin, height - margin),  # Bottom-right
                (margin, height - margin)  # Bottom-left
            ]

        if artwork.crop_box:
            self.crop_box = artwork.crop_box
        else:
            self.crop_box = (0, 0, width, height)

        # Load white balance settings
        if artwork.white_balance_adjustments:
            self.wb_temperature = artwork.white_balance_adjustments.get('temperature', 0.0)
            self.wb_tint = artwork.white_balance_adjustments.get('tint', 0.0)
            self.wb_brightness = artwork.white_balance_adjustments.get('brightness', 0.0)
            self.wb_contrast = artwork.white_balance_adjustments.get('contrast', 0.0)
            self.wb_saturation = artwork.white_balance_adjustments.get('saturation', 0.0)
        else:
            self.wb_temperature = 0.0
            self.wb_tint = 0.0
            self.wb_brightness = 0.0
            self.wb_contrast = 0.0
            self.wb_saturation = 0.0

        # Apply current edits
        self._apply_current_edits()

        # Clear info panel and show editor
        for widget in self.info_panel.winfo_children():
            widget.destroy()

        self._setup_editor_ui()

    def _apply_current_edits(self):
        """Apply perspective correction and crop to get edited image"""
        # Start with original
        result = self.original_photo.copy()

        # Apply perspective correction if corners have been modified
        if self.corner_points and len(self.corner_points) == 4:
            # Always apply the perspective transform based on the corner points
            src_points = np.float32(self.corner_points)

            # Calculate output dimensions based on the quadrilateral
            width_top = np.linalg.norm(np.array(self.corner_points[0]) - np.array(self.corner_points[1]))
            width_bottom = np.linalg.norm(np.array(self.corner_points[3]) - np.array(self.corner_points[2]))
            width_out = int(max(width_top, width_bottom))

            height_left = np.linalg.norm(np.array(self.corner_points[0]) - np.array(self.corner_points[3]))
            height_right = np.linalg.norm(np.array(self.corner_points[1]) - np.array(self.corner_points[2]))
            height_out = int(max(height_left, height_right))

            result = apply_perspective_correction(result, src_points, width_out, height_out)

        # Apply crop
        if self.crop_box:
            x1, y1, x2, y2 = self.crop_box
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(result.shape[1], int(x2)), min(result.shape[0], int(y2))
            if x2 > x1 and y2 > y1:
                result = result[y1:y2, x1:x2]

        self.edited_photo = result

    def _setup_editor_ui(self):
        """Set up the editor UI"""
        main_container = ctk.CTkFrame(self.info_panel)
        main_container.pack(fill="both", expand=True)

        # Title
        title_frame = ctk.CTkFrame(main_container)
        title_frame.pack(fill="x", padx=10, pady=5)

        title = ctk.CTkLabel(
            title_frame,
            text=f"Editing: {self.selected_artwork.name}",
            font=("Arial", 16, "bold")
        )
        title.pack(side="left", padx=5)

        # Reset button
        btn_reset = ctk.CTkButton(
            title_frame,
            text="🔄 Reset All",
            command=self._reset_edits,
            width=100,
            fg_color="#F44336"
        )
        btn_reset.pack(side="right", padx=5)

        # Mode selector
        mode_frame = ctk.CTkFrame(main_container)
        mode_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(mode_frame, text="Edit Mode:", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        self.mode_var = ctk.StringVar(value="perspective")

        ctk.CTkRadioButton(
            mode_frame,
            text="Perspective",
            variable=self.mode_var,
            value="perspective",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="Crop",
            variable=self.mode_var,
            value="crop",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="Adjustments",
            variable=self.mode_var,
            value="adjust",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        # Canvas area
        canvas_frame = ctk.CTkFrame(main_container, fg_color="#1a1a1a")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.edit_canvas = Canvas(
            canvas_frame,
            bg="#2a2a2a",
            highlightthickness=1,
            highlightbackground="#444"
        )
        self.edit_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Bind mouse events
        self.edit_canvas.bind("<Button-1>", self._on_canvas_click)
        self.edit_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.edit_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Controls panel
        self.controls_frame = ctk.CTkFrame(main_container)
        self.controls_frame.pack(fill="x", padx=10, pady=5)

        self._setup_controls()

        # Bottom controls (dimensions, save, delete)
        bottom_frame = ctk.CTkFrame(main_container)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        # Name
        name_section = ctk.CTkFrame(bottom_frame)
        name_section.pack(fill="x", pady=5)

        ctk.CTkLabel(name_section, text="Name:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.name_entry = ctk.CTkEntry(name_section, width=300)
        self.name_entry.insert(0, self.selected_artwork.name)
        self.name_entry.pack(side="left", padx=5)

        # Dimensions
        dim_section = ctk.CTkFrame(bottom_frame)
        dim_section.pack(fill="x", pady=5)

        ctk.CTkLabel(dim_section, text="Dimensions:", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        ctk.CTkLabel(dim_section, text="Width (cm):").pack(side="left", padx=2)
        self.width_entry = ctk.CTkEntry(dim_section, width=80)
        self.width_entry.insert(0, f"{self.selected_artwork.real_width_cm:.1f}")
        self.width_entry.pack(side="left", padx=2)

        ctk.CTkLabel(dim_section, text="Height (cm):").pack(side="left", padx=5)
        self.height_entry = ctk.CTkEntry(dim_section, width=80)
        self.height_entry.insert(0, f"{self.selected_artwork.real_height_cm:.1f}")
        self.height_entry.pack(side="left", padx=2)

        # Buttons
        btn_section = ctk.CTkFrame(bottom_frame)
        btn_section.pack(fill="x", pady=10)

        ctk.CTkButton(
            btn_section,
            text="💾 Save Changes",
            command=self._save_changes,
            width=150,
            height=35,
            fg_color="#4CAF50",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_section,
            text="🗑️ Delete",
            command=lambda: self._delete_artwork(self.selected_artwork),
            width=100,
            height=35,
            fg_color="#F44336"
        ).pack(side="left", padx=5)

        # Render initial preview
        self._update_canvas_preview()

    def _setup_controls(self):
        """Set up mode-specific controls"""
        # Clear existing controls
        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        if self.mode_var.get() == "perspective":
            ctk.CTkLabel(
                self.controls_frame,
                text="Drag the corner points to correct perspective distortion",
                font=("Arial", 10),
                text_color="gray"
            ).pack(pady=10)

            ctk.CTkButton(
                self.controls_frame,
                text="Apply Correction",
                command=self._apply_perspective,
                width=150,
                fg_color="#4CAF50"
            ).pack(pady=5)

        elif self.mode_var.get() == "crop":
            ctk.CTkLabel(
                self.controls_frame,
                text="Drag corners to adjust crop area",
                font=("Arial", 10),
                text_color="gray"
            ).pack(pady=10)

            ctk.CTkButton(
                self.controls_frame,
                text="Apply Crop",
                command=self._apply_crop,
                width=150,
                fg_color="#4CAF50"
            ).pack(pady=5)

        elif self.mode_var.get() == "adjust":
            # White balance sliders
            ctk.CTkLabel(
                self.controls_frame,
                text="Color & Tone Adjustments",
                font=("Arial", 11, "bold")
            ).pack(pady=(10, 5))

            # Temperature
            temp_frame = ctk.CTkFrame(self.controls_frame)
            temp_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(temp_frame, text="Temperature:", width=100).pack(side="left")
            self.temp_slider = ctk.CTkSlider(
                temp_frame, from_=-100, to=100,
                command=self._on_wb_change
            )
            self.temp_slider.set(self.wb_temperature)
            self.temp_slider.pack(side="left", fill="x", expand=True, padx=5)
            self.temp_label = ctk.CTkLabel(temp_frame, text=f"{self.wb_temperature:.0f}", width=40)
            self.temp_label.pack(side="left")

            # Tint
            tint_frame = ctk.CTkFrame(self.controls_frame)
            tint_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(tint_frame, text="Tint:", width=100).pack(side="left")
            self.tint_slider = ctk.CTkSlider(
                tint_frame, from_=-100, to=100,
                command=self._on_wb_change
            )
            self.tint_slider.set(self.wb_tint)
            self.tint_slider.pack(side="left", fill="x", expand=True, padx=5)
            self.tint_label = ctk.CTkLabel(tint_frame, text=f"{self.wb_tint:.0f}", width=40)
            self.tint_label.pack(side="left")

            # Brightness
            bright_frame = ctk.CTkFrame(self.controls_frame)
            bright_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(bright_frame, text="Brightness:", width=100).pack(side="left")
            self.bright_slider = ctk.CTkSlider(
                bright_frame, from_=-100, to=100,
                command=self._on_wb_change
            )
            self.bright_slider.set(self.wb_brightness)
            self.bright_slider.pack(side="left", fill="x", expand=True, padx=5)
            self.bright_label = ctk.CTkLabel(bright_frame, text=f"{self.wb_brightness:.0f}", width=40)
            self.bright_label.pack(side="left")

            # Contrast
            contrast_frame = ctk.CTkFrame(self.controls_frame)
            contrast_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(contrast_frame, text="Contrast:", width=100).pack(side="left")
            self.contrast_slider = ctk.CTkSlider(
                contrast_frame, from_=-100, to=100,
                command=self._on_wb_change
            )
            self.contrast_slider.set(self.wb_contrast)
            self.contrast_slider.pack(side="left", fill="x", expand=True, padx=5)
            self.contrast_label = ctk.CTkLabel(contrast_frame, text=f"{self.wb_contrast:.0f}", width=40)
            self.contrast_label.pack(side="left")

            # Saturation
            sat_frame = ctk.CTkFrame(self.controls_frame)
            sat_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(sat_frame, text="Saturation:", width=100).pack(side="left")
            self.sat_slider = ctk.CTkSlider(
                sat_frame, from_=-100, to=100,
                command=self._on_wb_change
            )
            self.sat_slider.set(self.wb_saturation)
            self.sat_slider.pack(side="left", fill="x", expand=True, padx=5)
            self.sat_label = ctk.CTkLabel(sat_frame, text=f"{self.wb_saturation:.0f}", width=40)
            self.sat_label.pack(side="left")

            ctk.CTkButton(
                self.controls_frame,
                text="Reset Adjustments",
                command=self._reset_white_balance,
                width=150
            ).pack(pady=10)

    def _on_mode_changed(self):
        """Handle mode change"""
        self.edit_mode = self.mode_var.get()
        self._setup_controls()
        self._update_canvas_preview()

    def _update_canvas_preview(self):
        """Update the canvas preview"""
        if not hasattr(self, 'edit_canvas'):
            return

        # Get canvas dimensions
        canvas_width = self.edit_canvas.winfo_width()
        canvas_height = self.edit_canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 600
        if canvas_height <= 1:
            canvas_height = 400

        # Determine which image to show based on mode
        if self.mode_var.get() == "perspective":
            display_img = self.original_photo.copy()
        elif self.mode_var.get() == "crop":
            # Show perspective-corrected image for cropping
            self._apply_current_edits()
            display_img = self.edited_photo.copy()
        else:  # adjust
            # Show final edited image with white balance
            self._apply_current_edits()
            display_img = self._apply_white_balance(self.edited_photo)

        # Convert to PIL
        img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Calculate scale to fit canvas
        img_width, img_height = pil_img.size
        scale_w = (canvas_width - 40) / img_width
        scale_h = (canvas_height - 40) / img_height
        self.canvas_scale = min(scale_w, scale_h, 1.0)

        new_width = int(img_width * self.canvas_scale)
        new_height = int(img_height * self.canvas_scale)

        pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.preview_image = ImageTk.PhotoImage(pil_img)

        # Clear canvas
        self.edit_canvas.delete("all")

        # Center image
        self.canvas_offset_x = (canvas_width - new_width) // 2
        self.canvas_offset_y = (canvas_height - new_height) // 2

        # Draw image
        self.edit_canvas.create_image(
            self.canvas_offset_x, self.canvas_offset_y,
            image=self.preview_image,
            anchor="nw",
            tags="preview"
        )

        # Draw overlays based on mode
        if self.mode_var.get() == "perspective":
            self._draw_perspective_markers(self.canvas_offset_x, self.canvas_offset_y)
        elif self.mode_var.get() == "crop":
            self._draw_crop_markers(self.canvas_offset_x, self.canvas_offset_y)

    def _draw_perspective_markers(self, offset_x, offset_y):
        """Draw corner markers for perspective correction"""
        if not self.corner_points or len(self.corner_points) != 4:
            return

        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
        labels = ["TL", "TR", "BR", "BL"]

        for i, (x, y) in enumerate(self.corner_points):
            # Convert to canvas coordinates
            canvas_x = offset_x + x * self.canvas_scale
            canvas_y = offset_y + y * self.canvas_scale

            # Draw circle
            radius = 8
            self.edit_canvas.create_oval(
                canvas_x - radius, canvas_y - radius,
                canvas_x + radius, canvas_y + radius,
                fill=colors[i],
                outline="white",
                width=2,
                tags=("corner", f"corner_{i}")
            )

            # Draw label
            self.edit_canvas.create_text(
                canvas_x, canvas_y,
                text=labels[i],
                fill="black",
                font=("Arial", 8, "bold"),
                tags=("corner", f"corner_{i}")
            )

        # Draw lines connecting corners
        for i in range(4):
            x1, y1 = self.corner_points[i]
            x2, y2 = self.corner_points[(i + 1) % 4]
            self.edit_canvas.create_line(
                offset_x + x1 * self.canvas_scale,
                offset_y + y1 * self.canvas_scale,
                offset_x + x2 * self.canvas_scale,
                offset_y + y2 * self.canvas_scale,
                fill="#00FF00",
                width=2,
                dash=(5, 5),
                tags="corner_line"
            )

    def _draw_crop_markers(self, offset_x, offset_y):
        """Draw crop box with corner handles"""
        if not self.crop_box:
            return

        x1, y1, x2, y2 = self.crop_box

        # Convert to canvas coordinates
        canvas_x1 = offset_x + x1 * self.canvas_scale
        canvas_y1 = offset_y + y1 * self.canvas_scale
        canvas_x2 = offset_x + x2 * self.canvas_scale
        canvas_y2 = offset_y + y2 * self.canvas_scale

        # Draw semi-transparent overlay outside crop area
        # Top
        self.edit_canvas.create_rectangle(
            offset_x, offset_y,
            offset_x + self.preview_image.width(), canvas_y1,
            fill="#000000",
            stipple="gray50",
            tags="crop_overlay"
        )
        # Bottom
        self.edit_canvas.create_rectangle(
            offset_x, canvas_y2,
            offset_x + self.preview_image.width(), offset_y + self.preview_image.height(),
            fill="#000000",
            stipple="gray50",
            tags="crop_overlay"
        )
        # Left
        self.edit_canvas.create_rectangle(
            offset_x, canvas_y1,
            canvas_x1, canvas_y2,
            fill="#000000",
            stipple="gray50",
            tags="crop_overlay"
        )
        # Right
        self.edit_canvas.create_rectangle(
            canvas_x2, canvas_y1,
            offset_x + self.preview_image.width(), canvas_y2,
            fill="#000000",
            stipple="gray50",
            tags="crop_overlay"
        )

        # Draw crop rectangle border
        self.edit_canvas.create_rectangle(
            canvas_x1, canvas_y1,
            canvas_x2, canvas_y2,
            outline="#00FF00",
            width=3,
            tags="crop_box"
        )

        # Draw corner handles - larger and more visible
        handle_size = 12
        corners = [
            (canvas_x1, canvas_y1, "nw"),
            (canvas_x2, canvas_y1, "ne"),
            (canvas_x2, canvas_y2, "se"),
            (canvas_x1, canvas_y2, "sw")
        ]

        for cx, cy, tag in corners:
            # Outer circle
            self.edit_canvas.create_oval(
                cx - handle_size, cy - handle_size,
                cx + handle_size, cy + handle_size,
                fill="#00FF00",
                outline="white",
                width=3,
                tags=("crop_handle", f"crop_{tag}")
            )

    def _on_canvas_click(self, event):
        """Handle canvas click"""
        if self.mode_var.get() == "perspective":
            # Check if clicking on a corner
            radius = 15
            for i, (x, y) in enumerate(self.corner_points):
                canvas_x = self.canvas_offset_x + x * self.canvas_scale
                canvas_y = self.canvas_offset_y + y * self.canvas_scale

                if abs(event.x - canvas_x) < radius and abs(event.y - canvas_y) < radius:
                    self.dragging_point = i
                    return

        elif self.mode_var.get() == "crop":
            # Check if clicking on crop handles
            if self.crop_box:
                x1, y1, x2, y2 = self.crop_box
                canvas_x1 = self.canvas_offset_x + x1 * self.canvas_scale
                canvas_y1 = self.canvas_offset_y + y1 * self.canvas_scale
                canvas_x2 = self.canvas_offset_x + x2 * self.canvas_scale
                canvas_y2 = self.canvas_offset_y + y2 * self.canvas_scale

                # Larger click radius for easier grabbing
                handle_size = 20
                corners = [
                    (canvas_x1, canvas_y1, "nw"),
                    (canvas_x2, canvas_y1, "ne"),
                    (canvas_x2, canvas_y2, "se"),
                    (canvas_x1, canvas_y2, "sw")
                ]

                for cx, cy, tag in corners:
                    dist = ((event.x - cx) ** 2 + (event.y - cy) ** 2) ** 0.5
                    if dist < handle_size:
                        self.dragging_crop = tag
                        return

    def _on_canvas_drag(self, event):
        """Handle canvas drag"""
        if self.mode_var.get() == "perspective" and self.dragging_point is not None:
            # Convert to image coordinates
            img_x = (event.x - self.canvas_offset_x) / self.canvas_scale
            img_y = (event.y - self.canvas_offset_y) / self.canvas_scale

            # Clamp to image bounds
            height, width = self.original_photo.shape[:2]
            img_x = max(0, min(width, img_x))
            img_y = max(0, min(height, img_y))

            self.corner_points[self.dragging_point] = (img_x, img_y)
            self._update_canvas_preview()

        elif self.mode_var.get() == "crop" and self.dragging_crop:
            # Convert to image coordinates
            img_x = (event.x - self.canvas_offset_x) / self.canvas_scale
            img_y = (event.y - self.canvas_offset_y) / self.canvas_scale

            # Clamp to image bounds
            height, width = self.edited_photo.shape[:2]
            img_x = max(0, min(width, img_x))
            img_y = max(0, min(height, img_y))

            x1, y1, x2, y2 = self.crop_box

            # Update the appropriate corner
            if self.dragging_crop == "nw":
                x1, y1 = img_x, img_y
            elif self.dragging_crop == "ne":
                x2, y1 = img_x, img_y
            elif self.dragging_crop == "se":
                x2, y2 = img_x, img_y
            elif self.dragging_crop == "sw":
                x1, y2 = img_x, img_y

            # Ensure minimum crop size (10 pixels)
            min_size = 10
            if x2 - x1 < min_size:
                if self.dragging_crop in ["nw", "sw"]:
                    x1 = x2 - min_size
                else:
                    x2 = x1 + min_size

            if y2 - y1 < min_size:
                if self.dragging_crop in ["nw", "ne"]:
                    y1 = y2 - min_size
                else:
                    y2 = y1 + min_size

            # Clamp again after adjustments
            x1 = max(0, min(width - min_size, x1))
            y1 = max(0, min(height - min_size, y1))
            x2 = max(min_size, min(width, x2))
            y2 = max(min_size, min(height, y2))

            self.crop_box = (x1, y1, x2, y2)
            self._update_canvas_preview()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        self.dragging_point = None
        self.dragging_crop = None

    def _apply_perspective(self):
        """Apply perspective correction"""
        self._apply_current_edits()
        # Reset crop box to full corrected image
        height, width = self.edited_photo.shape[:2]
        self.crop_box = (0, 0, width, height)

        # Switch to crop mode to show the result
        self.mode_var.set("crop")
        self._on_mode_changed()

        self.app._show_info("Perspective correction applied! Now in crop mode.")

    def _apply_crop(self):
        """Apply crop"""
        self._apply_current_edits()
        self._update_canvas_preview()
        self.app._show_info("Crop applied")

    def _apply_white_balance(self, image: np.ndarray) -> np.ndarray:
        """Apply white balance adjustments to image"""
        # Convert to PIL for easier adjustment
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Apply brightness
        if self.wb_brightness != 0:
            factor = 1.0 + (self.wb_brightness / 100.0)
            enhancer = ImageEnhance.Brightness(pil_img)
            pil_img = enhancer.enhance(factor)

        # Apply contrast
        if self.wb_contrast != 0:
            factor = 1.0 + (self.wb_contrast / 100.0)
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(factor)

        # Apply saturation
        if self.wb_saturation != 0:
            factor = 1.0 + (self.wb_saturation / 100.0)
            enhancer = ImageEnhance.Color(pil_img)
            pil_img = enhancer.enhance(factor)

        # Convert back to numpy for temperature and tint
        result = np.array(pil_img)

        # Apply temperature (shift blue-yellow)
        if self.wb_temperature != 0:
            temp_shift = self.wb_temperature / 100.0 * 30
            result[:, :, 0] = np.clip(result[:, :, 0] + temp_shift, 0, 255)  # R
            result[:, :, 2] = np.clip(result[:, :, 2] - temp_shift, 0, 255)  # B

        # Apply tint (shift green-magenta)
        if self.wb_tint != 0:
            tint_shift = self.wb_tint / 100.0 * 30
            result[:, :, 1] = np.clip(result[:, :, 1] + tint_shift, 0, 255)  # G

        # Convert back to BGR
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        return result

    def _on_wb_change(self, value=None):
        """Handle white balance slider change"""
        if hasattr(self, 'temp_slider'):
            self.wb_temperature = self.temp_slider.get()
            self.temp_label.configure(text=f"{self.wb_temperature:.0f}")

        if hasattr(self, 'tint_slider'):
            self.wb_tint = self.tint_slider.get()
            self.tint_label.configure(text=f"{self.wb_tint:.0f}")

        if hasattr(self, 'bright_slider'):
            self.wb_brightness = self.bright_slider.get()
            self.bright_label.configure(text=f"{self.wb_brightness:.0f}")

        if hasattr(self, 'contrast_slider'):
            self.wb_contrast = self.contrast_slider.get()
            self.contrast_label.configure(text=f"{self.wb_contrast:.0f}")

        if hasattr(self, 'sat_slider'):
            self.wb_saturation = self.sat_slider.get()
            self.sat_label.configure(text=f"{self.wb_saturation:.0f}")

        self._update_canvas_preview()

    def _reset_white_balance(self):
        """Reset white balance to defaults"""
        self.wb_temperature = 0.0
        self.wb_tint = 0.0
        self.wb_brightness = 0.0
        self.wb_contrast = 0.0
        self.wb_saturation = 0.0

        if hasattr(self, 'temp_slider'):
            self.temp_slider.set(0)
            self.tint_slider.set(0)
            self.bright_slider.set(0)
            self.contrast_slider.set(0)
            self.sat_slider.set(0)

        self._update_canvas_preview()

    def _reset_edits(self):
        """Reset all edits"""
        height, width = self.original_photo.shape[:2]
        margin = 20
        self.corner_points = [
            (margin, margin),
            (width - margin, margin),
            (width - margin, height - margin),
            (margin, height - margin)
        ]
        self.crop_box = (0, 0, width, height)
        self._reset_white_balance()
        self._apply_current_edits()
        self._update_canvas_preview()
        self.app._show_info("All edits reset")

    def _save_changes(self):
        """Save all changes to artwork"""
        if not self.selected_artwork:
            return

        # Update name
        self.selected_artwork.name = self.name_entry.get()

        # Update dimensions
        try:
            width = float(self.width_entry.get())
            height = float(self.height_entry.get())
            if width > 0 and height > 0:
                self.selected_artwork.update_dimensions_from_cm(width, height)
            else:
                self.app._show_error("Dimensions must be positive")
                return
        except ValueError:
            self.app._show_error("Invalid dimensions - please enter numbers")
            return

        # Save editing state
        self.selected_artwork.corner_points = self.corner_points.copy()
        self.selected_artwork.crop_box = self.crop_box
        self.selected_artwork.white_balance_adjustments = {
            'temperature': self.wb_temperature,
            'tint': self.wb_tint,
            'brightness': self.wb_brightness,
            'contrast': self.wb_contrast,
            'saturation': self.wb_saturation
        }

        # Apply final edits and update artwork image
        self._apply_current_edits()
        final_image = self._apply_white_balance(self.edited_photo)
        self.app.artwork_images[self.selected_artwork.art_id] = final_image

        # Update thumbnail
        self._create_thumbnail(self.selected_artwork.art_id, final_image)

        # Refresh list
        self._refresh_artwork_list()

        self.app._show_info(f"Changes saved for '{self.selected_artwork.name}'")

    def _delete_artwork(self, artwork: Artwork):
        """Delete an artwork"""
        from tkinter import messagebox

        if messagebox.askyesno("Confirm Delete", f"Delete '{artwork.name}'?"):
            # Remove from app
            self.app.artworks.remove(artwork)
            if artwork.art_id in self.app.artwork_images:
                del self.app.artwork_images[artwork.art_id]
            if artwork.art_id in self.thumbnail_images:
                del self.thumbnail_images[artwork.art_id]

            # Refresh and show welcome
            self._refresh_artwork_list()

            # Clear info panel
            for widget in self.info_panel.winfo_children():
                widget.destroy()

            welcome = ctk.CTkLabel(
                self.info_panel,
                text="Select an artwork to edit",
                font=("Arial", 14),
                text_color="gray"
            )
            welcome.pack(expand=True)

            self.app._show_info(f"'{artwork.name}' deleted")

    def _continue_to_framing(self):
        """Continue to framing studio"""
        if len(self.app.artworks) == 0:
            self.app._show_error("Please import at least one artwork before continuing")
            return

        self.app.show_framing_studio_screen()
