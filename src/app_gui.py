import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
# Import from other modules
from data_scraper import VeterinaryDataScraper
from config import Config
from shortcuts import ShortcutManager


# ============================================================
# VISUAL THEME - DARK MODE
# Centralized so the whole app's look can be tuned from one
# place instead of scattered color strings everywhere.
# ============================================================
COLORS = {
    'bg':          '#1a1a2e',   # app background - dark navy
    'card_bg':     '#16213e',   # section/card background - dark blue
    'border':      '#2a3a6a',   # card borders - muted blue
    'text':        '#e8e8f0',   # main text - light gray
    'muted':       '#8899bb',   # secondary text - muted blue-gray
    'primary':     '#4a7cf7',   # main action (Scrape & Add) - bright blue
    'primary_dark':'#3a5fc9',
    'success':     '#22c55e',   # Export - bright green
    'success_dark':'#16a34a',
    'danger':      '#ef4444',   # Clear All - bright red
    'danger_dark': '#dc2626',
    'accent':      '#06b6d4',   # Save credentials - cyan
    'accent_dark': '#0891b2',
    'row_odd':     '#1e2a4a',   # dark blue-gray
    'row_even':    '#16213e',   # dark blue
    'header_bg':   '#0f1629',   # very dark blue
    'header_fg':   '#c8d0e0',   # light gray-blue
    'entry_bg':    '#1a1a2e',   # entry background
    'entry_fg':    '#e8e8f0',   # entry text
}

STATUS_STYLES = {
    'info':    {'bg': '#1a3a6a', 'fg': '#7ab7ff'},
    'success': {'bg': '#1a4a2a', 'fg': '#4ade80'},
    'error':   {'bg': '#4a1a1a', 'fg': '#f87171'},
    'warning': {'bg': '#4a3a1a', 'fg': '#fbbf24'},
}

FONT_FAMILY = 'Segoe UI'


class PetdentityScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Petdentity Data Scraper")

        # Set window icon
        self.set_window_icon()

        self.root.geometry("1600x850")
        self.root.configure(bg=COLORS['bg'])

        self.scraper = None
        self.current_data = None
        self.all_records = []
        self.config = Config()
        self.auto_login_done = False
        self.logo_image = None  # Keep reference to prevent garbage collection

        self.apply_theme()
        self.setup_ui()
        self.load_saved_credentials()

        # ============================================================
        # INITIALIZE SHORTCUT MANAGER
        # ============================================================
        self.shortcuts = ShortcutManager(self.root, self)
        print("✅ Shortcut manager initialized")

        # Auto-login if credentials exist
        self.root.after(500, self.auto_login_if_credentials_exist)

    # ============================================================
    # THEME / STYLE SETUP
    # ============================================================
    def apply_theme(self):
        """
        Configure a consistent visual style for every ttk widget in the
        app: fonts, colors, card-style LabelFrames, and colored buttons
        per action (blue = primary, teal = save, green = export,
        red = destructive). Centralizing this here means the whole app's
        look can be tuned in one place.
        """
        style = ttk.Style()
        # 'clam' is the base theme that actually honors background/
        # foreground color overrides on Windows (the default 'vista'
        # theme mostly ignores them).
        style.theme_use('clam')

        style.configure('.', font=(FONT_FAMILY, 10), background=COLORS['bg'],
                         foreground=COLORS['text'])

        # Frames / cards
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Card.TLabelframe', background=COLORS['card_bg'],
                         bordercolor=COLORS['border'], relief='solid', borderwidth=2)
        style.configure('Card.TLabelframe.Label', background=COLORS['card_bg'],
                         foreground=COLORS['text'], font=(FONT_FAMILY, 10, 'bold'))

        # Labels
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'])
        style.configure('Card.TLabel', background=COLORS['card_bg'], foreground=COLORS['text'])
        style.configure('Muted.TLabel', background=COLORS['bg'], foreground=COLORS['muted'])
        style.configure('CardMuted.TLabel', background=COLORS['card_bg'], foreground=COLORS['muted'])
        style.configure('Title.TLabel', background=COLORS['bg'], foreground=COLORS['text'],
                         font=(FONT_FAMILY, 18, 'bold'))
        style.configure('Subtitle.TLabel', background=COLORS['bg'], foreground=COLORS['muted'],
                         font=(FONT_FAMILY, 10))
        style.configure('Counter.TLabel', background=COLORS['bg'], foreground=COLORS['primary'],
                         font=(FONT_FAMILY, 11, 'bold'))

        # Entries - dark mode
        style.configure('TEntry', fieldbackground=COLORS['entry_bg'], 
                         foreground=COLORS['entry_fg'],
                         bordercolor=COLORS['border'],
                         lightcolor=COLORS['border'], 
                         darkcolor=COLORS['border'], 
                         padding=5)
        style.map('TEntry',
                  fieldbackground=[('focus', COLORS['entry_bg'])])

        # Buttons — base + per-action colors
        style.configure('TButton', font=(FONT_FAMILY, 10, 'bold'), padding=(12, 8),
                         relief='flat', borderwidth=0)

        style.configure('Primary.TButton', background=COLORS['primary'], foreground='#ffffff')
        style.map('Primary.TButton',
                  background=[('active', COLORS['primary_dark']), ('disabled', '#2a4a8a')],
                  foreground=[('disabled', '#8899bb')])

        style.configure('Success.TButton', background=COLORS['success'], foreground='#ffffff')
        style.map('Success.TButton',
                  background=[('active', COLORS['success_dark']), ('disabled', '#2a6a3a')],
                  foreground=[('disabled', '#8899bb')])

        style.configure('Danger.TButton', background=COLORS['danger'], foreground='#ffffff')
        style.map('Danger.TButton',
                  background=[('active', COLORS['danger_dark']), ('disabled', '#6a2a2a')],
                  foreground=[('disabled', '#8899bb')])

        style.configure('Accent.TButton', background=COLORS['accent'], foreground='#ffffff')
        style.map('Accent.TButton',
                  background=[('active', COLORS['accent_dark']), ('disabled', '#2a5a6a')],
                  foreground=[('disabled', '#8899bb')])

        # Treeview (records table) - dark mode with clear separators
        style.configure('Treeview', 
                        background=COLORS['row_even'], 
                        fieldbackground=COLORS['row_even'],
                        foreground=COLORS['text'], 
                        rowheight=28, 
                        font=(FONT_FAMILY, 9),
                        bordercolor=COLORS['border'], 
                        borderwidth=2)
        
        # Treeview heading - dark
        style.configure('Treeview.Heading', 
                        background=COLORS['header_bg'], 
                        foreground=COLORS['header_fg'],
                        font=(FONT_FAMILY, 9, 'bold'), 
                        relief='solid', 
                        borderwidth=1, 
                        padding=(6, 6))
        style.map('Treeview.Heading', 
                  background=[('active', COLORS['header_bg'])])
        
        # Treeview selection colors
        style.map('Treeview', 
                  background=[('selected', COLORS['primary'])],
                  foreground=[('selected', '#ffffff')])

        # Scrollbars - dark
        style.configure('TScrollbar', 
                        background=COLORS['bg'], 
                        troughcolor=COLORS['bg'],
                        bordercolor=COLORS['border'], 
                        arrowcolor=COLORS['muted'])
        style.map('TScrollbar',
                  background=[('active', COLORS['card_bg'])])

    def set_window_icon(self):
        """Set the window icon for the application using .ico file"""
        try:
            # Get the path to the icon
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            
            # Try multiple possible icon locations
            icon_paths = [
                os.path.join(parent_dir, 'assets', 'logo.ico'),  # .ico in assets folder
                os.path.join(script_dir, 'assets', 'logo.ico'),  # .ico in script's assets folder
                os.path.join(parent_dir, 'logo.ico'),  # .ico in parent directory
                os.path.join(script_dir, 'logo.ico'),  # .ico in script directory
            ]
            
            # Also try PNG as fallback
            png_paths = [
                os.path.join(parent_dir, 'assets', 'logo.png'),
                os.path.join(script_dir, 'assets', 'logo.png'),
            ]
            
            # Try .ico files first
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    print(f"✅ Found icon file: {icon_path}")
                    try:
                        # For .ico files, use iconbitmap (works on Windows)
                        self.root.iconbitmap(default=icon_path)
                        print(f"✅ Window icon set from: {icon_path}")
                        return
                    except Exception as e:
                        print(f"⚠️ Failed to set icon from {icon_path}: {e}")
                        continue
            
            # If no .ico found, try PNG as fallback
            for png_path in png_paths:
                if os.path.exists(png_path):
                    print(f"⚠️ No .ico found, trying PNG: {png_path}")
                    try:
                        # Use PIL to convert PNG to PhotoImage
                        from PIL import Image, ImageTk
                        img = Image.open(png_path)
                        # Resize for icon
                        img = img.resize((64, 64), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.root.iconphoto(True, photo)
                        print(f"✅ Window icon set from PNG: {png_path}")
                        return
                    except ImportError:
                        try:
                            # Try direct PNG without PIL
                            self.root.iconphoto(True, tk.PhotoImage(file=png_path))
                            print(f"✅ Window icon set from PNG: {png_path}")
                            return
                        except Exception as e:
                            print(f"⚠️ Failed to set icon from PNG: {e}")
                            continue
            
            # If we get here, no icon was found
            print("⚠️ No icon file found. Looking in:")
            for path in icon_paths + png_paths:
                print(f"   - {path}")

        except Exception as e:
            print(f"⚠️ Could not set icon: {e}")

    # ============================================================
    # STATUS HELPER
    # Replaces the old scattered `self.status_label.config(text=...,
    # foreground="green")` calls with one consistent, color-coded
    # "chip" style status bar (info/success/error/warning).
    # ============================================================
    def set_status(self, message, kind='info'):
        colors = STATUS_STYLES.get(kind, STATUS_STYLES['info'])
        self.status_label.config(text=message, bg=colors['bg'], fg=colors['fg'])

    def setup_ui(self):
        """Setup the GUI interface"""

        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame
        main_frame = ttk.Frame(self.root, padding="16")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main frame grid
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # ------------------------------------------------------
        # Title with subtitle (logo removed)
        # ------------------------------------------------------
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, pady=(0, 12), sticky=tk.W)

        title_label = ttk.Label(title_frame, text="Petdentity Veterinary Data Scraper",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)

        subtitle_label = ttk.Label(title_frame, text="Automated pet record extraction",
                                  style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W)

        # ------------------------------------------------------
        # Credentials Card
        # ------------------------------------------------------
        cred_frame = ttk.LabelFrame(main_frame, text="🔐  Login Credentials", padding="14",
                                     style='Card.TLabelframe')
        cred_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        cred_frame.columnconfigure(1, weight=1)
        cred_frame.columnconfigure(3, weight=1)

        ttk.Label(cred_frame, text="Username/Email:", style='Card.TLabel').grid(
            row=0, column=0, padx=(0, 6), sticky=tk.W)
        self.username_entry = ttk.Entry(cred_frame, width=32)
        self.username_entry.grid(row=0, column=1, padx=(0, 20), sticky=(tk.W, tk.E))

        ttk.Label(cred_frame, text="Password:", style='Card.TLabel').grid(
            row=0, column=2, padx=(0, 6), sticky=tk.W)
        self.password_entry = ttk.Entry(cred_frame, width=32, show="•")
        self.password_entry.grid(row=0, column=3, padx=(0, 12), sticky=(tk.W, tk.E))

        self.save_creds_btn = ttk.Button(cred_frame, text="💾 Save", style='Accent.TButton',
                                          command=self.save_credentials)
        self.save_creds_btn.grid(row=0, column=4, padx=(0, 10))

        self.status_creds_label = ttk.Label(cred_frame, text="", style='CardMuted.TLabel')
        self.status_creds_label.grid(row=0, column=5, padx=5)

        # ------------------------------------------------------
        # Controls Card
        # ------------------------------------------------------
        control_frame = ttk.LabelFrame(main_frame, text="🌐  Scrape a Pet Page", padding="14",
                                        style='Card.TLabelframe')
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Pet Page URL:", style='Card.TLabel').grid(
            row=0, column=0, padx=(0, 6), sticky=tk.W)
        self.url_entry = ttk.Entry(control_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=(0, 12), sticky=(tk.W, tk.E))

        self.scrape_btn = ttk.Button(control_frame, text="📥 Scrape & Add", style='Primary.TButton',
                                     command=self.scrape_and_add, state='disabled')
        self.scrape_btn.grid(row=0, column=2, padx=5)

        self.export_btn = ttk.Button(control_frame, text="📊 Export CSV", style='Success.TButton',
                                      command=self.export_to_csv, state='disabled')
        self.export_btn.grid(row=0, column=3, padx=5)

        self.clear_btn = ttk.Button(control_frame, text="🗑️ Clear All", style='Danger.TButton',
                                     command=self.clear_all)
        self.clear_btn.grid(row=0, column=4, padx=5)

        # ------------------------------------------------------
        # Status bar — colored "chip" (plain tk.Label so bg/fg can
        # be changed freely per message type via set_status()).
        # ------------------------------------------------------
        self.status_label = tk.Label(
            main_frame, text="Status: Starting up...",
            font=(FONT_FAMILY, 9, 'bold'), anchor='w',
            padx=12, pady=6, bd=0
        )
        self.status_label.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.set_status("Status: Starting up...", 'info')

        # ------------------------------------------------------
        # Records Table Card
        # ------------------------------------------------------
        table_frame = ttk.LabelFrame(main_frame, text="📋  All Records", padding="10",
                                      style='Card.TLabelframe')
        table_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.create_all_records_treeview(table_frame)

        # ------------------------------------------------------
        # Bottom frame with counter and instructions
        # ------------------------------------------------------
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        self.record_counter = ttk.Label(bottom_frame, text="📊 Records: 0", style='Counter.TLabel')
        self.record_counter.grid(row=0, column=0, sticky=tk.W)

        instruction_label = ttk.Label(bottom_frame,
                                      text="💡 Double-click cell to copy  •  Select rows + Ctrl+C to copy",
                                      style='Muted.TLabel')
        instruction_label.grid(row=0, column=1, sticky=tk.E)

    def create_all_records_treeview(self, parent):
        """Create the treeview with all required columns including Contact Address"""

        # Create frame with scrollbars
        tree_container = ttk.Frame(parent)
        tree_container.pack(fill=tk.BOTH, expand=True)

        # Define columns - Added 'Contact Address' after 'Complete Address'
        columns = (
            '#',
            'Breed',
            'Pet Owner Fullname',
            'Mobile Number',
            'Complete Address',
            'Contact Address',  # NEW: Separate contact address column
            'Additional Contact 1',
            'Additional Contact 2',
            'Additional Contact 3',
            'Date of Birth',
            'Weight (Kg)',
            'Sex',
            'Color / Markings',
            'Microchip Number',
            'Vaccination Date',
            'Vaccine Type',
            'Vaccine Serial',
            'Vaccine Lot',
            'Vaccine Expiration',
            'Vaccination Date 2',
            'Vaccine Type 2',
            'Vaccine Serial 2',
            'Vaccine Lot 2',
            'Vaccine Expiration 2',
            'Vaccination Date 3',
            'Vaccine Type 3',
            'Vaccine Serial 3',
            'Vaccine Lot 3',
            'Vaccine Expiration 3'
        )

        # Create Treeview with separator lines
        self.all_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='headings',
            height=20,
            selectmode='extended'
        )

        # Define column widths
        column_widths = {
            '#': 40,
            'Breed': 150,
            'Pet Owner Fullname': 120,
            'Mobile Number': 100,
            'Complete Address': 150,
            'Contact Address': 150,  # NEW: Contact Address column
            'Additional Contact 1': 150,
            'Additional Contact 2': 150,
            'Additional Contact 3': 150,
            'Date of Birth': 80,
            'Weight (Kg)': 80,
            'Sex': 80,
            'Color / Markings': 116,
            'Microchip Number': 116,
            'Vaccination Date': 116,
            'Vaccine Type': 100,
            'Vaccine Serial': 100,
            'Vaccine Lot': 100,
            'Vaccine Expiration': 100,
            'Vaccination Date 2': 100,
            'Vaccine Type 2': 100,
            'Vaccine Serial 2': 100,
            'Vaccine Lot 2': 100,
            'Vaccine Expiration 2': 100,
            'Vaccination Date 3': 100,
            'Vaccine Type 3': 100,
            'Vaccine Serial 3': 100,
            'Vaccine Lot 3': 100,
            'Vaccine Expiration 3': 100
        }

        # Configure headings and columns with clear separators
        for col in columns:
            self.all_tree.heading(col, text=col, anchor='w')
            width = column_widths.get(col, 100)
            self.all_tree.column(col, width=width, minwidth=50, anchor='w')

        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.all_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.all_tree.xview)

        self.all_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Bind events
        self.all_tree.bind('<Control-c>', self.copy_selected_cells)
        self.all_tree.bind('<Control-C>', self.copy_selected_cells)
        self.all_tree.bind('<Double-Button-1>', self.copy_cell_on_double_click)

        # Grid layout
        self.all_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Configure grid weights
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Row coloring — darker zebra striping for dark mode
        self.all_tree.tag_configure('oddrow', background=COLORS['row_odd'])
        self.all_tree.tag_configure('evenrow', background=COLORS['row_even'])

        # Add separator lines between rows by configuring Treeview to show grid
        # Note: ttk.Treeview doesn't natively support grid lines, so we'll use
        # the border of each cell to create separator effect
        self.all_tree.tag_configure('oddrow', background=COLORS['row_odd'])
        self.all_tree.tag_configure('evenrow', background=COLORS['row_even'])

    def copy_cell_on_double_click(self, event):
        """Copy the clicked cell on double-click"""
        try:
            item = self.all_tree.identify_row(event.y)
            column = self.all_tree.identify_column(event.x)

            if not item:
                return

            col_index = int(column.replace('#', '')) - 1
            values = self.all_tree.item(item, 'values')

            if values and col_index < len(values):
                cell_value = str(values[col_index]).strip()
                if cell_value:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(cell_value)

                    display_value = cell_value[:50] + '...' if len(cell_value) > 50 else cell_value
                    self.set_status(f"✅ Copied: {display_value}", 'success')
                    self.root.after(3000, lambda: self.set_status(
                        f"Status: {len(self.all_records)} records loaded", 'info'
                    ))
        except Exception as e:
            print(f"Copy error: {e}")

    def copy_selected_cells(self, event):
        """Copy selected rows to clipboard"""
        try:
            selected_items = self.all_tree.selection()
            if not selected_items:
                return

            rows_data = []
            for item in selected_items:
                values = self.all_tree.item(item, 'values')
                if values:
                    rows_data.append('\t'.join(str(v) for v in values))

            if rows_data:
                clipboard_text = '\n'.join(rows_data)
                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_text)

                row_count = len(rows_data)
                self.set_status(f"✅ Copied {row_count} row(s) to clipboard", 'success')
                self.root.after(3000, lambda: self.set_status(
                    f"Status: {len(self.all_records)} records loaded", 'info'
                ))
        except Exception as e:
            print(f"Copy error: {e}")

    def load_saved_credentials(self):
        """Load saved credentials from file"""
        username, password = self.config.load_credentials()
        if username:
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)
            self.status_creds_label.config(text="✅ Credentials loaded", foreground=STATUS_STYLES['success']['fg'])
            return True
        return False

    def save_credentials(self):
        """Save credentials to file"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_creds_label.config(text="⚠️ Enter both fields", foreground=STATUS_STYLES['error']['fg'])
            return

        if self.config.save_credentials(username, password):
            self.status_creds_label.config(text="✅ Saved!", foreground=STATUS_STYLES['success']['fg'])
            # Auto-login after saving
            self.auto_login_if_credentials_exist()
        else:
            self.status_creds_label.config(text="❌ Save failed", foreground=STATUS_STYLES['error']['fg'])

    def auto_login_if_credentials_exist(self):
        """Auto-login if credentials exist - NO POPUPS"""
        if self.auto_login_done:
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.set_status("Status: Enter credentials and click Save", 'warning')
            return

        try:
            self.set_status("Status: 🔐 Auto-logging in...", 'warning')
            self.root.update()

            self.scraper = VeterinaryDataScraper(username, password)
            if self.scraper.start_browser():
                if self.scraper.auto_login():
                    self.auto_login_done = True
                    self.scrape_btn.config(state='normal')
                    self.set_status("Status: ✅ Auto-login successful! Enter URL and click 'Scrape & Add'", 'success')
                else:
                    self.set_status("Status: ⚠️ Auto-login failed. Check credentials and click Save again.", 'error')
            else:
                self.set_status("Status: ❌ Failed to start browser", 'error')

        except Exception as e:
            self.set_status(f"Status: ❌ Error - {str(e)[:50]}", 'error')

    def manual_login(self):
        """Manual login fallback - NO POPUPS"""
        try:
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()

            if not username or not password:
                self.set_status("Status: ⚠️ Enter credentials first", 'error')
                return

            if not self.scraper:
                self.scraper = VeterinaryDataScraper(username, password)
                if not self.scraper.start_browser():
                    self.set_status("Status: ❌ Failed to start browser", 'error')
                    return

            if self.scraper.auto_login():
                self.auto_login_done = True
                self.scrape_btn.config(state='normal')
                self.set_status("Status: ✅ Login successful! Enter URL and click 'Scrape & Add'", 'success')
            else:
                self.set_status("Status: ❌ Login failed. Check credentials.", 'error')

        except Exception as e:
            self.set_status(f"Status: ❌ Error - {str(e)[:50]}", 'error')

    def scrape_and_add(self):
        """Scrape the current page and add to All Records"""
        url = self.url_entry.get().strip()

        if not url:
            self.set_status("Status: ⚠️ Enter a pet page URL", 'error')
            return

        try:
            self.set_status("Status: 🔍 Scraping data...", 'warning')
            self.root.update()

            data = self.scraper.scrape_current_page(url)
            self.current_data = data

            # Add to all records
            self.all_records.append(data.copy())

            # Update the table
            self.update_all_records_treeview()

            # Enable export button
            self.export_btn.config(state='normal')

            # Update counter
            self.record_counter.config(text=f"📊 Records: {len(self.all_records)}")

            self.set_status(f"Status: ✅ Record #{len(self.all_records)} added!", 'success')

            self.url_entry.delete(0, tk.END)
            self.url_entry.focus()

        except Exception as e:
            self.set_status(f"Status: ❌ Error - {str(e)[:50]}", 'error')

    def update_all_records_treeview(self):
        """Update the all records treeview"""
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)

        for idx, record in enumerate(self.all_records, 1):
            contacts = record.get('additional_contacts', ['', '', ''])
            while len(contacts) < 3:
                contacts.append('')

            address_parts = []
            if record.get('house_no'):
                address_parts.append(record.get('house_no'))
            if record.get('city_municipality'):
                address_parts.append(record.get('city_municipality'))
            if record.get('province'):
                address_parts.append(record.get('province'))

            complete_address = ', '.join(address_parts) if address_parts else record.get('address', '')

            # Get the separate contact address
            contact_address = record.get('contact_address', '')

            color_markings = record.get('color', '')
            coat_remarks = record.get('coat_remarks', '')
            if coat_remarks and coat_remarks != '-' and coat_remarks != 'Not found':
                if color_markings:
                    color_markings += f" / {coat_remarks}"
                else:
                    color_markings = coat_remarks

            row_values = (
                idx,
                record.get('breed', ''),
                record.get('owner_name', ''),
                record.get('mobile', ''),
                complete_address,
                contact_address,
                contacts[0] if contacts[0] else '',
                contacts[1] if contacts[1] else '',
                contacts[2] if contacts[2] else '',
                record.get('birthdate', ''),
                record.get('weight', ''),
                record.get('gender', ''),
                color_markings,
                record.get('microchip', ''),
                record.get('vaccination_date_1', ''),
                record.get('vaccine_type_1', ''),
                record.get('vaccine_serial_1', ''),
                record.get('vaccine_lot_1', ''),
                record.get('vaccine_expiration_1', ''),
                record.get('vaccination_date_2', ''),
                record.get('vaccine_type_2', ''),
                record.get('vaccine_serial_2', ''),
                record.get('vaccine_lot_2', ''),
                record.get('vaccine_expiration_2', ''),
                record.get('vaccination_date_3', ''),
                record.get('vaccine_type_3', ''),
                record.get('vaccine_serial_3', ''),
                record.get('vaccine_lot_3', ''),
                record.get('vaccine_expiration_3', '')
            )

            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.all_tree.insert('', tk.END, values=row_values, tags=(tag,))

    def export_to_csv(self):
        """Export all records to CSV"""
        if not self.all_records:
            self.set_status("Status: ⚠️ No records to export", 'error')
            return

        try:
            import csv

            filename = f"pet_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            headers = [
                '#', 'Pet Owner Fullname', 'Mobile Number', 'Complete Address', 'Contact Address',
                'Additional Contact 1', 'Additional Contact 2', 'Additional Contact 3',
                'Date of Birth', 'Weight (Kg)', 'Sex', 'Color / Markings',
                'Microchip Number',
                'Vaccination Date', 'Vaccine Type', 'Vaccine Serial', 'Vaccine Lot', 'Vaccine Expiration',
                'Vaccination Date 2', 'Vaccine Type 2', 'Vaccine Serial 2', 'Vaccine Lot 2', 'Vaccine Expiration 2',
                'Vaccination Date 3', 'Vaccine Type 3', 'Vaccine Serial 3', 'Vaccine Lot 3', 'Vaccine Expiration 3'
            ]

            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                for idx, record in enumerate(self.all_records, 1):
                    contacts = record.get('additional_contacts', ['', '', ''])
                    while len(contacts) < 3:
                        contacts.append('')

                    address_parts = []
                    if record.get('house_no'):
                        address_parts.append(record.get('house_no'))
                    if record.get('city_municipality'):
                        address_parts.append(record.get('city_municipality'))
                    if record.get('province'):
                        address_parts.append(record.get('province'))

                    complete_address = ', '.join(address_parts) if address_parts else record.get('address', '')

                    # Get the separate contact address
                    contact_address = record.get('contact_address', '')

                    color_markings = record.get('color', '')
                    coat_remarks = record.get('coat_remarks', '')
                    if coat_remarks and coat_remarks != '-' and coat_remarks != 'Not found':
                        if color_markings:
                            color_markings += f" / {coat_remarks}"
                        else:
                            color_markings = coat_remarks

                    row = [
                        idx,
                        record.get('owner_name', ''),
                        record.get('mobile', ''),
                        complete_address,
                        contact_address,  # NEW: Contact Address column
                        contacts[0] if contacts[0] else '',
                        contacts[1] if contacts[1] else '',
                        contacts[2] if contacts[2] else '',
                        record.get('birthdate', ''),
                        record.get('weight', ''),
                        record.get('gender', ''),
                        color_markings,
                        record.get('microchip', ''),
                        record.get('vaccination_date_1', ''),
                        record.get('vaccine_type_1', ''),
                        record.get('vaccine_serial_1', ''),
                        record.get('vaccine_lot_1', ''),
                        record.get('vaccine_expiration_1', ''),
                        record.get('vaccination_date_2', ''),
                        record.get('vaccine_type_2', ''),
                        record.get('vaccine_serial_2', ''),
                        record.get('vaccine_lot_2', ''),
                        record.get('vaccine_expiration_2', ''),
                        record.get('vaccination_date_3', ''),
                        record.get('vaccine_type_3', ''),
                        record.get('vaccine_serial_3', ''),
                        record.get('vaccine_lot_3', ''),
                        record.get('vaccine_expiration_3', '')
                    ]
                    writer.writerow(row)

            self.set_status(f"✅ Exported {len(self.all_records)} records to {filename}", 'success')

        except Exception as e:
            self.set_status(f"❌ Export failed: {str(e)[:50]}", 'error')

    def clear_all(self):
        """Clear all records"""
        self.all_records = []
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)
        self.record_counter.config(text="📊 Records: 0")
        self.export_btn.config(state='disabled')
        self.set_status("Status: All records cleared", 'info')