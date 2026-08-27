import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import geckodriver_autoinstaller

class VeterinaryDataScraper:
    def __init__(self, username=None, password=None):
        self.options = Options()
        self.driver = None
        self.data = {}
        self.username = username
        self.password = password
        self.logged_in = False
        
    def start_browser(self):
        """Initialize Firefox browser"""
        try:
            geckodriver_autoinstaller.install()
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
    
    def auto_login(self, url=None):
        """Automatically login using stored credentials"""
        if not url:
            url = "https://app.petdentity.com.ph/session/login"
        
        if self.logged_in:
            return True
        
        print(f"🔐 Auto-logging in...")
        self.driver.get(url)
        time.sleep(2)
        
        try:
            # Find username field
            username_field = None
            username_selectors = [
                "//input[@type='email']",
                "//input[@type='text']",
                "//input[@name='email']",
                "//input[@name='username']",
                "//input[@placeholder='Email']",
                "//input[@placeholder='Username']",
                "//input[@id='email']",
                "//input[@id='username']"
            ]
            
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.XPATH, selector)
                    if username_field:
                        break
                except:
                    continue
            
            # Find password field
            password_field = None
            password_selectors = [
                "//input[@type='password']",
                "//input[@name='password']",
                "//input[@placeholder='Password']",
                "//input[@id='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.XPATH, selector)
                    if password_field:
                        break
                except:
                    continue
            
            if username_field and password_field:
                username_field.clear()
                username_field.send_keys(self.username)
                password_field.clear()
                password_field.send_keys(self.password)
                print("✅ Credentials entered")
                
                # Find login button
                login_selectors = [
                    "//button[@type='submit']",
                    "//input[@type='submit']",
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), 'Sign in')]",
                    "//button[contains(@class, 'login')]",
                    "//button[contains(@class, 'submit')]"
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = self.driver.find_element(By.XPATH, selector)
                        if login_button:
                            break
                    except:
                        continue
                
                if login_button:
                    login_button.click()
                    print("✅ Login button clicked")
                    time.sleep(3)
                    self.logged_in = True
                    return True
                else:
                    print("⚠️ Login button not found")
                    return False
            else:
                print("⚠️ Login fields not found")
                return False
                
        except Exception as e:
            print(f"⚠️ Auto-login failed: {e}")
            return False
    
    def is_microchip(self, number):
        """
        Check if a number sequence is a microchip.

        FIX: Previously required len(number) >= 15, which caused problems
        because the fallback phone regex only captures up to 13 digits,
        so a 15-digit microchip could be truncated to 13 digits and slip
        past this check (starts with '90' but fails the length test),
        then get misfiled as a contact.

        New rule (per your suggestion): ANY digit sequence that starts
        with '90' is treated as a microchip. This is safe for PH data
        because real mobile numbers start with '09', never '90', so
        there's no realistic collision with genuine contact numbers.
        """
        if not number:
            return False
        digits_only = re.sub(r'\D', '', number.strip())
        return digits_only.startswith('90')
    
    def parse_table_by_headers(self, table):
        """
        Parse a v-data-table into a list of {header_text: cell_text} dicts,
        matching each <td> to its column by reading the table's own <thead>
        instead of assuming a fixed cell index.

        WHY: The Contacts table row is [Actions, Name, Mobile, Address].
        Code that hardcodes cells[0]=name, cells[1]=mobile, cells[2]=address
        silently assumes the Actions cell isn't there / doesn't count,
        which is fragile — depending on how the icon-only Actions buttons
        render, the columns can drift by one position. That's exactly why
        'contact_address' was ending up with the Mobile Number instead of
        the real Address: it was reading the wrong column.

        Matching by header text ("Name", "Mobile", "Address", "UID", ...)
        is correct regardless of how many columns exist or where Actions
        sits, so this bug class can't happen again.
        """
        rows_out = []
        thead = table.find('thead')
        if not thead:
            return rows_out
        headers = [th.get_text().strip() for th in thead.find_all('th')]
        
        tbody = table.find('tbody')
        source_rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in source_rows:
            if 'No data available' in row.get_text():
                continue
            cells = row.find_all('td')
            if not cells:
                continue
            row_dict = {}
            for header, cell in zip(headers, cells):
                row_dict[header] = cell.get_text().strip()
            rows_out.append(row_dict)
        return rows_out
    
    def scrape_current_page(self, url=None):
        """Scrape the current page data using the actual HTML structure"""
        if url:
            print(f"🔗 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)
        
        # Get page source and parse with BeautifulSoup
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Reset data
        self.data = {
            'pet_name': '',
            'pet_id': '',
            'birthdate': '',
            'age': '',
            'weight': '',
            'height': '',
            'species': '',
            'animal_type': '',
            'breed': '',
            'gender': '',
            'color': '',
            'coat_remarks': '',
            'privacy': '',
            'pet_status': '',
            'owner_name': '',
            'mobile': '',
            # TWO FULLY SEPARATE ADDRESS COLUMNS — no merging, no fallback,
            # no guessing which one is "real". Each is sourced from exactly
            # one place on the page and shown as-is, even if blank or odd.
            #
            # 'address'          = ADDRESS PANEL only (house_no + city + province)
            # 'contact_address'  = CONTACTS PANEL's own Address column only
            'address': '',
            'house_no': '',
            'city_municipality': '',
            'province': '',
            'contact_address': '',
            'microchip': '',
            'unit_type': '',
            'form_type': '',
            'additional_contacts': ['', '', ''],
            'vaccination_date_1': '',
            'vaccine_type_1': '',
            'vaccine_serial_1': '',  # NEW: Serial column
            'vaccine_lot_1': '',
            'vaccine_expiration_1': '',
            'vaccination_date_2': '',
            'vaccine_type_2': '',
            'vaccine_serial_2': '',  # NEW: Serial column
            'vaccine_lot_2': '',
            'vaccine_expiration_2': '',
            'vaccination_date_3': '',
            'vaccine_type_3': '',
            'vaccine_serial_3': '',  # NEW: Serial column
            'vaccine_lot_3': '',
            'vaccine_expiration_3': ''
        }
        
        # Extract data using the actual HTML structure
        self.extract_from_html(soup)
        
        # Clean up
        self.clean_data()
        
        return self.data
    
    def extract_from_html(self, soup):
        """Extract data using the exact HTML structure from the page"""
        print("\n🔍 Extracting data from HTML structure...")
        
        # ============================================================
        # 1. EXTRACT PET NAME AND ID (from the top section)
        # ============================================================
        print("\n  📋 Extracting Pet Information...")
        
        # Pet Name - from div with class "text-h5 mt-4"
        pet_name_elem = soup.find('div', class_='text-h5 mt-4')
        if pet_name_elem:
            self.data['pet_name'] = pet_name_elem.get_text().strip()
            print(f"    ✅ Pet Name: {self.data['pet_name']}")
        
        # Pet ID - from div with class "text-body-1 text-grey"
        pet_id_elem = soup.find('div', class_='text-body-1 text-grey')
        if pet_id_elem:
            self.data['pet_id'] = pet_id_elem.get_text().strip()
            print(f"    ✅ Pet ID: {self.data['pet_id']}")
        
        # ============================================================
        # 2. EXTRACT PET DETAILS (BirthDate, Age, Weight, etc.)
        # ============================================================
        # Find all divs with class "text-body-1 text-primary" (labels)
        label_elems = soup.find_all('div', class_='text-body-1 text-primary')
        
        for label_elem in label_elems:
            label_text = label_elem.get_text().strip()
            
            # Find the next sibling div with class "text-body-1" (value)
            value_elem = label_elem.find_next_sibling('div', class_='text-body-1')
            if value_elem:
                value = value_elem.get_text().strip()
                
                # Map labels to fields
                if label_text == 'BirthDate':
                    self.data['birthdate'] = value
                    print(f"    ✅ Birthdate: {value}")
                elif label_text == 'Age':
                    self.data['age'] = value
                    print(f"    ✅ Age: {value}")
                elif label_text == 'Weight':
                    self.data['weight'] = value
                    print(f"    ✅ Weight: {value}")
                elif label_text == 'Height':
                    self.data['height'] = value
                    print(f"    ✅ Height: {value}")
                elif label_text == 'Animal':
                    self.data['species'] = value
                    print(f"    ✅ Species: {value}")
                elif label_text == 'Type':
                    self.data['animal_type'] = value
                    print(f"    ✅ Type: {value}")
                elif label_text == 'Breed':
                    self.data['breed'] = value
                    print(f"    ✅ Breed: {value}")
                elif label_text == 'Gender':
                    self.data['gender'] = value
                    print(f"    ✅ Gender: {value}")
                elif label_text == 'Coat(Color)':
                    self.data['color'] = value
                    print(f"    ✅ Color: {value}")
                elif label_text == 'Coat Remarks':
                    self.data['coat_remarks'] = value
                    print(f"    ✅ Coat Remarks: {value}")
                elif label_text == 'Privacy':
                    self.data['privacy'] = value
                    print(f"    ✅ Privacy: {value}")
                elif label_text == 'Pet Status':
                    self.data['pet_status'] = value
                    print(f"    ✅ Pet Status: {value}")
        
        # ============================================================
        # 3. EXTRACT ADDRESS PANEL -> self.data['address']
        #    This is one of two independent address columns. It is
        #    sourced ONLY from the Address panel and is never touched
        #    by the Contacts panel (see section 4's own separate column).
        # ============================================================
        print("\n  📋 Extracting Address Panel...")
        
        # Street address - class "text-body-1 font-weight-medium"
        street_elem = soup.find('div', class_='text-body-1 font-weight-medium')
        if street_elem:
            self.data['house_no'] = street_elem.get_text().strip()
            print(f"    ✅ Street: {self.data['house_no']}")
        
        # City/Barangay and Province - class "text-caption text-grey"
        caption_elems = soup.find_all('div', class_='text-caption text-grey')
        if len(caption_elems) >= 2:
            self.data['city_municipality'] = caption_elems[0].get_text().strip()
            self.data['province'] = caption_elems[1].get_text().strip()
            print(f"    ✅ City: {self.data['city_municipality']}")
            print(f"    ✅ Province: {self.data['province']}")
        
        # Build complete address
        address_parts = []
        if self.data.get('house_no'):
            address_parts.append(self.data['house_no'])
        if self.data.get('city_municipality'):
            address_parts.append(self.data['city_municipality'])
        if self.data.get('province'):
            address_parts.append(self.data['province'])
        
        if address_parts:
            self.data['address'] = ', '.join(address_parts)
            print(f"    ✅ Complete Address: {self.data['address'][:50]}...")
        
        # ============================================================
        # 4. EXTRACT OWNER CONTACTS (from Contacts table)
        # ============================================================
        print("\n  📋 Extracting Owner Contacts...")
        
        # Find the Contacts table section
        contacts_section = soup.find('div', {'data-v-0f58370f': ''})
        if contacts_section:
            # Look for the table with contacts
            table = contacts_section.find('table')
            if table:
                # Parse rows by matching each cell to its column HEADER
                # ("Name", "Mobile", "Address") instead of a fixed index —
                # this is what fixes contact_address showing the phone
                # number: it was previously reading the wrong <td> due to
                # the Actions column shifting positions.
                contact_rows = self.parse_table_by_headers(table)
                
                for row_dict in contact_rows:
                    name = row_dict.get('Name', '').strip()
                    mobile = row_dict.get('Mobile', '').strip()
                    address = row_dict.get('Address', '').strip()
                    
                    # Skip if the number starts with 90 (it's a microchip, not a contact)
                    if self.is_microchip(mobile):
                        # This is actually a microchip, not a contact
                        self.data['microchip'] = mobile
                        print(f"    ✅ Microchip (from contacts): {mobile}")
                        continue
                    
                    # Store the first contact as owner.
                    # 'contact_address' is a fully independent column,
                    # sourced only from this Contacts-panel Address cell.
                    # No merging, no fallback, no validation against
                    # self.data['address'] — literal value, as-is.
                    if not self.data.get('owner_name'):
                        self.data['owner_name'] = name
                        self.data['mobile'] = mobile
                        if address and not self.data.get('contact_address'):
                            self.data['contact_address'] = address
                        print(f"    ✅ Owner Name: {name}")
                        print(f"    ✅ Mobile: {mobile}")
                        print(f"    ✅ Contact Address (Contacts panel): {address}")
                    else:
                        # Additional contacts
                        contact_entry = f"{name} - {mobile}"
                        for i in range(3):
                            if not self.data['additional_contacts'][i]:
                                self.data['additional_contacts'][i] = contact_entry
                                print(f"    ✅ Additional Contact {i+1}: {contact_entry}")
                                break
        
        # If contacts not found in table, try extracting from page text
        if not self.data.get('owner_name'):
            page_text = soup.get_text()
            self.extract_owner_from_text(page_text)
        
        # ============================================================
        # 5. EXTRACT UNITS (Microchip / UID)
        # ============================================================
        print("\n  📋 Extracting Units (Microchip)...")
        
        # Find the Units section
        units_section = soup.find('div', {'data-v-79b41eb1': ''})
        if units_section:
            table = units_section.find('table')
            if table:
                # Header-based lookup (see parse_table_by_headers) instead
                # of fixed indices, for the same reason as the Contacts fix.
                unit_rows = self.parse_table_by_headers(table)
                for row_dict in unit_rows:
                    uid = row_dict.get('UID', '').strip()
                    unit_type = row_dict.get('UnitType', '').strip()
                    form_type = row_dict.get('FormType', '').strip()
                    
                    if uid:
                        self.data['microchip'] = uid
                        self.data['unit_type'] = unit_type
                        self.data['form_type'] = form_type
                        print(f"    ✅ Microchip (UID): {uid}")
                        print(f"    ✅ UnitType: {unit_type}")
                        print(f"    ✅ FormType: {form_type}")
        
        # If not found in table, look for 15-digit numbers starting with 90
        if not self.data.get('microchip'):
            page_text = soup.get_text()
            # Only look for numbers starting with 90
            microchips = re.findall(r'(90\d{13})', page_text)
            if microchips:
                self.data['microchip'] = microchips[0]
                print(f"    ✅ Microchip (from text): {microchips[0]}")
        
        # ============================================================
        # 6. EXTRACT VACCINATIONS (with Serial column)
        # ============================================================
        print("\n  📋 Extracting Vaccinations...")
        
        vax_count = 0
        # Find the Vaccinations section
        vaccines_section = soup.find('div', {'data-v-8ce69eab': ''})
        if vaccines_section:
            table = vaccines_section.find('table')
            if table:
                # Header-based lookup instead of fixed indices.
                vaccine_rows = self.parse_table_by_headers(table)
                for row_dict in vaccine_rows:
                    name = row_dict.get('Name', '').strip()
                    serial = row_dict.get('Serial', '').strip()
                    lot = row_dict.get('Lot', '').strip()
                    application = row_dict.get('Application', '').strip()
                    validity = row_dict.get('Validity', '').strip()
                    
                    vax_count += 1
                    if vax_count <= 3:
                        self.data[f'vaccine_type_{vax_count}'] = name
                        self.data[f'vaccine_serial_{vax_count}'] = serial  # NEW: Serial column
                        self.data[f'vaccine_lot_{vax_count}'] = lot
                        self.data[f'vaccination_date_{vax_count}'] = application
                        self.data[f'vaccine_expiration_{vax_count}'] = validity
                        print(f"    ✅ Vaccination {vax_count}: {name} - Serial: {serial} - Lot: {lot} - Date: {application} - Exp: {validity}")
        
        # If no vaccinations found in table, try to find date patterns
        if vax_count == 0:
            page_text = soup.get_text()
            date_pattern = r'([A-Za-z]{3}\s\d{2},\s\d{4})'
            all_dates = re.findall(date_pattern, page_text)
            
            # Look for date pairs
            date_pairs = re.findall(r'([A-Za-z]{3}\s\d{2},\s\d{4})\s+([A-Za-z]{3}\s\d{2},\s\d{4})', page_text)
            if date_pairs:
                for idx, (date1, date2) in enumerate(date_pairs[:3], 1):
                    # Skip if this is BirthDate
                    if date1 != self.data.get('birthdate'):
                        self.data[f'vaccination_date_{idx}'] = date1
                        self.data[f'vaccine_expiration_{idx}'] = date2
                        print(f"    ✅ Vaccination {idx}: {date1} -> {date2}")
    
    def extract_owner_from_text(self, text):
        """Fallback: Extract owner from text using patterns"""
        print("\n  📋 Extracting Owner from text (fallback)...")
        
        # FIX: widened from \d{11,13} to \d{10,15}. The old 13-digit cap
        # truncated 15-digit microchips (e.g. 900263003845254 ->
        # 9002630038452), which then failed the length-based is_microchip
        # check and got misfiled as a contact. Capturing the full sequence
        # lets is_microchip() correctly recognize it as a microchip instead.
        phone_pattern = r'(\d{10,15})'
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)'
        
        phones = re.findall(phone_pattern, text)
        
        # Exclude common UI words
        exclude_words = ['Actions', 'Action', 'Menu', 'Home', 'Back', 'Next', 'Save', 
                        'Cancel', 'Delete', 'Edit', 'Update', 'Submit', 'Search',
                        'View', 'Print', 'Export', 'Import', 'Settings', 'Profile',
                        'Account', 'Logout', 'Dashboard', 'Reports', 'Help',
                        'Name', 'Mobile', 'Address', 'Contact', 'Phone', 'Email',
                        'Type', 'Form', 'RFID', 'Microchip', 'Pet', 'Animal',
                        'Gender', 'Breed', 'BirthDate', 'Age', 'Weight', 'Coat']
        
        if phones:
            owner_found = False
            for phone in phones:
                # Skip if this is a microchip (starts with 90)
                if self.is_microchip(phone):
                    if not self.data.get('microchip'):
                        self.data['microchip'] = phone
                        print(f"    ✅ Microchip (fallback): {phone}")
                    continue
                
                phone_pos = text.find(phone)
                text_before = text[max(0, phone_pos - 300):phone_pos]
                names_before = re.findall(name_pattern, text_before)
                
                filtered_names = []
                for n in names_before:
                    if n not in exclude_words and len(n.split()) >= 2:
                        filtered_names.append(n)
                
                if filtered_names:
                    full_name = filtered_names[-1].strip()
                    if not owner_found:
                        self.data['owner_name'] = full_name
                        self.data['mobile'] = phone
                        print(f"    ✅ Owner Name (fallback): {full_name}")
                        print(f"    ✅ Mobile (fallback): {phone}")
                        owner_found = True
                    else:
                        contact_entry = f"{full_name} - {phone}"
                        for i in range(3):
                            if not self.data['additional_contacts'][i]:
                                self.data['additional_contacts'][i] = contact_entry
                                print(f"    ✅ Additional Contact {i+1} (fallback): {contact_entry}")
                                break
    
    def clean_data(self):
        """Clean up data"""
        print("\n🧹 Cleaning data...")
        
        # Clean weight - remove 'kg(s)' and extra text
        if self.data.get('weight'):
            weight_match = re.search(r'(\d+\.?\d*)', self.data['weight'])
            if weight_match:
                self.data['weight'] = f"{weight_match.group(1)} kg(s)"
            else:
                self.data['weight'] = ''
        
        # Clean owner_name - remove any 'Actions' if present
        if self.data.get('owner_name') and 'Actions' in self.data['owner_name']:
            self.data['owner_name'] = ''
        
        # Ensure additional_contacts has 3 items
        while len(self.data.get('additional_contacts', [])) < 3:
            self.data['additional_contacts'].append('')
        
        # Fill in missing vaccination fields (including serial)
        for i in range(1, 4):
            fields = ['vaccination_date', 'vaccine_type', 'vaccine_serial', 'vaccine_lot', 'vaccine_expiration']
            for field in fields:
                key = f'{field}_{i}'
                if key not in self.data:
                    self.data[key] = ''
        
        # Ensure contact_address key always exists
        if 'contact_address' not in self.data:
            self.data['contact_address'] = ''
        
        # 'address' (Address panel) is built from its own components only.
        # NO fallback to contact_address, and vice versa — the two columns
        # are completely independent. If the Address panel had no data,
        # 'address' simply stays blank; 'contact_address' is reported
        # separately and independently, whatever it is (even if blank too).
        if not self.data.get('address'):
            address_parts = []
            if self.data.get('house_no'):
                address_parts.append(self.data['house_no'])
            if self.data.get('city_municipality'):
                address_parts.append(self.data['city_municipality'])
            if self.data.get('province'):
                address_parts.append(self.data['province'])
            if address_parts:
                self.data['address'] = ', '.join(address_parts)