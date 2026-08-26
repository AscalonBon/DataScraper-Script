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
from datetime import datetime

class VeterinaryDataScraper:
    def __init__(self, username=None, password=None):
        self.options = Options()
        self.driver = None
        self.data = {}
        self.username = username
        self.password = password
        
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
        
        print(f"🔐 Navigating to {url}...")
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
                    return True
                else:
                    print("⚠️ Login button not found. Please login manually.")
                    return False
            else:
                print("⚠️ Login fields not found. Please login manually.")
                return False
                
        except Exception as e:
            print(f"⚠️ Auto-login failed: {e}")
            print("Please login manually.")
            return False
    
    def manual_login(self, url=None):
        """Manual login fallback"""
        if not url:
            url = "https://app.petdentity.com.ph/session/login"
        
        self.driver.get(url)
        print("\n" + "=" * 70)
        print("🔑 MANUAL LOGIN REQUIRED")
        print("=" * 70)
        print("📌 Please login manually in the Firefox window")
        print("⏳ Press ENTER here when you're logged in and ready to scrape")
        print("=" * 70)
        input()
        return True
    
    def scrape_current_page(self, url=None):
        """Scrape the current page data using direct element finding"""
        if url:
            print(f"🔗 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)
        
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
        
        # Method 1: Find by label text and get the next element's text
        self.extract_by_labels()
        
        # Method 2: Find all text and parse with better logic
        self.extract_from_page_text()
        
        # Clean up empty values
        self.clean_data()
        
        return self.data
    
    def extract_by_labels(self):
        """Extract data by finding label elements and their following siblings"""
        print("\n🔍 Extracting by labels...")
        
        # Label to field mapping
        label_map = {
            'Pet Name': 'pet_name',
            'BirthDate': 'birthdate',
            'Age': 'age',
            'Weight': 'weight',
            'Animal': 'species',
            'Breed': 'breed',
            'Gender': 'gender',
            'Coat(Color)': 'color',
            'Coat Remarks': 'coat_remarks',
            'Privacy': 'privacy',
            'Pet Status': 'pet_status'
        }
        
        for label_text, field_name in label_map.items():
            try:
                # Find element containing the label text
                label_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{label_text}')]")
                for elem in label_elements:
                    # Get the next sibling or following element that contains the value
                    try:
                        # Try next sibling
                        next_elem = elem.find_element(By.XPATH, "./following-sibling::*[1]")
                        value = next_elem.text.strip()
                    except:
                        try:
                            # Try following element
                            next_elem = elem.find_element(By.XPATH, "./following::*[1]")
                            value = next_elem.text.strip()
                        except:
                            continue
                    
                    if value and value != "NaN cm(s)" and value != "No data available":
                        self.data[field_name] = value
                        print(f"  ✅ Found {field_name}: {value}")
                        break
            except Exception as e:
                continue
        
        # Extract Owner Name and Mobile - look for the specific pattern
        try:
            # Look for "Name" label
            name_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Name')]")
            for elem in name_elements:
                try:
                    next_elem = elem.find_element(By.XPATH, "./following-sibling::*[1]")
                    value = next_elem.text.strip()
                    if value and len(value.split()) >= 2 and 'Actions' not in value:
                        self.data['owner_name'] = value
                        print(f"  ✅ Found Owner Name: {value}")
                        break
                except:
                    continue
        except:
            pass
        
        # Extract Mobile - look for 11-13 digit numbers
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            phones = re.findall(r'(\d{11,13})', page_text)
            if phones:
                self.data['mobile'] = phones[0]
                print(f"  ✅ Found Mobile: {phones[0]}")
                
                # Additional contacts
                for i, phone in enumerate(phones[1:4], 1):
                    self.data['additional_contacts'][i-1] = phone
                    print(f"  ✅ Found Additional Contact {i}: {phone}")
        except:
            pass
        
        # Extract Address - look for address patterns
        try:
            # Look for elements with address-like text
            address_found = False
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Unit') or contains(text(), 'Street') or contains(text(), 'Barangay')]")
            for elem in elements:
                text = elem.text.strip()
                if text and len(text) > 20 and ',' in text:
                    # Check if it's an address (contains numbers and words)
                    if re.search(r'\d+', text) and re.search(r'[A-Z]', text):
                        self.data['address'] = text
                        print(f"  ✅ Found Address: {text[:50]}...")
                        address_found = True
                        break
        except:
            pass
        
        # Extract Microchip - look for 15-digit numbers
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            microchips = re.findall(r'(\d{15})', page_text)
            if microchips:
                self.data['microchip'] = microchips[0]
                print(f"  ✅ Found Microchip: {microchips[0]}")
        except:
            pass
    
    def extract_from_page_text(self):
        """Fallback: Parse the page text directly"""
        print("\n🔍 Extracting from page text...")
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            # Look for owner name pattern - a name with 2+ parts followed by a phone number
            for i, line in enumerate(lines):
                # Check if this line looks like a name (2+ words, starts with capital)
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', line):
                    # Check if next line is a phone number
                    if i + 1 < len(lines) and re.match(r'^\d{11,13}$', lines[i+1]):
                        if 'Actions' not in line:
                            self.data['owner_name'] = line
                            self.data['mobile'] = lines[i+1]
                            print(f"  ✅ Found Owner (alt): {line}")
                            print(f"  ✅ Found Mobile (alt): {lines[i+1]}")
                            break
            
            # If address not found, look for it
            if not self.data.get('address'):
                address_pattern = r'(Unit\s+\d+[^,]+,\s+[^,]+,\s+[^,]+)'
                match = re.search(address_pattern, page_text)
                if match:
                    self.data['address'] = match.group(1)
                    print(f"  ✅ Found Address (alt): {self.data['address'][:50]}...")
            
        except Exception as e:
            print(f"  ⚠️ Alt extraction error: {e}")
    
    def clean_data(self):
        """Clean up and ensure all fields have values"""
        print("\n🧹 Cleaning data...")
        
        # If owner_name contains 'Actions', try to get it from page text
        if 'Actions' in self.data.get('owner_name', ''):
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                # Look for a name after "Name" label
                match = re.search(r'Name\s*\n\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', page_text)
                if match:
                    self.data['owner_name'] = match.group(1)
                    print(f"  ✅ Fixed Owner Name: {self.data['owner_name']}")
            except:
                pass
        
        # If owner_name is still 'Actions Name', try harder
        if self.data.get('owner_name') == 'Actions Name' or 'Actions' in self.data.get('owner_name', ''):
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                # Look for a name with 3+ parts that has "V." in it (like "Pilita Remedios V. Venzuela")
                match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+)', page_text)
                if match:
                    self.data['owner_name'] = match.group(1)
                    print(f"  ✅ Fixed Owner Name (V. pattern): {self.data['owner_name']}")
                else:
                    # Try another pattern
                    match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})', page_text)
                    if match:
                        potential = match.group(1)
                        if len(potential.split()) >= 3 and 'Actions' not in potential:
                            self.data['owner_name'] = potential
                            print(f"  ✅ Fixed Owner Name (alt): {self.data['owner_name']}")
            except:
                pass
        
        # Clean weight - remove 'kg' if present
        if self.data.get('weight'):
            self.data['weight'] = re.sub(r'[^0-9.]', '', self.data['weight'])
        
        # Ensure additional_contacts has 3 items
        while len(self.data.get('additional_contacts', [])) < 3:
            self.data['additional_contacts'].append('')