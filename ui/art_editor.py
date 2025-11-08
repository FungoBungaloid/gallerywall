"""
Art Editor Screen
"""
import customtkinter as ctk
from tkinter import filedialog
import os
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

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI"""
        # Main layout
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Left sidebar (artwork list)
        left_panel = ctk.CTkFrame(main_frame, width=250)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        left_panel.pack_propagate(False)

        # Center/right (info or editing area)
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self._setup_artwork_list(left_panel)
        self._setup_info_panel(right_panel)

    def _setup_artwork_list(self, parent):
        """Set up artwork list sidebar"""
        title = ctk.CTkLabel(parent, text="Artwork", font=("Arial", 16, "bold"))
        title.pack(pady=(10, 5))

        # Import button
        btn_import = ctk.CTkButton(parent, text="Import Artwork", command=self._import_artwork)
        btn_import.pack(pady=10, padx=10, fill="x")

        # Artwork list (scrollable)
        self.artwork_list_frame = ctk.CTkScrollableFrame(parent)
        self.artwork_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._refresh_artwork_list()

        # Bottom buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        btn_back = ctk.CTkButton(btn_frame, text="Back", command=self.app.show_wall_setup_screen)
        btn_back.pack(side="left", pady=5)

        btn_next = ctk.CTkButton(btn_frame, text="Continue", command=self._continue_to_framing)
        btn_next.pack(side="right", pady=5)

    def _setup_info_panel(self, parent):
        """Set up info/editing panel"""
        self.info_panel = parent

        # Welcome message
        welcome = ctk.CTkLabel(
            parent,
            text="Import artwork to get started",
            font=("Arial", 14)
        )
        welcome.pack(expand=True)

    def _import_artwork(self):
        """Import artwork files"""
        file_paths = filedialog.askopenfilenames(
            title="Select Artwork Images",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All Files", "*.*")
            ]
        )

        if file_paths:
            for file_path in file_paths:
                self._add_artwork(file_path)

            self._refresh_artwork_list()

    def _add_artwork(self, file_path: str):
        """Add artwork to collection"""
        # Load image
        image = ImageProcessor.load_image(file_path)
        if image is None:
            return

        # Create artwork model
        art_id = FileManager.generate_id()
        name = os.path.splitext(os.path.basename(file_path))[0]

        # Get image dimensions (estimate 20x25cm as default)
        artwork = Artwork(
            art_id=art_id,
            name=name,
            original_image_path=file_path,
            real_width_cm=20.0,
            real_height_cm=25.0,
            real_width_inches=20.0 / 2.54,
            real_height_inches=25.0 / 2.54
        )

        self.app.artworks.append(artwork)
        self.app.artwork_images[art_id] = image

    def _refresh_artwork_list(self):
        """Refresh the artwork list display"""
        # Clear existing items
        for widget in self.artwork_list_frame.winfo_children():
            widget.destroy()

        # Add artwork items
        for artwork in self.app.artworks:
            item_frame = ctk.CTkFrame(self.artwork_list_frame)
            item_frame.pack(fill="x", pady=2, padx=2)

            name_label = ctk.CTkLabel(item_frame, text=artwork.name, anchor="w")
            name_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

            edit_btn = ctk.CTkButton(
                item_frame,
                text="Edit",
                width=60,
                command=lambda a=artwork: self._edit_artwork(a)
            )
            edit_btn.pack(side="right", padx=5, pady=5)

    def _edit_artwork(self, artwork: Artwork):
        """Edit artwork dimensions and properties"""
        self.selected_artwork = artwork

        # Clear info panel
        for widget in self.info_panel.winfo_children():
            widget.destroy()

        # Title
        title = ctk.CTkLabel(
            self.info_panel,
            text=f"Edit: {artwork.name}",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=20)

        # Name
        name_label = ctk.CTkLabel(self.info_panel, text="Name:", font=("Arial", 12))
        name_label.pack(pady=(10, 5))

        name_entry = ctk.CTkEntry(self.info_panel, width=300)
        name_entry.insert(0, artwork.name)
        name_entry.pack(pady=5)

        # Dimensions
        dim_label = ctk.CTkLabel(self.info_panel, text="Dimensions:", font=("Arial", 12, "bold"))
        dim_label.pack(pady=(20, 10))

        # Width (cm)
        width_cm_label = ctk.CTkLabel(self.info_panel, text="Width (cm):")
        width_cm_label.pack(pady=5)

        width_cm_entry = ctk.CTkEntry(self.info_panel, width=200)
        width_cm_entry.insert(0, str(artwork.real_width_cm))
        width_cm_entry.pack(pady=5)

        # Height (cm)
        height_cm_label = ctk.CTkLabel(self.info_panel, text="Height (cm):")
        height_cm_label.pack(pady=5)

        height_cm_entry = ctk.CTkEntry(self.info_panel, width=200)
        height_cm_entry.insert(0, str(artwork.real_height_cm))
        height_cm_entry.pack(pady=5)

        # Save button
        def save_changes():
            artwork.name = name_entry.get()
            try:
                width = float(width_cm_entry.get())
                height = float(height_cm_entry.get())
                artwork.update_dimensions_from_cm(width, height)
            except ValueError:
                pass
            self._refresh_artwork_list()
            self._show_info_message("Changes saved!")

        btn_save = ctk.CTkButton(self.info_panel, text="Save Changes", command=save_changes)
        btn_save.pack(pady=20)

    def _show_info_message(self, message: str):
        """Show info message"""
        self.app._show_info(message)

    def _continue_to_framing(self):
        """Continue to framing studio"""
        if len(self.app.artworks) == 0:
            self.app._show_error("Please import at least one artwork before continuing")
            return

        self.app.show_framing_studio_screen()
