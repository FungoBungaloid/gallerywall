"""
Wall Setup Screen - With Photo Import and Perspective Correction
"""
import customtkinter as ctk
from tkinter import colorchooser, filedialog, Canvas
from PIL import Image, ImageTk
import numpy as np
import cv2
from models.wall import Wall
from utils.file_manager import FileManager
from utils.perspective import apply_perspective_correction
from processors.image_processor import ImageProcessor
import config


class WallSetupScreen:
    """Screen for setting up the wall (template or photo)"""

    def __init__(self, app, parent):
        """
        Initialize wall setup screen

        Args:
            app: Main application instance
            parent: Parent widget
        """
        self.app = app
        self.parent = parent

        # State
        self.wall_type = "template"  # "template" or "photo"
        self.wall_color = "#FFFFFF"
        self.wall_width_cm = 200.0
        self.wall_height_cm = 150.0

        # Photo mode state
        self.original_photo = None  # Original wall photo (numpy array)
        self.corrected_photo = None  # Perspective-corrected photo
        self.photo_path = None
        self.corner_points = []  # List of (x, y) tuples for 4 corners
        self.dragging_point = None
        self.photo_tk = None  # PhotoImage for display
        self.preview_scale = 1.0  # Scale factor for display

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI"""
        # Main layout: left panel for controls, right panel for preview
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Left panel (controls)
        left_panel = ctk.CTkFrame(main_frame, width=320)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        left_panel.pack_propagate(False)

        # Right panel (preview)
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Left panel contents
        self._setup_controls(left_panel)

        # Right panel contents
        self._setup_preview(right_panel)

    def _setup_controls(self, parent):
        """Set up control panel"""
        # Title
        title = ctk.CTkLabel(parent, text="Wall Setup", font=("Arial", 18, "bold"))
        title.pack(pady=(10, 20))

        # Wall type selection
        type_label = ctk.CTkLabel(parent, text="Wall Type:", font=("Arial", 12, "bold"))
        type_label.pack(pady=(10, 5))

        self.type_var = ctk.StringVar(value="template")
        type_template = ctk.CTkRadioButton(
            parent,
            text="Color Template",
            variable=self.type_var,
            value="template",
            command=self._on_type_changed
        )
        type_template.pack(pady=5, padx=10, anchor="w")

        type_photo = ctk.CTkRadioButton(
            parent,
            text="Wall Photo",
            variable=self.type_var,
            value="photo",
            command=self._on_type_changed
        )
        type_photo.pack(pady=5, padx=10, anchor="w")

        # Template mode controls
        self.template_controls = ctk.CTkFrame(parent)
        self.template_controls.pack(pady=(15, 10), fill="x", padx=10)

        color_label = ctk.CTkLabel(self.template_controls, text="Wall Color:", font=("Arial", 11))
        color_label.pack(pady=5)

        self.color_button = ctk.CTkButton(
            self.template_controls,
            text="Choose Color",
            command=self._choose_color,
            fg_color=self.wall_color,
            width=200
        )
        self.color_button.pack(pady=5)

        # Photo mode controls
        self.photo_controls = ctk.CTkFrame(parent)

        photo_label = ctk.CTkLabel(
            self.photo_controls,
            text="Upload a photo of your wall",
            font=("Arial", 11),
            wraplength=260
        )
        photo_label.pack(pady=5)

        btn_load_photo = ctk.CTkButton(
            self.photo_controls,
            text="📁 Load Wall Photo",
            command=self._load_wall_photo,
            height=35,
            width=200
        )
        btn_load_photo.pack(pady=10)

        self.photo_status = ctk.CTkLabel(
            self.photo_controls,
            text="No photo loaded",
            font=("Arial", 9),
            text_color="gray"
        )
        self.photo_status.pack(pady=5)

        # Instructions for photo mode
        instructions = ctk.CTkLabel(
            self.photo_controls,
            text="After loading:\n1. Drag the 4 corner markers\n2. Position them at wall corners\n3. Click 'Apply Correction'",
            font=("Arial", 9),
            text_color="gray",
            justify="left",
            wraplength=260
        )
        instructions.pack(pady=10)

        self.btn_apply_correction = ctk.CTkButton(
            self.photo_controls,
            text="Apply Correction",
            command=self._apply_perspective_correction,
            state="disabled",
            fg_color="#4CAF50"
        )
        self.btn_apply_correction.pack(pady=10)

        # Dimensions (common for both modes)
        dim_label = ctk.CTkLabel(parent, text="Wall Dimensions:", font=("Arial", 12, "bold"))
        dim_label.pack(pady=(20, 10))

        # Width
        dim_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dim_frame.pack(fill="x", padx=10)

        ctk.CTkLabel(dim_frame, text="Width:", font=("Arial", 10)).pack(anchor="w")
        width_inputs = ctk.CTkFrame(dim_frame, fg_color="transparent")
        width_inputs.pack(fill="x", pady=2)

        self.width_cm_entry = ctk.CTkEntry(width_inputs, width=90)
        self.width_cm_entry.insert(0, str(self.wall_width_cm))
        self.width_cm_entry.bind('<KeyRelease>', self._on_width_cm_changed)
        self.width_cm_entry.pack(side="left", padx=(0, 2))

        ctk.CTkLabel(width_inputs, text="cm /", font=("Arial", 9)).pack(side="left", padx=2)

        self.width_in_entry = ctk.CTkEntry(width_inputs, width=90)
        self.width_in_entry.insert(0, f"{self.wall_width_cm / 2.54:.1f}")
        self.width_in_entry.bind('<KeyRelease>', self._on_width_in_changed)
        self.width_in_entry.pack(side="left", padx=2)

        ctk.CTkLabel(width_inputs, text="in", font=("Arial", 9)).pack(side="left")

        # Height
        ctk.CTkLabel(dim_frame, text="Height:", font=("Arial", 10)).pack(anchor="w", pady=(10, 0))
        height_inputs = ctk.CTkFrame(dim_frame, fg_color="transparent")
        height_inputs.pack(fill="x", pady=2)

        self.height_cm_entry = ctk.CTkEntry(height_inputs, width=90)
        self.height_cm_entry.insert(0, str(self.wall_height_cm))
        self.height_cm_entry.bind('<KeyRelease>', self._on_height_cm_changed)
        self.height_cm_entry.pack(side="left", padx=(0, 2))

        ctk.CTkLabel(height_inputs, text="cm /", font=("Arial", 9)).pack(side="left", padx=2)

        self.height_in_entry = ctk.CTkEntry(height_inputs, width=90)
        self.height_in_entry.insert(0, f"{self.wall_height_cm / 2.54:.1f}")
        self.height_in_entry.bind('<KeyRelease>', self._on_height_in_changed)
        self.height_in_entry.pack(side="left", padx=2)

        ctk.CTkLabel(height_inputs, text="in", font=("Arial", 9)).pack(side="left")

        # Bottom buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        btn_cancel = ctk.CTkButton(btn_frame, text="← Back", command=self.app.show_welcome_screen, width=100)
        btn_cancel.pack(side="left", padx=2, pady=5)

        btn_save = ctk.CTkButton(
            btn_frame,
            text="Continue →",
            command=self._save_and_continue,
            fg_color="#4CAF50",
            width=100
        )
        btn_save.pack(side="right", padx=2, pady=5)

        # Show initial mode controls
        self._on_type_changed()

    def _setup_preview(self, parent):
        """Set up preview panel"""
        preview_label = ctk.CTkLabel(parent, text="Preview", font=("Arial", 16, "bold"))
        preview_label.pack(pady=10)

        # Preview canvas (using tkinter Canvas for image and corner points)
        self.preview_canvas = Canvas(
            parent,
            bg=self.wall_color,
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # Bind mouse events for dragging corner points
        self.preview_canvas.bind("<Button-1>", self._on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        self._update_preview()

    def _on_type_changed(self):
        """Handle wall type change"""
        self.wall_type = self.type_var.get()

        # Show/hide appropriate controls
        if self.wall_type == "template":
            self.template_controls.pack(pady=(15, 10), fill="x", padx=10)
            self.photo_controls.pack_forget()
        else:  # photo
            self.template_controls.pack_forget()
            self.photo_controls.pack(pady=(15, 10), fill="x", padx=10)

        self._update_preview()

    def _choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose Wall Color", initialcolor=self.wall_color)
        if color[1]:
            self.wall_color = color[1]
            self.color_button.configure(fg_color=self.wall_color)
            self._update_preview()

    def _load_wall_photo(self):
        """Load wall photo from file"""
        file_path = filedialog.askopenfilename(
            title="Select Wall Photo",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG Images", "*.jpg *.jpeg"),
                ("PNG Images", "*.png"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Load image
            self.original_photo = ImageProcessor.load_image(file_path)
            if self.original_photo is None:
                self.app._show_error("Failed to load image")
                return

            self.photo_path = file_path
            self.corrected_photo = None  # Reset correction

            # Initialize default corner points (10% margin)
            height, width = self.original_photo.shape[:2]
            margin_x = int(width * 0.1)
            margin_y = int(height * 0.1)

            self.corner_points = [
                (margin_x, margin_y),  # Top-left
                (width - margin_x, margin_y),  # Top-right
                (width - margin_x, height - margin_y),  # Bottom-right
                (margin_x, height - margin_y)  # Bottom-left
            ]

            self.photo_status.configure(text="Photo loaded - adjust corners", text_color="green")
            self.btn_apply_correction.configure(state="normal")

            self._update_preview()

        except Exception as e:
            self.app._show_error(f"Error loading photo: {e}")
            print(f"Error loading wall photo: {e}")

    def _apply_perspective_correction(self):
        """Apply perspective correction to wall photo"""
        if self.original_photo is None or len(self.corner_points) != 4:
            return

        try:
            # Apply correction
            self.corrected_photo = apply_perspective_correction(
                self.original_photo,
                self.corner_points,
                int(self.wall_width_cm * 10),  # Target width in pixels
                int(self.wall_height_cm * 10)  # Target height in pixels
            )

            if self.corrected_photo is not None:
                self.photo_status.configure(
                    text="✓ Perspective corrected!",
                    text_color="green"
                )
                self.app._show_info("Perspective correction applied successfully!")
                self._update_preview()
            else:
                self.app._show_error("Perspective correction failed")

        except Exception as e:
            self.app._show_error(f"Error applying correction: {e}")
            print(f"Error in perspective correction: {e}")

    def _on_canvas_click(self, event):
        """Handle canvas click for dragging corner points"""
        if self.wall_type != "photo" or not self.corner_points:
            return

        # Find nearest corner point
        min_dist = float('inf')
        nearest_idx = None

        for idx, (px, py) in enumerate(self.corner_points):
            # Convert to canvas coordinates
            cx, cy = self._image_to_canvas_coords(px, py)
            dist = ((event.x - cx) ** 2 + (event.y - cy) ** 2) ** 0.5

            if dist < 20 and dist < min_dist:  # 20px radius
                min_dist = dist
                nearest_idx = idx

        if nearest_idx is not None:
            self.dragging_point = nearest_idx

    def _on_canvas_drag(self, event):
        """Handle dragging of corner points"""
        if self.dragging_point is not None and self.original_photo is not None:
            # Convert canvas to image coordinates
            img_x, img_y = self._canvas_to_image_coords(event.x, event.y)

            # Clamp to image bounds
            height, width = self.original_photo.shape[:2]
            img_x = max(0, min(width - 1, img_x))
            img_y = max(0, min(height - 1, img_y))

            self.corner_points[self.dragging_point] = (img_x, img_y)
            self._update_preview()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        self.dragging_point = None

    def _image_to_canvas_coords(self, img_x: int, img_y: int) -> tuple:
        """Convert image coordinates to canvas coordinates"""
        if self.original_photo is None:
            return (img_x, img_y)

        # Get canvas size
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width <= 1:
            return (img_x, img_y)

        # Get image size
        img_height, img_width = self.original_photo.shape[:2]

        # Calculate scale to fit image in canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y) * 0.9  # 90% to add margin

        # Calculate offset to center image
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2

        # Transform coordinates
        canvas_x = int(img_x * scale) + offset_x
        canvas_y = int(img_y * scale) + offset_y

        return (canvas_x, canvas_y)

    def _canvas_to_image_coords(self, canvas_x: int, canvas_y: int) -> tuple:
        """Convert canvas coordinates to image coordinates"""
        if self.original_photo is None:
            return (canvas_x, canvas_y)

        # Get canvas size
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        # Get image size
        img_height, img_width = self.original_photo.shape[:2]

        # Calculate scale
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y) * 0.9

        # Calculate offset
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2

        # Transform back to image coordinates
        img_x = int((canvas_x - offset_x) / scale)
        img_y = int((canvas_y - offset_y) / scale)

        return (img_x, img_y)

    def _on_width_cm_changed(self, event=None):
        """Handle width (cm) change"""
        try:
            value = float(self.width_cm_entry.get())
            if value > 0:
                self.wall_width_cm = value
                self.width_in_entry.delete(0, 'end')
                self.width_in_entry.insert(0, f"{value / 2.54:.1f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_width_in_changed(self, event=None):
        """Handle width (inches) change"""
        try:
            value = float(self.width_in_entry.get())
            if value > 0:
                self.wall_width_cm = value * 2.54
                self.width_cm_entry.delete(0, 'end')
                self.width_cm_entry.insert(0, f"{self.wall_width_cm:.1f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_height_cm_changed(self, event=None):
        """Handle height (cm) change"""
        try:
            value = float(self.height_cm_entry.get())
            if value > 0:
                self.wall_height_cm = value
                self.height_in_entry.delete(0, 'end')
                self.height_in_entry.insert(0, f"{value / 2.54:.1f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_height_in_changed(self, event=None):
        """Handle height (inches) change"""
        try:
            value = float(self.height_in_entry.get())
            if value > 0:
                self.wall_height_cm = value * 2.54
                self.height_cm_entry.delete(0, 'end')
                self.height_cm_entry.insert(0, f"{self.wall_height_cm:.1f}")
                self._update_preview()
        except ValueError:
            pass

    def _update_preview(self):
        """Update preview canvas"""
        self.preview_canvas.delete("all")

        if self.wall_type == "template":
            # Simple color preview
            self.preview_canvas.configure(bg=self.wall_color)
        else:  # photo
            if self.corrected_photo is not None:
                # Show corrected photo
                self._display_image(self.corrected_photo, show_corners=False)
            elif self.original_photo is not None:
                # Show original with corner points
                self._display_image(self.original_photo, show_corners=True)
            else:
                self.preview_canvas.configure(bg="#2B2B2B")

    def _display_image(self, image: np.ndarray, show_corners: bool = False):
        """Display image in preview canvas"""
        try:
            # Convert to PIL
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            # Get canvas size
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width <= 1:
                return

            # Calculate scale to fit
            img_width, img_height = pil_img.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y) * 0.9  # 90% for margins

            display_width = int(img_width * scale)
            display_height = int(img_height * scale)

            # Resize image
            pil_img = pil_img.resize((display_width, display_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.photo_tk = ImageTk.PhotoImage(pil_img)

            # Center image in canvas
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2

            self.preview_canvas.create_image(offset_x, offset_y, image=self.photo_tk, anchor="nw")

            # Draw corner points if in correction mode
            if show_corners and self.corner_points:
                colors = ["#FF5722", "#4CAF50", "#2196F3", "#FFC107"]  # TL, TR, BR, BL
                labels = ["TL", "TR", "BR", "BL"]

                for idx, (img_x, img_y) in enumerate(self.corner_points):
                    cx, cy = self._image_to_canvas_coords(img_x, img_y)

                    # Draw circle
                    r = 8
                    self.preview_canvas.create_oval(
                        cx - r, cy - r, cx + r, cy + r,
                        fill=colors[idx],
                        outline="white",
                        width=2,
                        tags="corner"
                    )

                    # Draw label
                    self.preview_canvas.create_text(
                        cx, cy - 15,
                        text=labels[idx],
                        fill="white",
                        font=("Arial", 10, "bold"),
                        tags="corner"
                    )

                # Draw connecting lines
                for i in range(4):
                    p1 = self._image_to_canvas_coords(*self.corner_points[i])
                    p2 = self._image_to_canvas_coords(*self.corner_points[(i + 1) % 4])
                    self.preview_canvas.create_line(
                        p1[0], p1[1], p2[0], p2[1],
                        fill="#FFC107",
                        width=2,
                        dash=(5, 3),
                        tags="corner"
                    )

        except Exception as e:
            print(f"Error displaying image: {e}")

    def _save_and_continue(self):
        """Save wall configuration and continue to next screen"""
        # Validate photo mode
        if self.wall_type == "photo":
            if self.original_photo is None:
                self.app._show_error("Please load a wall photo first")
                return
            if self.corrected_photo is None:
                if not self.app._show_confirm(
                    "Perspective correction has not been applied.\n\n"
                    "Continue anyway? (The photo may appear distorted)"
                ):
                    return

        # Create wall model
        wall_id = FileManager.generate_id()

        if self.wall_type == "photo":
            # Use corrected photo if available, otherwise original
            final_photo = self.corrected_photo if self.corrected_photo is not None else self.original_photo

            self.app.current_wall = Wall(
                wall_id=wall_id,
                type="photo",
                original_image_path=self.photo_path,
                corrected_image=final_photo,
                corner_points=self.corner_points,
                color="#FFFFFF",  # Not used for photos
                real_width_cm=self.wall_width_cm,
                real_height_cm=self.wall_height_cm,
                real_width_inches=self.wall_width_cm / 2.54,
                real_height_inches=self.wall_height_cm / 2.54
            )
        else:
            self.app.current_wall = Wall(
                wall_id=wall_id,
                type="template",
                color=self.wall_color,
                real_width_cm=self.wall_width_cm,
                real_height_cm=self.wall_height_cm,
                real_width_inches=self.wall_width_cm / 2.54,
                real_height_inches=self.wall_height_cm / 2.54
            )

        # Proceed to art editor
        self.app.show_art_editor_screen()
