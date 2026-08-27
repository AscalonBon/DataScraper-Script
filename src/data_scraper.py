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
    
    def scrape_current_page(self, url=None):
        """Scrape the current page data using exact HTML structure"""
        if url:
            print(f"🔗 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)
        
        # Get page source and parse with BeautifulSoup
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Reset data
        self.data = {
            'owner_name': '',
            'mobile': '',
            'address': '',
            'house_no': '',
            'street': '',
            'barangay': '',
            'city_municipality': '',
            'province': '',
            'birthdate': '',
            'weight': '',
            'color': '',
            'coat_remarks': '',
            'gender': '',
            'microchip': '',
            'pet_name': '',
            'species': '',
            'breed': '',
            'age': '',
            'privacy': '',
            'pet_status': '',
            'additional_contacts': ['', '', ''],
            'vaccination_date_1': '',
            'vaccine_type_1': '',
            'vaccine_lot_1': '',
            'vaccine_expiration_1': '',
            'vaccination_date_2': '',
            'vaccine_type_2': '',
            'vaccine_lot_2': '',
            'vaccine_expiration_2': '',
            'vaccination_date_3': '',
            'vaccine_type_3': '',
            'vaccine_lot_3': '',
            'vaccine_expiration_3': ''
        }
        
        # Extract using exact HTML structure
        self.extract_exact_structure(soup)
        
        # Clean up
        self.clean_data()
        
        return self.data
    
    def extract_exact_structure(self, soup):
        """Extract data using the exact HTML structure provided"""
        print("\n🔍 Extracting data using exact HTML structure...")
        
        # ============================================================
        # 1. Extract Pet Information - div with class="text-body-1 text-primary"
        # ============================================================
        print("\n  📋 Extracting Pet Information...")
        
        # Find all label-value pairs
        label_elements = soup.find_all('div', class_='text-body-1 text-primary')
        
        for label_elem in label_elements:
            label_text = label_elem.get_text().strip()
            
            # Find the next sibling that contains the value
            value_elem = label_elem.find_next_sibling('div', class_='text-body-1')
            if not value_elem:
                value_elem = label_elem.find_next_sibling()
            
            if value_elem:
                value = value_elem.get_text().strip()
                
                # Map labels to fields
                if label_text == 'Pet Name':
                    self.data['pet_name'] = value
                    print(f"    ✅ Pet Name: {value}")
                elif label_text == 'BirthDate':
                    self.data['birthdate'] = value
                    print(f"    ✅ Birthdate: {value}")
                elif label_text == 'Age':
                    self.data['age'] = value
                    print(f"    ✅ Age: {value}")
                elif label_text == 'Weight':
                    self.data['weight'] = value
                    print(f"    ✅ Weight: {value}")
                elif label_text == 'Animal':
                    self.data['species'] = value
                    print(f"    ✅ Species: {value}")
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
        # 2. Extract Address - div with class="text-body-1 font-weight-medium"
        # ============================================================
        print("\n  📋 Extracting Address...")
        
        # Find street address
        street_elem = soup.find('div', class_='text-body-1 font-weight-medium')
        if street_elem:
            self.data['house_no'] = street_elem.get_text().strip()
            print(f"    ✅ House No/Street: {self.data['house_no']}")
        
        # Find city/barangay (text-caption text-grey)
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
        # 3. Extract Owner Name and Mobile from the page
        # ============================================================
        print("\n  📋 Extracting Owner Information...")
        
        # Get all text from the page
        page_text = soup.get_text()
        
        # Look for owner name pattern - name with 2+ parts followed by phone
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)'
        phone_pattern = r'(\d{11,13})'
        
        # Find all phones
        phones = re.findall(phone_pattern, page_text)
        
        # Find all names
        names = re.findall(name_pattern, page_text)
        
        # Filter out common UI words
        exclude_words = ['Actions', 'Action', 'Menu', 'Home', 'Back', 'Next', 'Save', 
                        'Cancel', 'Delete', 'Edit', 'Update', 'Submit', 'Search',
                        'View', 'Print', 'Export', 'Import', 'Settings', 'Profile',
                        'Account', 'Logout', 'Dashboard', 'Reports', 'Help',
                        'Name', 'Mobile', 'Address', 'Contact', 'Phone', 'Email',
                        'Type', 'Form', 'RFID', 'Microchip', 'Pet', 'Animal',
                        'Gender', 'Breed', 'BirthDate', 'Age', 'Weight', 'Coat']
        
        if phones:
            owner_found = False
            
            for i, phone in enumerate(phones):
                # Find position of this phone number
                phone_pos = page_text.find(phone)
                
                # Look for the closest name BEFORE this phone number
                text_before = page_text[max(0, phone_pos - 300):phone_pos]
                names_before = re.findall(name_pattern, text_before)
                
                # Filter out excluded words
                filtered_names = []
                for n in names_before:
                    if n not in exclude_words and len(n.split()) >= 2:
                        filtered_names.append(n)
                
                if filtered_names:
                    full_name = filtered_names[-1].strip()
                    
                    if not owner_found:
                        self.data['owner_name'] = full_name
                        self.data['mobile'] = phone
                        print(f"    ✅ Owner Name: {full_name}")
                        print(f"    ✅ Mobile: {phone}")
                        owner_found = True
                    else:
                        # Additional contact
                        contact_entry = f"{full_name} - {phone}"
                        existing_contacts = [c.split(' - ')[0] for c in self.data['additional_contacts']]
                        if full_name not in existing_contacts and full_name != self.data.get('owner_name', ''):
                            self.data['additional_contacts'].append(contact_entry)
                            print(f"    ✅ Additional Contact: {contact_entry}")
        
        # If owner not found, look for "Name" label
        if not self.data.get('owner_name'):
            name_label = soup.find(string=re.compile(r'^Name$'))
            if name_label:
                parent = name_label.parent
                if parent:
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        name_value = next_sibling.get_text().strip()
                        if name_value and 'Actions' not in name_value and len(name_value.split()) >= 2:
                            self.data['owner_name'] = name_value
                            print(f"    ✅ Owner Name (from label): {name_value}")
        
        # ============================================================
        # 4. Extract Microchip (UID)
        # ============================================================
        print("\n  📋 Extracting Microchip...")
        
        # Look for 15-digit numbers
        microchips = re.findall(r'(\d{15})', page_text)
        if microchips:
            self.data['microchip'] = microchips[0]
            print(f"    ✅ Microchip: {microchips[0]}")
        
        # Look for "UID" label
        uid_label = soup.find(string=re.compile(r'UID', re.IGNORECASE))
        if uid_label:
            parent = uid_label.parent
            if parent:
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    uid_value = next_sibling.get_text().strip()
                    if re.match(r'^\d{15}$', uid_value):
                        self.data['microchip'] = uid_value
                        print(f"    ✅ Microchip (from UID): {uid_value}")
        
        # ============================================================
        # 5. Extract Vaccination Dates
        # ============================================================
        print("\n  📋 Extracting Vaccination Data...")
        
        date_pattern = r'([A-Za-z]{3}\s\d{2},\s\d{4})'
        all_dates = re.findall(date_pattern, page_text)
        
        # Look for date pairs (vaccination date and expiration)
        date_pairs = re.findall(r'([A-Za-z]{3}\s\d{2},\s\d{4})\s+([A-Za-z]{3}\s\d{2},\s\d{4})', page_text)
        
        if date_pairs:
            for idx, (date1, date2) in enumerate(date_pairs[:3], 1):
                # Skip if this is BirthDate
                birthdate = self.data.get('birthdate', '')
                if date1 == birthdate:
                    continue
                    
                self.data[f'vaccination_date_{idx}'] = date1
                self.data[f'vaccine_expiration_{idx}'] = date2
                print(f"    ✅ Vaccination {idx}: {date1} -> {date2}")
        
        # If no date pairs found, try looking for dates in sequence
        if not date_pairs and len(all_dates) >= 2:
            # Skip the first date if it's BirthDate
            start_idx = 0
            if all_dates[0] == self.data.get('birthdate'):
                start_idx = 1
            
            vax_idx = 1
            for i in range(start_idx, len(all_dates) - 1, 2):
                if vax_idx > 3:
                    break
                if i + 1 < len(all_dates):
                    self.data[f'vaccination_date_{vax_idx}'] = all_dates[i]
                    self.data[f'vaccine_expiration_{vax_idx}'] = all_dates[i + 1]
                    print(f"    ✅ Vaccination {vax_idx}: {all_dates[i]} -> {all_dates[i + 1]}")
                    vax_idx += 1
        
        # ============================================================
        # 6. Check for "No data available" in vaccination table
        # ============================================================
        no_data = soup.find('td', string='No data available')
        if no_data:
            print("    ℹ️ No vaccination data available")
        
        # ============================================================
        # 7. Extract Additional Contacts from the page
        # ============================================================
        print("\n  📋 Extracting Additional Contacts...")
        
        # Look for phone numbers not already captured
        if phones:
            contact_idx = 0
            for phone in phones:
                # Skip the main mobile number
                if phone == self.data.get('mobile'):
                    continue
                
                if contact_idx >= 3:
                    break
                
                # Try to find name near this phone
                phone_pos = page_text.find(phone)
                text_before = page_text[max(0, phone_pos - 200):phone_pos]
                names_before = re.findall(name_pattern, text_before)
                
                # Filter out excluded words
                filtered_names = []
                for n in names_before:
                    if n not in exclude_words and len(n.split()) >= 2:
                        filtered_names.append(n)
                
                if filtered_names:
                    contact_name = filtered_names[-1].strip()
                    self.data['additional_contacts'][contact_idx] = f"{contact_name} - {phone}"
                else:
                    self.data['additional_contacts'][contact_idx] = phone
                
                print(f"    ✅ Additional Contact {contact_idx + 1}: {self.data['additional_contacts'][contact_idx]}")
                contact_idx += 1
    
    def clean_data(self):
        """Clean up data"""
        print("\n🧹 Cleaning data...")
        
        # Clean weight - remove 'kg' and extra text
        if self.data.get('weight'):
            weight_match = re.search(r'(\d+\.?\d*)', self.data['weight'])
            if weight_match:
                self.data['weight'] = weight_match.group(1)
            else:
                self.data['weight'] = ''
        
        # If owner_name contains 'Actions', clear it
        if 'Actions' in self.data.get('owner_name', ''):
            self.data['owner_name'] = ''
        
        # Ensure additional_contacts has 3 items
        while len(self.data.get('additional_contacts', [])) < 3:
            self.data['additional_contacts'].append('')
        
        # Fill in missing vaccination fields
        for i in range(1, 4):
            for field in ['vaccination_date', 'vaccine_type', 'vaccine_lot', 'vaccine_expiration']:
                key = f'{field}_{i}'
                if key not in self.data:
                    self.data[key] = ''
        
        # Ensure address components are set
        if not self.data.get('address') and self.data.get('house_no'):
            address_parts = []
            if self.data.get('house_no'):
                address_parts.append(self.data['house_no'])
            if self.data.get('city_municipality'):
                address_parts.append(self.data['city_municipality'])
            if self.data.get('province'):
                address_parts.append(self.data['province'])
            if address_parts:
                self.data['address'] = ', '.join(address_parts)