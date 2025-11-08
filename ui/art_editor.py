"""
Art Editor Screen - Enhanced with Image Previews
"""
import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk
import os
import cv2
import numpy as np
from models.artwork import Artwork
from processors.image_processor import ImageProcessor
from utils.file_manager import FileManager
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

        # Center/right (preview and editing area)
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
        """Edit artwork dimensions and properties"""
        self.selected_artwork = artwork

        # Clear info panel
        for widget in self.info_panel.winfo_children():
            widget.destroy()

        # Main container
        edit_frame = ctk.CTkFrame(self.info_panel)
        edit_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            edit_frame,
            text=f"Edit Artwork",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(10, 5))

        # Image preview
        preview_frame = ctk.CTkFrame(edit_frame, fg_color="#1a1a1a")
        preview_frame.pack(pady=15, padx=20, fill="both", expand=True)

        # Load and display image preview
        if artwork.art_id in self.app.artwork_images:
            self._show_preview(preview_frame, self.app.artwork_images[artwork.art_id])

        # Controls frame
        controls_frame = ctk.CTkFrame(edit_frame)
        controls_frame.pack(fill="x", padx=20, pady=10)

        # Name
        name_label = ctk.CTkLabel(controls_frame, text="Name:", font=("Arial", 11, "bold"))
        name_label.pack(pady=(10, 5))

        name_entry = ctk.CTkEntry(controls_frame, width=400, height=35)
        name_entry.insert(0, artwork.name)
        name_entry.pack(pady=5)

        # Dimensions
        dim_label = ctk.CTkLabel(controls_frame, text="Real-World Dimensions:", font=("Arial", 11, "bold"))
        dim_label.pack(pady=(15, 5))

        dim_inputs_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        dim_inputs_frame.pack(pady=5)

        # Width (cm)
        width_frame = ctk.CTkFrame(dim_inputs_frame, fg_color="transparent")
        width_frame.pack(side="left", padx=10)

        ctk.CTkLabel(width_frame, text="Width (cm):", font=("Arial", 10)).pack()
        width_cm_entry = ctk.CTkEntry(width_frame, width=120)
        width_cm_entry.insert(0, f"{artwork.real_width_cm:.1f}")
        width_cm_entry.pack(pady=2)

        # Height (cm)
        height_frame = ctk.CTkFrame(dim_inputs_frame, fg_color="transparent")
        height_frame.pack(side="left", padx=10)

        ctk.CTkLabel(height_frame, text="Height (cm):", font=("Arial", 10)).pack()
        height_cm_entry = ctk.CTkEntry(height_frame, width=120)
        height_cm_entry.insert(0, f"{artwork.real_height_cm:.1f}")
        height_cm_entry.pack(pady=2)

        # Info about inches
        inch_info = ctk.CTkLabel(
            controls_frame,
            text=f"({artwork.real_width_inches:.1f}\" × {artwork.real_height_inches:.1f}\")",
            font=("Arial", 9),
            text_color="gray"
        )
        inch_info.pack(pady=5)

        # Save button
        def save_changes():
            artwork.name = name_entry.get()
            try:
                width = float(width_cm_entry.get())
                height = float(height_cm_entry.get())
                if width > 0 and height > 0:
                    artwork.update_dimensions_from_cm(width, height)
                    self._refresh_artwork_list()
                    self.app._show_info(f"Changes saved for '{artwork.name}'")
                else:
                    self.app._show_error("Dimensions must be positive")
            except ValueError:
                self.app._show_error("Invalid dimensions - please enter numbers")

        btn_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            command=save_changes,
            width=150,
            height=40,
            fg_color="#4CAF50",
            font=("Arial", 12, "bold")
        )
        btn_save.pack(side="left", padx=5)

        btn_delete = ctk.CTkButton(
            btn_frame,
            text="🗑️ Delete",
            command=lambda: self._delete_artwork(artwork),
            width=100,
            height=40,
            fg_color="#F44336"
        )
        btn_delete.pack(side="left", padx=5)

    def _show_preview(self, parent, image_array: np.ndarray):
        """Show image preview in the panel"""
        try:
            # Convert to PIL
            img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            # Calculate size to fit in preview (max 500px)
            max_size = 500
            img_width, img_height = pil_img.size

            if img_width > max_size or img_height > max_size:
                if img_width > img_height:
                    new_width = max_size
                    new_height = int(img_height * (max_size / img_width))
                else:
                    new_height = max_size
                    new_width = int(img_width * (max_size / img_height))

                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.preview_image = ImageTk.PhotoImage(pil_img)

            # Display in label
            preview_label = ctk.CTkLabel(
                parent,
                image=self.preview_image,
                text=""
            )
            preview_label.pack(expand=True, pady=20)

            # Image info
            info_label = ctk.CTkLabel(
                parent,
                text=f"Original size: {img_width} × {img_height} pixels",
                font=("Arial", 9),
                text_color="gray"
            )
            info_label.pack(pady=(0, 10))

        except Exception as e:
            print(f"Error showing preview: {e}")
            error_label = ctk.CTkLabel(
                parent,
                text="Error loading preview",
                text_color="red"
            )
            error_label.pack(expand=True)

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
