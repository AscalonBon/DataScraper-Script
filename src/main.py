#!/usr/bin/env python3
"""
Petdentity Veterinary Data Scraper
Main entry point for the application
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the src directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import GUI - UPDATED to import from app_gui
from app_gui import PetdentityScraperGUI

def main():
    """Main entry point"""
    try:
        root = tk.Tk()
        root.state('zoomed')
        root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))
        app = PetdentityScraperGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Fatal error: {e}")
        try:
            messagebox.showerror("Fatal Error", f"Application failed to start:\n{str(e)}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()