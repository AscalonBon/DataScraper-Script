import time
import json
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime

class VeterinaryDataScraper:
    def __init__(self):
        self.options = Options()
        self.driver = None
        self.data = {}
        
    def start_browser(self):
        """Initialize Firefox browser"""
        try:
            service = Service(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=self.options)
            print("✅ Firefox started successfully")
            return True
        except:
            try:
                self.driver = webdriver.Firefox(options=self.options)
                print("✅ Firefox started successfully")
                return True
            except Exception as e:
                print(f"❌ Error starting Firefox: {e}")
                return False
    
    def close_browser(self):
        if self.driver:
            self.driver.quit()
    
    def initial_login(self, url=None):
        """Initial login - opens Petdentity login page"""
        if not url:
            url = "https://app.petdentity.com.ph/session/login"
        
        self.driver.get(url)
        return True
    
    def scrape_current_page(self, url=None):
        """Scrape the current page data"""
        if url:
            self.driver.get(url)
            time.sleep(3)
        
        # Get all text from the page
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        
        # Reset data
        self.data = {}
        
        # Extract using regex patterns
        self.extract_key_value_pairs(page_text)
        
        # Clean up
        self.clean_data()
        
        return self.data
    
    def extract_key_value_pairs(self, text):
        """Extract data from key-value patterns"""
        
        # Define patterns for critical fields
        patterns = {
            'birthdate': r'BirthDate\s*\n\s*([A-Za-z]{3}\s\d{2},\s\d{4})',
            'weight': r'Weight\s*\n\s*([\d.]+)\s*kg',
            'color': r'Coat\(Color\)\s*\n\s*([A-Za-z0-9/]+)',
            'coat_remarks': r'Coat Remarks\s*\n\s*([^\n]+)',
            'gender': r'Gender\s*\n\s*([A-Z]+)',
            'species': r'Animal\s*\n\s*([A-Z]+)',
            'breed': r'Breed\s*\n\s*([A-Z\s]+)',
            'age': r'Age\s*\n\s*([^\n]+)',
            'pet_name': r'Pet Name\s*\n\s*([^\n]+)',
            'privacy': r'Privacy\s*\n\s*([A-Z]+)',
            'pet_status': r'Pet Status\s*\n\s*([A-Z]+)',
            'microchip': r'Microchip\s*\n\s*(\d{15})'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value != "No data available" and value != "NaN cm(s)":
                    self.data[field] = value
        
        # Extract address
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if (re.match(r'^(Unit|Block|Lot|No\.?|#)\s*\d+', line, re.IGNORECASE) or
                re.match(r'^\d+\s+[A-Za-z]+', line)):
                address_lines = [line]
                j = i + 1
                while j < len(lines) and j < i + 4:
                    next_line = lines[j]
                    if (',' in next_line or 'CITY' in next_line.upper() or 
                        'NCR' in next_line or 'Philippines' in next_line):
                        address_lines.append(next_line)
                        j += 1
                    else:
                        break
                if address_lines:
                    self.data['address'] = ', '.join(address_lines)
                    break
        
        if 'address' not in self.data:
            address_match = re.search(
                r'([A-Za-z0-9\s,\.\-]+(?:CITY|PROVINCE|REGION|NCR)[^\n]+(?:\n[^\n]+){0,2})',
                text,
                re.IGNORECASE
            )
            if address_match:
                self.data['address'] = address_match.group(1).strip()
        
        # Find owner name and mobile - IMPROVED NAME PATTERN
        # This pattern captures: First Middle? Last with possible suffix (Jr., Sr., etc.)
        # Examples: Bernard T. Dela Cruz, Dianne Bernadette R. Dela Cruz, Princess Kate R. Dela Cruz
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)'
        
        phone_pattern = r'(\d{11,13})'
        phones = re.findall(phone_pattern, text)
        names = re.findall(name_pattern, text)
        
        if phones:
            owner_found = False
            for i, phone in enumerate(phones):
                if i == 0:
                    phone_pos = text.find(phone)
                    text_before = text[max(0, phone_pos - 300):phone_pos]
                    names_before = re.findall(name_pattern, text_before)
                    if names_before:
                        # Get the full name (not just last part)
                        full_name = names_before[-1].strip()
                        self.data['owner_name'] = full_name
                        self.data['mobile'] = phone
                        print(f"Found Owner: {full_name}")
                        owner_found = True
                    else:
                        if names:
                            self.data['owner_name'] = names[0].strip()
                            self.data['mobile'] = phone
                            owner_found = True
                else:
                    # Additional contacts - only add if not the same as owner
                    if 'additional_contacts' not in self.data:
                        self.data['additional_contacts'] = []
                    
                    phone_pos = text.find(phone)
                    text_before = text[max(0, phone_pos - 300):phone_pos]
                    names_before = re.findall(name_pattern, text_before)
                    
                    if names_before:
                        contact_name = names_before[-1].strip()
                    else:
                        # Try to find name in the line with the phone
                        lines_with_phone = [line for line in lines if phone in line]
                        if lines_with_phone:
                            # Extract name from that line (before the phone number)
                            line = lines_with_phone[0]
                            name_match = re.search(name_pattern, line)
                            if name_match:
                                contact_name = name_match.group(1).strip()
                            else:
                                contact_name = "Unknown"
                        else:
                            contact_name = "Unknown"
                    
                    # Clean up the contact name - remove trailing phone numbers or extra text
                    contact_name = re.sub(r'\s*\d+$', '', contact_name).strip()
                    
                    # Only add if it's a valid name and not already in the list
                    if contact_name and contact_name != "Unknown" and len(contact_name) > 3:
                        # Check if this contact is already in the list
                        contact_entry = f"{contact_name} - {phone}"
                        existing_contacts = [c.split(' - ')[0] for c in self.data['additional_contacts']]
                        if contact_name not in existing_contacts and contact_name != self.data.get('owner_name', ''):
                            self.data['additional_contacts'].append(contact_entry)
                            print(f"Found Additional Contact: {contact_entry}")
        
        # If owner not found, try a different approach - look for name patterns in the text
        if 'owner_name' not in self.data:
            # Look for names with phone numbers nearby
            for i, line in enumerate(lines):
                # Check if line has a phone number
                if re.search(r'\d{11,13}', line):
                    # Extract name from the same line or previous line
                    name_match = re.search(name_pattern, line)
                    if not name_match and i > 0:
                        name_match = re.search(name_pattern, lines[i-1])
                    
                    if name_match:
                        name = name_match.group(1).strip()
                        phone = re.search(r'(\d{11,13})', line).group(1)
                        if 'owner_name' not in self.data:
                            self.data['owner_name'] = name
                            self.data['mobile'] = phone
                            print(f"Found Owner (alt): {name}")
                        else:
                            # Additional contact
                            if 'additional_contacts' not in self.data:
                                self.data['additional_contacts'] = []
                            contact_entry = f"{name} - {phone}"
                            existing_names = [c.split(' - ')[0] for c in self.data['additional_contacts']]
                            if name not in existing_names and name != self.data.get('owner_name', ''):
                                self.data['additional_contacts'].append(contact_entry)
                                print(f"Found Additional Contact (alt): {contact_entry}")
        
        # Extract vaccination data
        date_pattern = r'([A-Za-z]{3}\s\d{2},\s\d{4})'
        all_dates = re.findall(date_pattern, text)
        
        vaccination_records = []
        for i in range(len(all_dates) - 1):
            date1 = all_dates[i]
            date2 = all_dates[i + 1]
            
            pos1 = text.find(date1)
            pos2 = text.find(date2, pos1 + 1)
            
            if pos2 - pos1 < 300:
                if not re.search(f'BirthDate.*{date1}', text[pos1-50:pos1+50]):
                    vax_entry = {
                        'date': date1,
                        'expiration': date2,
                        'type': 'Not provided',
                        'lot': 'Not provided'
                    }
                    vaccination_records.append(vax_entry)
                    break
        
        # Store vaccination records
        for idx, vax in enumerate(vaccination_records[:3], 1):
            suffix = f"_{idx}" if idx > 1 else ""
            self.data[f'vaccination_date{suffix}'] = vax.get('date', 'Not provided')
            self.data[f'vaccine_type{suffix}'] = vax.get('type', 'Not provided')
            self.data[f'vaccine_lot{suffix}'] = vax.get('lot', 'Not provided')
            self.data[f'vaccine_expiration{suffix}'] = vax.get('expiration', 'Not provided')
    
    def clean_data(self):
        """Clean and organize the collected data"""
        
        critical_defaults = {
            'owner_name': 'Not found',
            'mobile': 'Not found',
            'address': 'Not found',
            'birthdate': 'Not found',
            'weight': 'Not found',
            'color': 'Not found',
            'coat_remarks': 'Not found',
            'gender': 'Not found',
            'microchip': 'Not found',
            'pet_name': 'Not found',
            'species': 'Not found',
            'breed': 'Not found',
            'age': 'Not found',
            'privacy': 'Not found',
            'pet_status': 'Not found'
        }
        
        for field, default in critical_defaults.items():
            if field not in self.data:
                self.data[field] = default
        
        if 'additional_contacts' not in self.data:
            self.data['additional_contacts'] = []
        
        while len(self.data['additional_contacts']) < 3:
            self.data['additional_contacts'].append('Not provided')
        
        for i in range(1, 4):
            suffix = f"_{i}" if i > 1 else ""
            for field in ['vaccination_date', 'vaccine_type', 'vaccine_lot', 'vaccine_expiration']:
                key = f'{field}{suffix}'
                if key not in self.data:
                    self.data[key] = 'Not provided'


class PetdentityScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Petdentity Data Scraper")
        self.root.geometry("1200x800")
        
        self.scraper = None
        self.current_data = None
        self.all_records = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI interface"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Petdentity Veterinary Data Scraper", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # Control Frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # URL Entry
        ttk.Label(control_frame, text="Pet Page URL:").grid(row=0, column=0, padx=5)
        self.url_entry = ttk.Entry(control_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5)
        
        # Buttons
        self.login_btn = ttk.Button(control_frame, text="1. Login", command=self.login)
        self.login_btn.grid(row=0, column=2, padx=5)
        
        self.scrape_btn = ttk.Button(control_frame, text="2. Scrape", command=self.scrape, state='disabled')
        self.scrape_btn.grid(row=0, column=3, padx=5)
        
        self.save_btn = ttk.Button(control_frame, text="Save Record", command=self.save_record, state='disabled')
        self.save_btn.grid(row=0, column=4, padx=5)
        
        self.save_all_btn = ttk.Button(control_frame, text="Save All", command=self.save_all, state='disabled')
        self.save_all_btn.grid(row=0, column=5, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="Clear All", command=self.clear_all)
        self.clear_btn.grid(row=0, column=6, padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Status: Not logged in", foreground="red")
        self.status_label.grid(row=2, column=0, sticky=(tk.W), pady=5)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Tab 1: Current Record
        self.current_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.current_frame, text="Current Record")
        
        # Create Treeview for current record
        self.create_treeview(self.current_frame)
        
        # Tab 2: All Records
        self.all_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.all_frame, text="All Records (0)")
        
        # Create Treeview for all records
        self.create_all_records_treeview(self.all_frame)
        
        # Tab 3: Raw JSON
        self.json_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.json_frame, text="Raw JSON")
        
        self.json_text = scrolledtext.ScrolledText(self.json_frame, wrap=tk.WORD, height=20)
        self.json_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Record counter
        self.record_counter = ttk.Label(main_frame, text="Records scraped: 0")
        self.record_counter.grid(row=4, column=0, sticky=(tk.W), pady=5)
        
    def create_treeview(self, parent):
        """Create the treeview for displaying current record"""
        
        # Create frame with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview
        columns = ('Field', 'Value')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        
        # Define headings
        self.tree.heading('Field', text='Field')
        self.tree.heading('Value', text='Value')
        
        # Set column widths
        self.tree.column('Field', width=250)
        self.tree.column('Value', width=700)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_all_records_treeview(self, parent):
        """Create the treeview for displaying all records"""
        
        # Create frame with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview with more columns
        columns = ('#', 'Pet Name', 'Owner', 'Mobile', 'Birthdate', 'Gender', 'Microchip')
        self.all_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.all_tree.heading('#', text='#')
        self.all_tree.heading('Pet Name', text='Pet Name')
        self.all_tree.heading('Owner', text='Owner')
        self.all_tree.heading('Mobile', text='Mobile')
        self.all_tree.heading('Birthdate', text='Birthdate')
        self.all_tree.heading('Gender', text='Gender')
        self.all_tree.heading('Microchip', text='Microchip')
        
        # Set column widths
        self.all_tree.column('#', width=50)
        self.all_tree.column('Pet Name', width=120)
        self.all_tree.column('Owner', width=200)
        self.all_tree.column('Mobile', width=120)
        self.all_tree.column('Birthdate', width=120)
        self.all_tree.column('Gender', width=80)
        self.all_tree.column('Microchip', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.all_tree.yview)
        self.all_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click to show details
        self.all_tree.bind('<Double-Button-1>', self.show_record_details)
        
        # Pack
        self.all_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def login(self):
        """Handle login process"""
        try:
            self.status_label.config(text="Status: Opening browser...", foreground="orange")
            self.root.update()
            
            self.scraper = VeterinaryDataScraper()
            if self.scraper.start_browser():
                self.scraper.initial_login()
                self.login_btn.config(state='disabled')
                self.scrape_btn.config(state='normal')
                self.status_label.config(text="Status: Logged in - Enter URL and click Scrape", foreground="green")
                messagebox.showinfo("Success", "Browser opened! Please login manually in the Firefox window.")
            else:
                self.status_label.config(text="Status: Failed to start browser", foreground="red")
                messagebox.showerror("Error", "Failed to start Firefox. Please make sure Firefox is installed.")
                
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def scrape(self):
        """Scrape the current page"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a pet page URL")
            return
        
        try:
            self.status_label.config(text="Status: Scraping data...", foreground="orange")
            self.root.update()
            
            data = self.scraper.scrape_current_page(url)
            self.current_data = data
            
            # Display in treeview
            self.display_data(data)
            
            # Update JSON tab
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, json.dumps(data, indent=2))
            
            self.save_btn.config(state='normal')
            self.save_all_btn.config(state='normal')
            self.status_label.config(text="Status: Scrape complete!", foreground="green")
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Scraping failed: {str(e)}")
    
    def display_data(self, data):
        """Display data in the treeview"""
        # Clear current tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Define field order and labels
        field_order = [
            ('pet_name', 'Pet Name'),
            ('species', 'Species'),
            ('breed', 'Breed'),
            ('birthdate', 'Birthdate'),
            ('age', 'Age'),
            ('weight', 'Weight (kg)'),
            ('gender', 'Gender'),
            ('color', 'Color'),
            ('coat_remarks', 'Coat Remarks'),
            ('microchip', 'Microchip'),
            ('privacy', 'Privacy'),
            ('pet_status', 'Pet Status'),
            ('owner_name', 'Owner Name'),
            ('mobile', 'Mobile Number'),
            ('address', 'Address'),
        ]
        
        # Add fields
        for field_key, field_label in field_order:
            value = data.get(field_key, 'Not found')
            if value and value != 'Not found':
                self.tree.insert('', tk.END, values=(field_label, value))
        
        # Add additional contacts
        contacts = data.get('additional_contacts', [])
        for i, contact in enumerate(contacts, 1):
            if contact and contact != 'Not provided':
                self.tree.insert('', tk.END, values=(f'Contact {i}', contact))
        
        # Add vaccination records
        for i in range(1, 4):
            suffix = f"_{i}" if i > 1 else ""
            date = data.get(f'vaccination_date{suffix}', 'Not provided')
            if date and date != 'Not provided':
                vax_type = data.get(f'vaccine_type{suffix}', 'Not provided')
                lot = data.get(f'vaccine_lot{suffix}', 'Not provided')
                expiration = data.get(f'vaccine_expiration{suffix}', 'Not provided')
                
                vax_text = f"Date: {date}"
                if vax_type and vax_type != 'Not provided':
                    vax_text += f", Type: {vax_type}"
                if lot and lot != 'Not provided':
                    vax_text += f", Lot: {lot}"
                if expiration and expiration != 'Not provided':
                    vax_text += f", Expiration: {expiration}"
                
                self.tree.insert('', tk.END, values=(f'Vaccination {i}', vax_text))
    
    def save_record(self):
        """Save the current record to file"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        filename = f"vet_record_{len(self.all_records) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.current_data, f, indent=2)
        
        # Add to all records
        self.all_records.append(self.current_data.copy())
        self.update_all_records_treeview()
        self.record_counter.config(text=f"Records scraped: {len(self.all_records)}")
        self.notebook.tab(1, text=f"All Records ({len(self.all_records)})")
        
        messagebox.showinfo("Success", f"Record saved to {filename}")
    
    def save_all(self):
        """Save all records to a single file"""
        if not self.all_records:
            messagebox.showwarning("Warning", "No records to save")
            return
        
        filename = f"all_vet_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.all_records, f, indent=2)
        
        messagebox.showinfo("Success", f"All {len(self.all_records)} records saved to {filename}")
    
    def update_all_records_treeview(self):
        """Update the all records treeview"""
        # Clear current tree
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)
        
        # Add all records
        for idx, record in enumerate(self.all_records, 1):
            self.all_tree.insert('', tk.END, values=(
                idx,
                record.get('pet_name', 'N/A'),
                record.get('owner_name', 'N/A'),
                record.get('mobile', 'N/A'),
                record.get('birthdate', 'N/A'),
                record.get('gender', 'N/A'),
                record.get('microchip', 'N/A')
            ))
    
    def show_record_details(self, event):
        """Show details of a selected record"""
        selection = self.all_tree.selection()
        if not selection:
            return
        
        # Get the record index
        values = self.all_tree.item(selection[0])['values']
        if not values:
            return
        
        idx = values[0] - 1  # Convert to 0-based index
        if 0 <= idx < len(self.all_records):
            record = self.all_records[idx]
            
            # Display in current tab
            self.display_data(record)
            self.notebook.select(0)  # Switch to current record tab
            
            # Update JSON tab
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, json.dumps(record, indent=2))
            
            self.current_data = record
            self.save_btn.config(state='normal')
    
    def clear_all(self):
        """Clear all data"""
        if messagebox.askyesno("Confirm", "Clear all records?"):
            self.all_records = []
            for item in self.all_tree.get_children():
                self.all_tree.delete(item)
            self.record_counter.config(text="Records scraped: 0")
            self.notebook.tab(1, text="All Records (0)")
            self.save_all_btn.config(state='disabled')


def main():
    root = tk.Tk()
    app = PetdentityScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()