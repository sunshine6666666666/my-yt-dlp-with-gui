import os
import sys

# Ensure core and gui packages are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    # Detect yt-dlp executable
    parent_dir = os.path.dirname(current_dir)
    yt_dlp_path = os.path.join(parent_dir, "yt-dlp")
    
    if os.name == "nt":
        yt_dlp_path += ".exe"
    
    if not os.path.exists(yt_dlp_path):
        yt_dlp_path = "yt-dlp"

    # Decide UI backend
    # Default to PySide6 on macOS for reliability
    try:
        from PySide6.QtWidgets import QApplication
        from gui_qt.app_qt import AppWindow
        
        app = QApplication(sys.argv)
        # Setup dark theme if possible or stick to native
        window = AppWindow(yt_dlp_path=yt_dlp_path)
        window.show()
        sys.exit(app.exec())
    except ImportError:
        print("Error: PySide6 is not installed. Please run: pip install PySide6")
        sys.exit(1)

if __name__ == "__main__":
    main()
