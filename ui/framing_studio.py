"""
Framing Studio Screen
"""
import customtkinter as ctk
from tkinter import colorchooser, simpledialog, messagebox
from models.frame import FrameConfig, MatConfig, FrameTemplate
from processors.frame_renderer import FrameRenderer
from utils.template_manager import TemplateManager
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

        # Template manager
        self.template_manager = TemplateManager()

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

            # Reset UI to defaults
            if hasattr(self, 'mat_enabled_var'):
                self.mat_enabled_var.set(False)
                self.mat_width_entry.delete(0, 'end')
                self.mat_width_entry.insert(0, "3.0")
                self.mat_color = "#FFFFFF"
                self.mat_color_btn.configure(fg_color=self.mat_color)

                self.frame_width_entry.delete(0, 'end')
                self.frame_width_entry.insert(0, "2.0")
                self.frame_color = "#000000"
                self.frame_color_btn.configure(fg_color=self.frame_color)

                self.frame_shadow_var.set(True)
                self.mat_shadow_var.set(True)

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

        # Preview canvas with background for better visibility
        preview_frame = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        preview_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Select artwork to preview",
            font=("Arial", 12),
            text_color="gray"
        )
        self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)

        # Initial preview
        if self.selected_artwork:
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

        # Templates section
        template_label = ctk.CTkLabel(controls_frame, text="Templates", font=("Arial", 12, "bold"))
        template_label.pack(pady=(20, 5))

        # Template selection
        self.template_var = ctk.StringVar(value="")
        self.template_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.template_var,
            values=["No templates"],
            command=self._on_template_selected
        )
        self.template_dropdown.pack(pady=5, fill="x", padx=5)
        self._refresh_templates_list()

        # Template buttons
        template_btn_frame = ctk.CTkFrame(controls_frame)
        template_btn_frame.pack(pady=5, fill="x")

        btn_save_template = ctk.CTkButton(
            template_btn_frame,
            text="💾 Save as Template",
            command=self._save_as_template,
            width=140
        )
        btn_save_template.pack(side="left", pady=5, padx=2)

        btn_apply_template = ctk.CTkButton(
            template_btn_frame,
            text="📋 Apply Template",
            command=self._apply_template,
            width=140
        )
        btn_apply_template.pack(side="right", pady=5, padx=2)

        btn_bulk_apply = ctk.CTkButton(
            controls_frame,
            text="📋 Apply to All Artworks",
            command=self._bulk_apply_template,
            fg_color="#28A745"
        )
        btn_bulk_apply.pack(pady=5, fill="x", padx=5)

        btn_delete_template = ctk.CTkButton(
            controls_frame,
            text="🗑️ Delete Template",
            command=self._delete_template,
            fg_color="#DC3545"
        )
        btn_delete_template.pack(pady=5, fill="x", padx=5)

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
            self.preview_label.configure(
                text="Select artwork to preview",
                image=None,
                text_color="gray"
            )
            return

        # Check if artwork image exists
        artwork_image = self.app.artwork_images.get(self.selected_artwork.art_id)
        if artwork_image is None:
            self.preview_label.configure(
                text=f"Image not found for:\n{self.selected_artwork.name}",
                image=None,
                text_color="red"
            )
            return

        try:
            # Get frame parameters
            frame_width = float(self.frame_width_entry.get()) if hasattr(self, 'frame_width_entry') else 2.0
            mat_width = float(self.mat_width_entry.get()) if hasattr(self, 'mat_width_entry') and self.mat_enabled_var.get() else 0

            # Create frame config
            mat_config = None
            if hasattr(self, 'mat_enabled_var') and self.mat_enabled_var.get() and mat_width > 0:
                mat_config = MatConfig(
                    top_width_cm=mat_width,
                    bottom_width_cm=mat_width,
                    left_width_cm=mat_width,
                    right_width_cm=mat_width,
                    color=self.mat_color if hasattr(self, 'mat_color') else "#FFFFFF"
                )

            frame_config = FrameConfig(
                mat=mat_config,
                frame_width_cm=frame_width,
                frame_color=self.frame_color if hasattr(self, 'frame_color') else "#000000",
                frame_shadow_enabled=self.frame_shadow_var.get() if hasattr(self, 'frame_shadow_var') else True,
                mat_shadow_enabled=self.mat_shadow_var.get() if hasattr(self, 'mat_shadow_var') else True
            )

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
            max_size = 500
            if framed_img.width > max_size or framed_img.height > max_size:
                ratio = min(max_size / framed_img.width, max_size / framed_img.height)
                new_size = (int(framed_img.width * ratio), int(framed_img.height * ratio))
                framed_img = framed_img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(framed_img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo  # Keep a reference

        except Exception as e:
            print(f"Error updating preview: {e}")
            self.preview_label.configure(
                text=f"Error rendering preview:\n{str(e)}",
                image=None,
                text_color="red"
            )

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

    def _refresh_templates_list(self):
        """Refresh the templates dropdown list"""
        templates = self.template_manager.load_all_templates()

        if templates:
            template_names = [t.name for t in templates]
            self.template_dropdown.configure(values=template_names)
            if not self.template_var.get() or self.template_var.get() not in template_names:
                self.template_var.set(template_names[0])
        else:
            self.template_dropdown.configure(values=["No templates"])
            self.template_var.set("No templates")

    def _on_template_selected(self, template_name: str):
        """Handle template selection from dropdown"""
        # Just update the selection, don't auto-apply
        pass

    def _save_as_template(self):
        """Save current frame configuration as a template"""
        if not self.selected_artwork:
            messagebox.showwarning("No Artwork", "Please select an artwork first")
            return

        # Ask for template name
        name = simpledialog.askstring(
            "Save Template",
            "Enter a name for this frame template:",
            parent=self.parent
        )

        if not name:
            return

        # Ask for optional description
        description = simpledialog.askstring(
            "Template Description",
            "Enter a description (optional):",
            parent=self.parent
        )

        if description is None:
            description = ""

        try:
            # Get current frame config
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

            # Create template
            template = FrameTemplate(
                template_id="",  # Will be auto-generated
                name=name,
                description=description,
                frame_config=frame_config,
                created_date="",  # Will be auto-generated
                modified_date=""  # Will be auto-generated
            )

            # Save template
            if self.template_manager.save_template(template):
                self._refresh_templates_list()
                self.template_var.set(name)
                messagebox.showinfo("Success", f"Template '{name}' saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save template")

        except ValueError:
            messagebox.showerror("Error", "Invalid frame dimensions")

    def _apply_template(self):
        """Apply selected template to current artwork"""
        if not self.selected_artwork:
            messagebox.showwarning("No Artwork", "Please select an artwork first")
            return

        template_name = self.template_var.get()
        if template_name == "No templates":
            messagebox.showwarning("No Template", "No template selected")
            return

        # Find the template
        templates = self.template_manager.load_all_templates()
        selected_template = None
        for template in templates:
            if template.name == template_name:
                selected_template = template
                break

        if not selected_template:
            messagebox.showerror("Error", "Template not found")
            return

        # Apply to current artwork
        self.selected_artwork.frame_config = FrameConfig.from_dict(
            selected_template.frame_config.to_dict()
        )

        # Update UI with template values
        self._init_frame_config()
        self._update_preview()
        self._refresh_artwork_list()

        messagebox.showinfo("Success", f"Template '{template_name}' applied to {self.selected_artwork.name}")

    def _bulk_apply_template(self):
        """Apply selected template to all artworks"""
        template_name = self.template_var.get()
        if template_name == "No templates":
            messagebox.showwarning("No Template", "No template selected")
            return

        if len(self.app.artworks) == 0:
            messagebox.showwarning("No Artworks", "No artworks to apply template to")
            return

        # Confirm bulk apply
        if not messagebox.askyesno(
            "Confirm Bulk Apply",
            f"Apply template '{template_name}' to all {len(self.app.artworks)} artworks?\n\n"
            f"This will overwrite existing frame configurations."
        ):
            return

        # Find the template
        templates = self.template_manager.load_all_templates()
        selected_template = None
        for template in templates:
            if template.name == template_name:
                selected_template = template
                break

        if not selected_template:
            messagebox.showerror("Error", "Template not found")
            return

        # Apply to all artworks
        count = 0
        for artwork in self.app.artworks:
            artwork.frame_config = FrameConfig.from_dict(
                selected_template.frame_config.to_dict()
            )
            count += 1

        # Refresh UI
        self._refresh_artwork_list()
        if self.selected_artwork:
            self._init_frame_config()
            self._update_preview()

        messagebox.showinfo(
            "Success",
            f"Template '{template_name}' applied to {count} artwork(s)"
        )

    def _delete_template(self):
        """Delete selected template"""
        template_name = self.template_var.get()
        if template_name == "No templates":
            messagebox.showwarning("No Template", "No template selected")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Delete template '{template_name}'?"):
            return

        # Find the template
        templates = self.template_manager.load_all_templates()
        template_id = None
        for template in templates:
            if template.name == template_name:
                template_id = template.template_id
                break

        if template_id:
            if self.template_manager.delete_template(template_id):
                self._refresh_templates_list()
                messagebox.showinfo("Success", f"Template '{template_name}' deleted")
            else:
                messagebox.showerror("Error", "Failed to delete template")

    def _continue_to_workspace(self):
        """Continue to workspace"""
        self.app.show_workspace_screen()
