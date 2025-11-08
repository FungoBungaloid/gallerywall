"""
Wall Setup Screen
"""
import customtkinter as ctk
from tkinter import colorchooser
import numpy as np
from models.wall import Wall
from utils.file_manager import FileManager
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

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI"""
        # Main layout: left panel for controls, right panel for preview
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Left panel (controls)
        left_panel = ctk.CTkFrame(main_frame, width=config.PANEL_WIDTH)
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
        type_label = ctk.CTkLabel(parent, text="Wall Type:", font=("Arial", 12))
        type_label.pack(pady=(10, 5))

        self.type_var = ctk.StringVar(value="template")
        type_template = ctk.CTkRadioButton(
            parent,
            text="Color Template",
            variable=self.type_var,
            value="template",
            command=self._on_type_changed
        )
        type_template.pack(pady=5)

        type_photo = ctk.CTkRadioButton(
            parent,
            text="Photo (Coming Soon)",
            variable=self.type_var,
            value="photo",
            command=self._on_type_changed,
            state="disabled"
        )
        type_photo.pack(pady=5)

        # Color picker (for template mode)
        color_frame = ctk.CTkFrame(parent)
        color_frame.pack(pady=(20, 10), fill="x")

        color_label = ctk.CTkLabel(color_frame, text="Wall Color:", font=("Arial", 12))
        color_label.pack(pady=5)

        self.color_button = ctk.CTkButton(
            color_frame,
            text="Choose Color",
            command=self._choose_color,
            fg_color=self.wall_color
        )
        self.color_button.pack(pady=5)

        # Dimensions
        dim_label = ctk.CTkLabel(parent, text="Dimensions:", font=("Arial", 12, "bold"))
        dim_label.pack(pady=(20, 10))

        # Width (cm)
        width_cm_label = ctk.CTkLabel(parent, text="Width (cm):", font=("Arial", 11))
        width_cm_label.pack(pady=(5, 2))

        self.width_cm_entry = ctk.CTkEntry(parent)
        self.width_cm_entry.insert(0, str(self.wall_width_cm))
        self.width_cm_entry.bind('<FocusOut>', self._on_width_cm_changed)
        self.width_cm_entry.pack(pady=(0, 5))

        # Width (inches)
        width_in_label = ctk.CTkLabel(parent, text="Width (inches):", font=("Arial", 11))
        width_in_label.pack(pady=(5, 2))

        self.width_in_entry = ctk.CTkEntry(parent)
        self.width_in_entry.insert(0, f"{self.wall_width_cm / 2.54:.2f}")
        self.width_in_entry.bind('<FocusOut>', self._on_width_in_changed)
        self.width_in_entry.pack(pady=(0, 15))

        # Height (cm)
        height_cm_label = ctk.CTkLabel(parent, text="Height (cm):", font=("Arial", 11))
        height_cm_label.pack(pady=(5, 2))

        self.height_cm_entry = ctk.CTkEntry(parent)
        self.height_cm_entry.insert(0, str(self.wall_height_cm))
        self.height_cm_entry.bind('<FocusOut>', self._on_height_cm_changed)
        self.height_cm_entry.pack(pady=(0, 5))

        # Height (inches)
        height_in_label = ctk.CTkLabel(parent, text="Height (inches):", font=("Arial", 11))
        height_in_label.pack(pady=(5, 2))

        self.height_in_entry = ctk.CTkEntry(parent)
        self.height_in_entry.insert(0, f"{self.wall_height_cm / 2.54:.2f}")
        self.height_in_entry.bind('<FocusOut>', self._on_height_in_changed)
        self.height_in_entry.pack(pady=(0, 15))

        # Bottom buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="bottom", fill="x", pady=10)

        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", command=self.app.show_welcome_screen)
        btn_cancel.pack(side="left", padx=5, pady=5)

        btn_save = ctk.CTkButton(btn_frame, text="Save & Continue", command=self._save_and_continue)
        btn_save.pack(side="right", padx=5, pady=5)

    def _setup_preview(self, parent):
        """Set up preview panel"""
        preview_label = ctk.CTkLabel(parent, text="Preview", font=("Arial", 16, "bold"))
        preview_label.pack(pady=10)

        # Preview canvas
        self.preview_canvas = ctk.CTkCanvas(parent, bg=self.wall_color)
        self.preview_canvas.pack(fill="both", expand=True, padx=20, pady=20)

        self._update_preview()

    def _on_type_changed(self):
        """Handle wall type change"""
        self.wall_type = self.type_var.get()
        self._update_preview()

    def _choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose Wall Color", initialcolor=self.wall_color)
        if color[1]:
            self.wall_color = color[1]
            self.color_button.configure(fg_color=self.wall_color)
            self._update_preview()

    def _on_width_cm_changed(self, event=None):
        """Handle width (cm) change"""
        try:
            value = float(self.width_cm_entry.get())
            if value > 0:
                self.wall_width_cm = value
                # Update inches
                self.width_in_entry.delete(0, 'end')
                self.width_in_entry.insert(0, f"{value / 2.54:.2f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_width_in_changed(self, event=None):
        """Handle width (inches) change"""
        try:
            value = float(self.width_in_entry.get())
            if value > 0:
                self.wall_width_cm = value * 2.54
                # Update cm
                self.width_cm_entry.delete(0, 'end')
                self.width_cm_entry.insert(0, f"{self.wall_width_cm:.2f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_height_cm_changed(self, event=None):
        """Handle height (cm) change"""
        try:
            value = float(self.height_cm_entry.get())
            if value > 0:
                self.wall_height_cm = value
                # Update inches
                self.height_in_entry.delete(0, 'end')
                self.height_in_entry.insert(0, f"{value / 2.54:.2f}")
                self._update_preview()
        except ValueError:
            pass

    def _on_height_in_changed(self, event=None):
        """Handle height (inches) change"""
        try:
            value = float(self.height_in_entry.get())
            if value > 0:
                self.wall_height_cm = value * 2.54
                # Update cm
                self.height_cm_entry.delete(0, 'end')
                self.height_cm_entry.insert(0, f"{self.wall_height_cm:.2f}")
                self._update_preview()
        except ValueError:
            pass

    def _update_preview(self):
        """Update preview canvas"""
        self.preview_canvas.configure(bg=self.wall_color)

    def _save_and_continue(self):
        """Save wall configuration and continue to next screen"""
        # Create wall model
        wall_id = FileManager.generate_id()
        self.app.current_wall = Wall(
            wall_id=wall_id,
            type=self.wall_type,
            color=self.wall_color,
            real_width_cm=self.wall_width_cm,
            real_height_cm=self.wall_height_cm,
            real_width_inches=self.wall_width_cm / 2.54,
            real_height_inches=self.wall_height_cm / 2.54
        )

        # Proceed to art editor
        self.app.show_art_editor_screen()
