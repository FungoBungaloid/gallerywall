"""
Main Application Class
"""
import customtkinter as ctk
from typing import Optional, List, Dict
from models.wall import Wall
from models.artwork import Artwork
from models.workspace import Workspace
from utils.file_manager import FileManager
import config


class GalleryWallApp:
    """Main application controller"""

    def __init__(self):
        """Initialize application"""
        self.root = ctk.CTk()
        self.root.title(config.APP_NAME)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")

        # Set theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Application state
        self.file_manager: Optional[FileManager] = None
        self.current_wall: Optional[Wall] = None
        self.artworks: List[Artwork] = []
        self.artwork_images: Dict[str, any] = {}  # art_id -> numpy array
        self.workspaces: List[Workspace] = []
        self.current_workspace: Optional[Workspace] = None

        # Current screen
        self.current_screen = None

        # Initialize UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main UI structure"""
        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Show welcome screen initially
        self.show_welcome_screen()

    def show_welcome_screen(self):
        """Show welcome/start screen"""
        self._clear_screen()

        # Welcome frame
        welcome_frame = ctk.CTkFrame(self.main_container)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            welcome_frame,
            text=config.APP_NAME,
            font=("Arial", 32, "bold")
        )
        title.pack(pady=(50, 10))

        # Subtitle
        subtitle = ctk.CTkLabel(
            welcome_frame,
            text="Plan your perfect gallery wall arrangement",
            font=("Arial", 14)
        )
        subtitle.pack(pady=(0, 50))

        # Buttons
        btn_new = ctk.CTkButton(
            welcome_frame,
            text="New Project",
            command=self.new_project,
            width=200,
            height=40,
            font=("Arial", 14)
        )
        btn_new.pack(pady=10)

        btn_load = ctk.CTkButton(
            welcome_frame,
            text="Load Project",
            command=self.load_project,
            width=200,
            height=40,
            font=("Arial", 14)
        )
        btn_load.pack(pady=10)

    def new_project(self):
        """Start a new project"""
        from ui.wall_setup import WallSetupScreen
        self._clear_screen()
        self.current_screen = WallSetupScreen(self, self.main_container)

    def load_project(self):
        """Load an existing project"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("Gallery Wall Project", "*.gwproj"), ("All Files", "*.*")]
        )

        if file_path:
            self.file_manager = FileManager(file_path)
            project_data = self.file_manager.load_project()

            if project_data:
                self._load_project_data(project_data)
                self.show_workspace_screen()
            else:
                self._show_error("Failed to load project file")

    def _load_project_data(self, project_data: dict):
        """Load project data into application state"""
        # Load wall
        if 'walls' in project_data and len(project_data['walls']) > 0:
            self.current_wall = Wall.from_dict(project_data['walls'][0])

        # Load artworks
        if 'artworks' in project_data:
            self.artworks = [Artwork.from_dict(a) for a in project_data['artworks']]

        # Load workspaces
        if 'workspaces' in project_data:
            self.workspaces = [Workspace.from_dict(w) for w in project_data['workspaces']]
            if len(self.workspaces) > 0:
                self.current_workspace = self.workspaces[0]

    def save_project(self):
        """Save current project"""
        if not self.file_manager:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Save Project",
                defaultextension=".gwproj",
                filetypes=[("Gallery Wall Project", "*.gwproj"), ("All Files", "*.*")]
            )

            if file_path:
                self.file_manager = FileManager(file_path)
            else:
                return

        # Build project data
        project_data = {
            'project_name': config.DEFAULT_PROJECT_NAME,
            'walls': [self.current_wall.to_dict()] if self.current_wall else [],
            'artworks': [a.to_dict() for a in self.artworks],
            'workspaces': [w.to_dict() for w in self.workspaces]
        }

        if self.file_manager.save_project(project_data):
            self._show_info("Project saved successfully")
        else:
            self._show_error("Failed to save project")

    def show_wall_setup_screen(self):
        """Show wall setup screen"""
        from ui.wall_setup import WallSetupScreen
        self._clear_screen()
        self.current_screen = WallSetupScreen(self, self.main_container)

    def show_art_editor_screen(self):
        """Show art editor screen"""
        from ui.art_editor import ArtEditorScreen
        self._clear_screen()
        self.current_screen = ArtEditorScreen(self, self.main_container)

    def show_framing_studio_screen(self):
        """Show framing studio screen"""
        from ui.framing_studio import FramingStudioScreen
        self._clear_screen()
        self.current_screen = FramingStudioScreen(self, self.main_container)

    def show_workspace_screen(self):
        """Show arrangement workspace screen"""
        from ui.arrangement_workspace import ArrangementWorkspaceScreen
        self._clear_screen()
        self.current_screen = ArrangementWorkspaceScreen(self, self.main_container)

    def _clear_screen(self):
        """Clear current screen"""
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.current_screen = None

    def _show_error(self, message: str):
        """Show error dialog"""
        from tkinter import messagebox
        messagebox.showerror("Error", message)

    def _show_info(self, message: str):
        """Show info dialog"""
        from tkinter import messagebox
        messagebox.showinfo("Info", message)

    def run(self):
        """Start the application"""
        self.root.mainloop()
