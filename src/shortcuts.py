"""
Keyboard shortcuts manager for the Petdentity Scraper
"""

import tkinter as tk
from tkinter import ttk


class ShortcutManager:
    """Manage keyboard shortcuts for the application"""
    
    def __init__(self, root, gui_instance):
        """
        Initialize the shortcut manager
        
        Args:
            root: The root tkinter window
            gui_instance: The PetdentityScraperGUI instance
        """
        self.root = root
        self.gui = gui_instance
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Setup all keyboard shortcuts"""
        
        # ============================================================
        # ENTER KEY - Trigger Scrape & Add
        # ============================================================
        # Bind Enter key to scrape function when focus is on URL entry
        self.gui.url_entry.bind('<Return>', self.on_enter_pressed)
        
        # Also bind to the root window (so Enter works anywhere)
        self.root.bind('<Return>', self.on_enter_pressed)
        
        # ============================================================
        # OTHER USEFUL SHORTCUTS
        # ============================================================
        
        # Ctrl+S - Save Credentials
        self.root.bind('<Control-s>', self.on_ctrl_s)
        self.root.bind('<Control-S>', self.on_ctrl_s)
        
        # Ctrl+E - Export CSV
        self.root.bind('<Control-e>', self.on_ctrl_e)
        self.root.bind('<Control-E>', self.on_ctrl_e)
        
        # Ctrl+C - Copy selected cells (already handled in Treeview)
        # This is handled by the Treeview's built-in binding
        
        # F1 - Help (show shortcuts)
        self.root.bind('<F1>', self.show_shortcuts_help)
        
        # F5 - Refresh/Scrape
        self.root.bind('<F5>', self.on_f5)
        
        # Escape - Clear URL entry
        self.root.bind('<Escape>', self.on_escape)
        
        # Ctrl+L - Focus URL entry
        self.root.bind('<Control-l>', self.on_ctrl_l)
        self.root.bind('<Control-L>', self.on_ctrl_l)
        
        # Ctrl+Q - Quit application
        self.root.bind('<Control-q>', self.on_ctrl_q)
        self.root.bind('<Control-Q>', self.on_ctrl_q)
        
        print("✅ Keyboard shortcuts loaded:")
        print("   Enter      - Scrape & Add")
        print("   Ctrl+S     - Save Credentials")
        print("   Ctrl+E     - Export CSV")
        print("   Ctrl+C     - Copy selected cells")
        print("   Ctrl+L     - Focus URL entry")
        print("   Ctrl+Q     - Quit")
        print("   F1         - Show shortcuts help")
        print("   F5         - Scrape & Add")
        print("   Escape     - Clear URL entry")
    
    def on_enter_pressed(self, event=None):
        """Handle Enter key press - triggers Scrape & Add"""
        # Check if the Scrape button is enabled
        if self.gui.scrape_btn['state'] != 'disabled':
            # Check if there's a URL entered
            url = self.gui.url_entry.get().strip()
            if url:
                self.gui.scrape_and_add()
                return "break"  # Prevent default Enter behavior
            else:
                # Focus the URL entry if empty
                self.gui.url_entry.focus()
                self.gui.status_label.config(
                    text="Status: ⚠️ Enter a URL first",
                    foreground="orange"
                )
        else:
            self.gui.status_label.config(
                text="Status: ⚠️ Please wait for login to complete",
                foreground="orange"
            )
        return "break"
    
    def on_ctrl_s(self, event=None):
        """Handle Ctrl+S - Save Credentials"""
        self.gui.save_credentials()
        return "break"
    
    def on_ctrl_e(self, event=None):
        """Handle Ctrl+E - Export CSV"""
        self.gui.export_to_csv()
        return "break"
    
    def on_f5(self, event=None):
        """Handle F5 - Scrape & Add"""
        self.on_enter_pressed()
        return "break"
    
    def on_escape(self, event=None):
        """Handle Escape - Clear URL entry"""
        self.gui.url_entry.delete(0, tk.END)
        self.gui.url_entry.focus()
        self.gui.status_label.config(
            text="Status: URL cleared",
            foreground="blue"
        )
        return "break"
    
    def on_ctrl_l(self, event=None):
        """Handle Ctrl+L - Focus URL entry"""
        self.gui.url_entry.focus()
        self.gui.url_entry.select_range(0, tk.END)
        self.gui.status_label.config(
            text="Status: URL entry focused",
            foreground="blue"
        )
        return "break"
    
    def on_ctrl_q(self, event=None):
        """Handle Ctrl+Q - Quit application"""
        if self.gui.all_records:
            if tk.messagebox.askyesno("Quit", "You have unsaved records. Are you sure you want to quit?"):
                self.root.quit()
        else:
            self.root.quit()
        return "break"
    
    def show_shortcuts_help(self, event=None):
        """Show a help dialog with all keyboard shortcuts"""
        help_text = """
        🐾 Petdentity Scraper - Keyboard Shortcuts
        
        ─────────────────────────────────────────────
        Enter          - Scrape & Add (on URL entry)
        Ctrl+S         - Save Credentials
        Ctrl+E         - Export CSV
        Ctrl+C         - Copy selected cells (in table)
        Ctrl+L         - Focus URL entry
        Ctrl+Q         - Quit application
        F1             - Show this help
        F5             - Scrape & Add
        Escape         - Clear URL entry
        
        ─────────────────────────────────────────────
        💡 Double-click any cell to copy its value
        💡 Select rows + Ctrl+C to copy to Excel
        """
        
        # Create a popup window
        help_window = tk.Toplevel(self.root)
        help_window.title("Keyboard Shortcuts")
        help_window.geometry("500x400")
        help_window.resizable(False, False)
        
        # Make it modal
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Center the window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (help_window.winfo_screenheight() // 2) - (400 // 2)
        help_window.geometry(f"+{x}+{y}")
        
        # Add text
        text_widget = tk.Text(help_window, wrap=tk.WORD, font=('Courier', 10), padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
        
        return "break"