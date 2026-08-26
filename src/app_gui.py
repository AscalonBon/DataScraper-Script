import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Import from other modules
from data_scraper import VeterinaryDataScraper
from config import Config

class PetdentityScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Petdentity Data Scraper")
        self.root.geometry("1500x850")
        
        self.scraper = None
        self.current_data = None
        self.all_records = []
        self.config = Config()
        
        self.setup_ui()
        self.load_saved_credentials()
        
    def setup_ui(self):
        """Setup the GUI interface"""
        
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🐾 Petdentity Veterinary Data Scraper", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=5, sticky=tk.W)
        
        # Credentials Frame
        cred_frame = ttk.LabelFrame(main_frame, text="Login Credentials", padding="10")
        cred_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        cred_frame.columnconfigure(1, weight=1)
        
        ttk.Label(cred_frame, text="Username/Email:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.username_entry = ttk.Entry(cred_frame, width=35)
        self.username_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(cred_frame, text="Password:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.password_entry = ttk.Entry(cred_frame, width=35, show="*")
        self.password_entry.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        self.save_creds_btn = ttk.Button(cred_frame, text="💾 Save", command=self.save_credentials)
        self.save_creds_btn.grid(row=0, column=4, padx=5)
        
        # Control Frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        ttk.Label(control_frame, text="Pet Page URL:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.url_entry = ttk.Entry(control_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        # Buttons
        self.login_btn = ttk.Button(control_frame, text="🔑 Login", command=self.login)
        self.login_btn.grid(row=0, column=2, padx=5)
        
        self.scrape_btn = ttk.Button(control_frame, text="📥 Scrape & Add", command=self.scrape_and_add, state='disabled')
        self.scrape_btn.grid(row=0, column=3, padx=5)
        
        self.export_btn = ttk.Button(control_frame, text="📊 Export CSV", command=self.export_to_csv, state='disabled')
        self.export_btn.grid(row=0, column=4, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="🗑️ Clear All", command=self.clear_all)
        self.clear_btn.grid(row=0, column=5, padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Status: Not logged in", foreground="red")
        self.status_label.grid(row=3, column=0, sticky=(tk.W), pady=5)
        
        # Records Table - Main area
        table_frame = ttk.LabelFrame(main_frame, text="All Records", padding="5")
        table_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with all columns
        self.create_all_records_treeview(table_frame)
        
        # Bottom frame with counter and instructions
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)
        
        self.record_counter = ttk.Label(bottom_frame, text="📊 Records: 0", font=('Arial', 10, 'bold'))
        self.record_counter.grid(row=0, column=0, sticky=tk.W)
        
        instruction_label = ttk.Label(bottom_frame, 
                                     text="💡 Double-click cell to copy | Select rows + Ctrl+C to copy",
                                     foreground="blue")
        instruction_label.grid(row=0, column=1, sticky=tk.E)
        
    def create_all_records_treeview(self, parent):
        """Create the treeview with all required columns"""
        
        # Create frame with scrollbars
        tree_container = ttk.Frame(parent)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = (
            '#',
            'Pet Owner Fullname',
            'Mobile Number',
            'Complete Address',
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
            'Vaccine Lot',
            'Vaccine Expiration',
            'Vaccination Date 2',
            'Vaccine Type 2',
            'Vaccine Lot 2',
            'Vaccine Expiration 2',
            'Vaccination Date 3',
            'Vaccine Type 3',
            'Vaccine Lot 3',
            'Vaccine Expiration 3'
        )
        
        # Create Treeview
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
            'Pet Owner Fullname': 200,
            'Mobile Number': 130,
            'Complete Address': 300,
            'Additional Contact 1': 200,
            'Additional Contact 2': 200,
            'Additional Contact 3': 200,
            'Date of Birth': 100,
            'Weight (Kg)': 80,
            'Sex': 70,
            'Color / Markings': 150,
            'Microchip Number': 150,
            'Vaccination Date': 110,
            'Vaccine Type': 110,
            'Vaccine Lot': 110,
            'Vaccine Expiration': 110,
            'Vaccination Date 2': 110,
            'Vaccine Type 2': 110,
            'Vaccine Lot 2': 110,
            'Vaccine Expiration 2': 110,
            'Vaccination Date 3': 110,
            'Vaccine Type 3': 110,
            'Vaccine Lot 3': 110,
            'Vaccine Expiration 3': 110
        }
        
        # Configure headings and columns
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
        
        # Row coloring
        self.all_tree.tag_configure('oddrow', background='#f5f5f5')
        self.all_tree.tag_configure('evenrow', background='#ffffff')
        
        # Style
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Arial', 9))
        style.configure("Treeview.Heading", font=('Arial', 9, 'bold'))
    
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
                    self.status_label.config(
                        text=f"✅ Copied: {display_value}",
                        foreground="green"
                    )
                    self.root.after(3000, lambda: self.status_label.config(
                        text=f"Status: {len(self.all_records)} records loaded",
                        foreground="blue"
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
                self.status_label.config(
                    text=f"✅ Copied {row_count} row(s) to clipboard",
                    foreground="green"
                )
                self.root.after(3000, lambda: self.status_label.config(
                    text=f"Status: {len(self.all_records)} records loaded",
                    foreground="blue"
                ))
        except Exception as e:
            print(f"Copy error: {e}")
    
    def load_saved_credentials(self):
        """Load saved credentials from file"""
        username, password = self.config.load_credentials()
        if username:
            self.username_entry.insert(0, username)
            self.password_entry.insert(0, password)
            print("✅ Loaded saved credentials")
    
    def save_credentials(self):
        """Save credentials to file"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter both username and password")
            return
        
        if self.config.save_credentials(username, password):
            messagebox.showinfo("Success", "Credentials saved securely!")
        else:
            messagebox.showerror("Error", "Failed to save credentials")
    
    def login(self):
        """Handle login process"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            manual = messagebox.askyesno("Manual Login", 
                                        "No credentials found. Would you like to login manually?")
            if manual:
                self.manual_login()
            return
        
        try:
            self.status_label.config(text="Status: Opening browser...", foreground="orange")
            self.root.update()
            
            self.scraper = VeterinaryDataScraper(username, password)
            if self.scraper.start_browser():
                if self.scraper.auto_login():
                    self.login_btn.config(state='disabled')
                    self.scrape_btn.config(state='normal')
                    self.status_label.config(text="Status: ✅ Auto-login successful!", foreground="green")
                    messagebox.showinfo("Success", "Auto-login successful!")
                else:
                    self.manual_login()
            else:
                self.status_label.config(text="Status: ❌ Failed to start browser", foreground="red")
                messagebox.showerror("Error", "Failed to start Firefox.")
                
        except Exception as e:
            self.status_label.config(text=f"Status: ❌ Error - {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def manual_login(self):
        """Fallback to manual login"""
        try:
            if not self.scraper:
                self.scraper = VeterinaryDataScraper()
                if not self.scraper.start_browser():
                    messagebox.showerror("Error", "Failed to start browser")
                    return
            
            self.scraper.manual_login()
            self.login_btn.config(state='disabled')
            self.scrape_btn.config(state='normal')
            self.status_label.config(text="Status: ✅ Manual login confirmed", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Status: ❌ Error - {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Manual login failed: {str(e)}")
    
    def scrape_and_add(self):
        """Scrape the current page and add to All Records"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a pet page URL")
            return
        
        try:
            self.status_label.config(text="Status: 🔍 Scraping data...", foreground="orange")
            self.root.update()
            
            data = self.scraper.scrape_current_page(url)
            self.current_data = data
            
            # Print scraped data for debugging
            print("\n📊 Scraped Data:")
            for key, value in data.items():
                if value:
                    print(f"  {key}: {value}")
            
            # Add to all records
            self.all_records.append(data.copy())
            
            # Update the table
            self.update_all_records_treeview()
            
            # Enable export button
            self.export_btn.config(state='normal')
            
            # Update counter
            self.record_counter.config(text=f"📊 Records: {len(self.all_records)}")
            
            self.status_label.config(
                text=f"Status: ✅ Record #{len(self.all_records)} added!",
                foreground="green"
            )
            
            self.url_entry.delete(0, tk.END)
            self.url_entry.focus()
            
        except Exception as e:
            self.status_label.config(text=f"Status: ❌ Error - {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Scraping failed: {str(e)}")
    
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
            if record.get('street'):
                address_parts.append(record.get('street'))
            if record.get('barangay'):
                address_parts.append(record.get('barangay'))
            if record.get('city_municipality'):
                address_parts.append(record.get('city_municipality'))
            if record.get('province'):
                address_parts.append(record.get('province'))
            
            complete_address = ', '.join(address_parts) if address_parts else record.get('address', '')
            
            color_markings = record.get('color', '')
            coat_remarks = record.get('coat_remarks', '')
            if coat_remarks and coat_remarks != '-' and coat_remarks != 'Not found':
                if color_markings:
                    color_markings += f" / {coat_remarks}"
                else:
                    color_markings = coat_remarks
            
            row_values = (
                idx,
                record.get('owner_name', ''),
                record.get('mobile', ''),
                complete_address,
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
                record.get('vaccine_lot_1', ''),
                record.get('vaccine_expiration_1', ''),
                record.get('vaccination_date_2', ''),
                record.get('vaccine_type_2', ''),
                record.get('vaccine_lot_2', ''),
                record.get('vaccine_expiration_2', ''),
                record.get('vaccination_date_3', ''),
                record.get('vaccine_type_3', ''),
                record.get('vaccine_lot_3', ''),
                record.get('vaccine_expiration_3', '')
            )
            
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.all_tree.insert('', tk.END, values=row_values, tags=(tag,))
    
    def export_to_csv(self):
        """Export all records to CSV"""
        if not self.all_records:
            messagebox.showwarning("Warning", "No records to export")
            return
        
        try:
            import csv
            
            filename = f"pet_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            headers = [
                '#', 'Pet Owner Fullname', 'Mobile Number', 'Complete Address',
                'Additional Contact 1', 'Additional Contact 2', 'Additional Contact 3',
                'Date of Birth', 'Weight (Kg)', 'Sex', 'Color / Markings',
                'Microchip Number',
                'Vaccination Date', 'Vaccine Type', 'Vaccine Lot', 'Vaccine Expiration',
                'Vaccination Date 2', 'Vaccine Type 2', 'Vaccine Lot 2', 'Vaccine Expiration 2',
                'Vaccination Date 3', 'Vaccine Type 3', 'Vaccine Lot 3', 'Vaccine Expiration 3'
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
                    if record.get('street'):
                        address_parts.append(record.get('street'))
                    if record.get('barangay'):
                        address_parts.append(record.get('barangay'))
                    if record.get('city_municipality'):
                        address_parts.append(record.get('city_municipality'))
                    if record.get('province'):
                        address_parts.append(record.get('province'))
                    
                    complete_address = ', '.join(address_parts) if address_parts else record.get('address', '')
                    
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
                        record.get('vaccine_lot_1', ''),
                        record.get('vaccine_expiration_1', ''),
                        record.get('vaccination_date_2', ''),
                        record.get('vaccine_type_2', ''),
                        record.get('vaccine_lot_2', ''),
                        record.get('vaccine_expiration_2', ''),
                        record.get('vaccination_date_3', ''),
                        record.get('vaccine_type_3', ''),
                        record.get('vaccine_lot_3', ''),
                        record.get('vaccine_expiration_3', '')
                    ]
                    writer.writerow(row)
            
            messagebox.showinfo("Success", f"✅ Exported {len(self.all_records)} records to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def clear_all(self):
        """Clear all records"""
        if messagebox.askyesno("Confirm", "Clear all records?"):
            self.all_records = []
            for item in self.all_tree.get_children():
                self.all_tree.delete(item)
            self.record_counter.config(text="📊 Records: 0")
            self.export_btn.config(state='disabled')
            self.status_label.config(text="Status: All records cleared", foreground="blue")


def main():
    root = tk.Tk()
    app = PetdentityScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()