"""
Framing Studio Screen
"""
import customtkinter as ctk
from tkinter import colorchooser
from models.frame import FrameConfig, MatConfig
from processors.frame_renderer import FrameRenderer
from PIL import Image, ImageTk
import config


class FramingStudioScreen:
    """Screen for configuring frames and mats"""

    def __init__(self, app, parent):
        """
        Initialize framing studio screen

        Args:
            app: Main application instance
            parent: Parent widget
        """
        self.app = app
        self.parent = parent

        # State
        self.selected_artwork = None if len(app.artworks) == 0 else app.artworks[0]
        self.current_frame_config = None

        if self.selected_artwork:
            self._init_frame_config()

        self._setup_ui()

    def _init_frame_config(self):
        """Initialize frame configuration for selected artwork"""
        if self.selected_artwork.frame_config:
            self.current_frame_config = self.selected_artwork.frame_config
            # Load existing config into UI
            if hasattr(self, 'mat_enabled_var'):
                self.mat_enabled_var.set(self.current_frame_config.mat is not None)
                if self.current_frame_config.mat:
                    self.mat_width_entry.delete(0, 'end')
                    self.mat_width_entry.insert(0, str(self.current_frame_config.mat.top_width_cm))
                    self.mat_color = self.current_frame_config.mat.color
                    self.mat_color_btn.configure(fg_color=self.mat_color)

                self.frame_width_entry.delete(0, 'end')
                self.frame_width_entry.insert(0, str(self.current_frame_config.frame_width_cm))
                self.frame_color = self.current_frame_config.frame_color
                self.frame_color_btn.configure(fg_color=self.frame_color)

                self.frame_shadow_var.set(self.current_frame_config.frame_shadow_enabled)
                self.mat_shadow_var.set(self.current_frame_config.mat_shadow_enabled)
        else:
            # Create default frame config
            self.current_frame_config = FrameConfig(
                mat=None,
                frame_width_cm=2.0,
                frame_color="#000000"
            )

    def _setup_ui(self):
        """Set up the UI"""
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True)

        # Left panel (artwork list)
        left_panel = ctk.CTkFrame(main_frame, width=200)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        left_panel.pack_propagate(False)

        # Center panel (preview)
        center_panel = ctk.CTkFrame(main_frame)
        center_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Right panel (controls)
        right_panel = ctk.CTkFrame(main_frame, width=300)
        right_panel.pack(side="right", fill="y", padx=10, pady=10)
        right_panel.pack_propagate(False)

        self._setup_artwork_list(left_panel)
        self._setup_preview(center_panel)
        self._setup_controls(right_panel)

    def _setup_artwork_list(self, parent):
        """Set up artwork list"""
        title = ctk.CTkLabel(parent, text="Artwork", font=("Arial", 14, "bold"))
        title.pack(pady=10)

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(parent)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._refresh_artwork_list()

        # Bottom buttons
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="bottom", fill="x", pady=10, padx=5)

        btn_back = ctk.CTkButton(btn_frame, text="Back", command=self.app.show_art_editor_screen)
        btn_back.pack(side="left", pady=5)

        btn_next = ctk.CTkButton(btn_frame, text="Continue", command=self._continue_to_workspace)
        btn_next.pack(side="right", pady=5)

    def _setup_preview(self, parent):
        """Set up preview area"""
        title = ctk.CTkLabel(parent, text="Preview", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        # Preview canvas
        self.preview_label = ctk.CTkLabel(parent, text="")
        self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)

        self._update_preview()

    def _setup_controls(self, parent):
        """Set up framing controls"""
        title = ctk.CTkLabel(parent, text="Frame Settings", font=("Arial", 14, "bold"))
        title.pack(pady=10)

        # Scrollable frame for controls
        controls_frame = ctk.CTkScrollableFrame(parent)
        controls_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Mat section
        mat_label = ctk.CTkLabel(controls_frame, text="Mat", font=("Arial", 12, "bold"))
        mat_label.pack(pady=(10, 5))

        self.mat_enabled_var = ctk.BooleanVar(value=False)
        mat_check = ctk.CTkCheckBox(
            controls_frame,
            text="Enable Mat",
            variable=self.mat_enabled_var,
            command=self._on_mat_enabled_changed
        )
        mat_check.pack(pady=5)

        # Mat width
        mat_width_label = ctk.CTkLabel(controls_frame, text="Mat Width (cm):")
        mat_width_label.pack(pady=5)

        self.mat_width_entry = ctk.CTkEntry(controls_frame, width=150)
        self.mat_width_entry.insert(0, "3.0")
        self.mat_width_entry.bind('<KeyRelease>', lambda e: self._update_preview())
        self.mat_width_entry.pack(pady=5)

        # Mat color
        self.mat_color = "#FFFFFF"
        self.mat_color_btn = ctk.CTkButton(
            controls_frame,
            text="Mat Color",
            command=self._choose_mat_color,
            fg_color=self.mat_color
        )
        self.mat_color_btn.pack(pady=5)

        # Frame section
        frame_label = ctk.CTkLabel(controls_frame, text="Frame", font=("Arial", 12, "bold"))
        frame_label.pack(pady=(20, 5))

        # Frame width
        frame_width_label = ctk.CTkLabel(controls_frame, text="Frame Width (cm):")
        frame_width_label.pack(pady=5)

        self.frame_width_entry = ctk.CTkEntry(controls_frame, width=150)
        self.frame_width_entry.insert(0, "2.0")
        self.frame_width_entry.bind('<KeyRelease>', lambda e: self._update_preview())
        self.frame_width_entry.pack(pady=5)

        # Frame color
        self.frame_color = "#000000"
        self.frame_color_btn = ctk.CTkButton(
            controls_frame,
            text="Frame Color",
            command=self._choose_frame_color,
            fg_color=self.frame_color
        )
        self.frame_color_btn.pack(pady=5)

        # Shadow toggles
        shadow_label = ctk.CTkLabel(controls_frame, text="Shadows", font=("Arial", 12, "bold"))
        shadow_label.pack(pady=(20, 5))

        self.frame_shadow_var = ctk.BooleanVar(value=True)
        frame_shadow_check = ctk.CTkCheckBox(
            controls_frame,
            text="Frame Shadow",
            variable=self.frame_shadow_var,
            command=self._update_preview
        )
        frame_shadow_check.pack(pady=5)

        self.mat_shadow_var = ctk.BooleanVar(value=True)
        mat_shadow_check = ctk.CTkCheckBox(
            controls_frame,
            text="Mat Shadow",
            variable=self.mat_shadow_var,
            command=self._update_preview
        )
        mat_shadow_check.pack(pady=5)

        # Apply and preview buttons
        btn_frame = ctk.CTkFrame(controls_frame)
        btn_frame.pack(pady=20, fill="x")

        btn_preview = ctk.CTkButton(
            btn_frame,
            text="Refresh Preview",
            command=self._update_preview
        )
        btn_preview.pack(pady=5, fill="x")

        btn_apply = ctk.CTkButton(
            btn_frame,
            text="Apply to Artwork",
            command=self._apply_frame_config,
            fg_color="#2196F3"
        )
        btn_apply.pack(pady=5, fill="x")

    def _refresh_artwork_list(self):
        """Refresh the artwork list"""
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Add artwork buttons
        for artwork in self.app.artworks:
            # Add indicator if artwork has frame
            frame_indicator = " [Framed]" if artwork.frame_config else ""
            btn = ctk.CTkButton(
                self.list_frame,
                text=f"{artwork.name}{frame_indicator}",
                command=lambda a=artwork: self._select_artwork(a)
            )
            btn.pack(fill="x", pady=2, padx=2)

    def _select_artwork(self, artwork):
        """Select artwork for framing"""
        self.selected_artwork = artwork
        self._init_frame_config()
        self._update_preview()

    def _on_mat_enabled_changed(self):
        """Handle mat enabled checkbox change"""
        self._update_preview()

    def _choose_mat_color(self):
        """Choose mat color"""
        color = colorchooser.askcolor(title="Choose Mat Color", initialcolor=self.mat_color)
        if color[1]:
            self.mat_color = color[1]
            self.mat_color_btn.configure(fg_color=self.mat_color)
            self._update_preview()

    def _choose_frame_color(self):
        """Choose frame color"""
        color = colorchooser.askcolor(title="Choose Frame Color", initialcolor=self.frame_color)
        if color[1]:
            self.frame_color = color[1]
            self.frame_color_btn.configure(fg_color=self.frame_color)
            self._update_preview()

    def _update_preview(self):
        """Update preview with current frame configuration"""
        if not self.selected_artwork:
            return

        try:
            # Get frame parameters
            frame_width = float(self.frame_width_entry.get())
            mat_width = float(self.mat_width_entry.get()) if self.mat_enabled_var.get() else 0

            # Create frame config
            mat_config = None
            if self.mat_enabled_var.get() and mat_width > 0:
                mat_config = MatConfig(
                    top_width_cm=mat_width,
                    bottom_width_cm=mat_width,
                    left_width_cm=mat_width,
                    right_width_cm=mat_width,
                    color=self.mat_color
                )

            frame_config = FrameConfig(
                mat=mat_config,
                frame_width_cm=frame_width,
                frame_color=self.frame_color,
                frame_shadow_enabled=self.frame_shadow_var.get(),
                mat_shadow_enabled=self.mat_shadow_var.get()
            )

            # Render preview
            artwork_image = self.app.artwork_images.get(self.selected_artwork.art_id)
            if artwork_image is not None:
                # Use moderate scale for preview
                scale = 10.0  # 10 pixels per cm

                framed_img = FrameRenderer.render_framed_artwork(
                    artwork_image,
                    self.selected_artwork.real_width_cm,
                    self.selected_artwork.real_height_cm,
                    frame_config,
                    scale
                )

                # Resize for display if too large
                max_size = 400
                if framed_img.width > max_size or framed_img.height > max_size:
                    ratio = min(max_size / framed_img.width, max_size / framed_img.height)
                    new_size = (int(framed_img.width * ratio), int(framed_img.height * ratio))
                    framed_img = framed_img.resize(new_size, Image.LANCZOS)

                # Convert to PhotoImage and display
                photo = ImageTk.PhotoImage(framed_img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo  # Keep a reference

        except ValueError:
            pass

    def _apply_frame_config(self):
        """Apply current frame configuration to selected artwork"""
        if not self.selected_artwork:
            return

        try:
            # Get frame parameters
            frame_width = float(self.frame_width_entry.get())
            mat_width = float(self.mat_width_entry.get()) if self.mat_enabled_var.get() else 0

            # Create frame config
            mat_config = None
            if self.mat_enabled_var.get() and mat_width > 0:
                mat_config = MatConfig(
                    top_width_cm=mat_width,
                    bottom_width_cm=mat_width,
                    left_width_cm=mat_width,
                    right_width_cm=mat_width,
                    color=self.mat_color
                )

            frame_config = FrameConfig(
                mat=mat_config,
                frame_width_cm=frame_width,
                frame_color=self.frame_color,
                frame_shadow_enabled=self.frame_shadow_var.get(),
                mat_shadow_enabled=self.mat_shadow_var.get()
            )

            # Apply to artwork
            self.selected_artwork.frame_config = frame_config

            # Update the artwork list to show it's framed
            self._refresh_artwork_list()

            self.app._show_info("Frame configuration applied!")

        except ValueError:
            self.app._show_error("Invalid frame dimensions")

    def _continue_to_workspace(self):
        """Continue to workspace"""
        self.app.show_workspace_screen()
