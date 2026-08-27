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
            'vaccine_serial_1': '',
            'vaccine_lot_1': '',
            'vaccine_expiration_1': '',
            'vaccination_date_2': '',
            'vaccine_type_2': '',
            'vaccine_serial_2': '',
            'vaccine_lot_2': '',
            'vaccine_expiration_2': '',
            'vaccination_date_3': '',
            'vaccine_type_3': '',
            'vaccine_serial_3': '',
            'vaccine_lot_3': '',
            'vaccine_expiration_3': ''
        }

        # Extract using exact HTML structure
        self.extract_exact_structure(soup)

        # Clean up
        self.clean_data()

        return self.data

    def get_section_card(self, soup, title):
        """
        Each panel (profile / address / Contacts / Vaccinations / Units) is a
        header button followed by a sibling '.v-sheet' content div:

            <div class="v-row v-row--dense">
                <button>...<div class="px-2">{title}</div></button>
            </div>
            <div class="v-sheet ... outlined">  <-- this is what we return

        Scoping every extraction to the card returned here is what prevents
        values from one section (e.g. a vaccine's Serial number) from ever
        being read as if they belonged to another section (e.g. Contacts).
        Returns None if that section isn't present on the page.
        """
        label_div = soup.find(
            'div',
            class_=lambda c: c and 'px-2' in c.split(),
            string=lambda s: s and s.strip() == title
        )
        if not label_div:
            print(f"  ⚠️ Section '{title}' not found on this page")
            return None

        row = label_div.find_parent(
            'div',
            class_=lambda c: c and 'v-row' in c.split() and 'v-row--dense' in c.split()
        )
        if not row:
            return None

        return row.find_next_sibling('div', class_=lambda c: c and 'v-sheet' in c.split())

    def extract_exact_structure(self, soup):
        """Extract data using section-scoped selectors (never whole-page regex)"""
        print("\n🔍 Extracting data by section...")
        self.extract_profile(soup)
        self.extract_address(soup)
        self.extract_contacts(soup)
        self.extract_vaccinations(soup)
        self.extract_microchip(soup)

    def extract_profile(self, soup):
        """
        Profile card is pairs of:
            <div class="text-body-1 text-primary"> Label </div>
            <div class="text-body-1">Value</div>
        """
        print("\n  📋 Extracting Pet Information...")
        card = self.get_section_card(soup, 'profile')
        if not card:
            return

        label_map = {
            'Pet Name': 'pet_name', 'BirthDate': 'birthdate', 'Age': 'age',
            'Weight': 'weight', 'Animal': 'species', 'Breed': 'breed',
            'Gender': 'gender', 'Coat(Color)': 'color', 'Coat Remarks': 'coat_remarks',
            'Privacy': 'privacy', 'Pet Status': 'pet_status',
        }

        labels = card.find_all(
            'div', class_=lambda c: c and 'text-body-1' in c.split() and 'text-primary' in c.split()
        )
        for label_elem in labels:
            label_text = label_elem.get_text(strip=True)
            field = label_map.get(label_text)
            if not field:
                continue
            value_elem = label_elem.find_next_sibling('div')
            if not value_elem:
                continue
            value = value_elem.get_text(strip=True)
            if value and value.lower() not in ('nan kg(s)', '- cm(s)', 'not found', '-'):
                self.data[field] = value
                print(f"    ✅ {field}: {value}")

    def extract_address(self, soup):
        """
        Address card is:
            <div class="text-body-1 font-weight-medium">Street</div>
            <div class="text-caption text-grey">Barangay/City</div>
            <div class="text-caption text-grey">Province, Postal</div>
        """
        print("\n  📋 Extracting Address...")
        card = self.get_section_card(soup, 'address')
        if not card:
            return

        street_elem = card.find(
            'div', class_=lambda c: c and 'text-body-1' in c.split() and 'font-weight-medium' in c.split()
        )
        street = street_elem.get_text(strip=True) if street_elem else ''

        grey_elems = card.find_all(
            'div', class_=lambda c: c and 'text-caption' in c.split() and 'text-grey' in c.split()
        )
        grey_lines = [el.get_text(strip=True) for el in grey_elems if el.get_text(strip=True)]

        self.data['house_no'] = street
        if len(grey_lines) >= 1:
            self.data['city_municipality'] = grey_lines[0]
        if len(grey_lines) >= 2:
            self.data['province'] = grey_lines[1]

        parts = [p for p in ([street] + grey_lines) if p]
        if parts:
            self.data['address'] = ', '.join(parts)
            print(f"    ✅ Complete Address: {self.data['address'][:50]}...")

    def extract_contacts(self, soup):
        """
        Contacts card table columns: Actions | Name | Mobile | Address.
        Scoped strictly to this table's rows, so a vaccine's name/serial
        pair (from a different table entirely) can never end up here.
        """
        print("\n  📋 Extracting Contacts...")
        card = self.get_section_card(soup, 'Contacts')
        if not card:
            return

        rows = card.select('table tbody tr.v-data-table__tr')
        contacts = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            name = cells[1].get_text(strip=True)
            mobile = cells[2].get_text(strip=True)
            if name or mobile:
                contacts.append((name, mobile))

        if contacts:
            self.data['owner_name'], self.data['mobile'] = contacts[0]
            print(f"    ✅ Owner Name: {contacts[0][0]}")
            print(f"    ✅ Mobile: {contacts[0][1]}")
            for i, (name, mobile) in enumerate(contacts[1:4], 0):
                self.data['additional_contacts'][i] = f"{name} - {mobile}" if name else mobile
                print(f"    ✅ Additional Contact {i + 1}: {self.data['additional_contacts'][i]}")

    def extract_vaccinations(self, soup):
        """
        Vaccinations card table columns: Actions | Name | Serial | Lot | Application | Validity.
        Scoped strictly to this table, so its Serial/Name values never leak
        into Contacts or Microchip.
        """
        print("\n  📋 Extracting Vaccination Data...")
        card = self.get_section_card(soup, 'Vaccinations')
        if not card:
            return

        rows = card.select('table tbody tr.v-data-table__tr')
        if not rows:
            print("    ℹ️ No vaccination data available")
            return

        for i, row in enumerate(rows[:3], 1):
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            self.data[f'vaccine_type_{i}'] = cells[1].get_text(strip=True)
            self.data[f'vaccine_serial_{i}'] = cells[2].get_text(strip=True)
            self.data[f'vaccine_lot_{i}'] = cells[3].get_text(strip=True)
            self.data[f'vaccination_date_{i}'] = cells[4].get_text(strip=True)
            self.data[f'vaccine_expiration_{i}'] = cells[5].get_text(strip=True) if len(cells) > 5 else ''
            print(f"    ✅ Vaccine {i}: {self.data[f'vaccine_type_{i}']} "
                  f"(serial {self.data[f'vaccine_serial_{i}']})")

    def extract_microchip(self, soup):
        """
        Units card table columns: Actions | UID | UnitType | FormType.
        Microchip is the UID of the row whose FormType is 'Microchip' —
        identified by which table/column it came from, not by a digit prefix.
        """
        print("\n  📋 Extracting Microchip...")
        card = self.get_section_card(soup, 'Units')
        if not card:
            return

        rows = card.select('table tbody tr.v-data-table__tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4 and 'microchip' in cells[3].get_text(strip=True).lower():
                self.data['microchip'] = cells[1].get_text(strip=True)
                print(f"    ✅ Microchip: {self.data['microchip']}")
                break

    def clean_data(self):
        """Clean up data"""
        print("\n🧹 Cleaning data...")

        # Clean weight - strip stray text, keep the number, then add a consistent unit
        if self.data.get('weight'):
            weight_match = re.search(r'(\d+\.?\d*)', self.data['weight'])
            if weight_match:
                self.data['weight'] = f"{weight_match.group(1)} kg(s)"
            else:
                self.data['weight'] = ''

        # Ensure additional_contacts always has exactly 3 slots
        while len(self.data.get('additional_contacts', [])) < 3:
            self.data['additional_contacts'].append('')

        # Fill in missing vaccination fields
        for i in range(1, 4):
            for field in ['vaccination_date', 'vaccine_type', 'vaccine_serial', 'vaccine_lot', 'vaccine_expiration']:
                key = f'{field}_{i}'
                if key not in self.data:
                    self.data[key] = ''