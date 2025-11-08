"""
Gallery Wall Visualizer - Main Entry Point

A desktop application for visualizing gallery wall arrangements.
Users can photograph their walls, prepare and frame their artwork digitally,
then experiment with different arrangements before committing to hanging anything.
"""

import sys
from app import GalleryWallApp


def main():
    """Main entry point"""
    try:
        app = GalleryWallApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
