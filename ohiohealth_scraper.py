#!/usr/bin/env python3
"""
OhioHealth Hospital JSON URL Scraper
Automatically extracts all hospital pricing JSON URLs from the main page
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

class OhioHealthScraper:
    def __init__(self):
        self.base_url = "https://www.ohiohealth.com/billing-insurance/pre-visit-financial-checklist/healthcare-estimates-and-pricing"
        self.hospitals = {}
        self.output_dir = Path("C:\\Users\\Owner\\.openclaw\\workspace-openclaw-ai")
    
    def scrape(self):
        """Scrape the OhioHealth pricing page for hospital JSON URLs"""
        print("[*] Scraping OhioHealth pricing page...")
        print(f"    URL: {self.base_url}\n")
        
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that contain 'json'
            links = soup.find_all('a', href=re.compile(r'\.json$', re.IGNORECASE))
            
            print(f"[OK] Found {len(links)} JSON links\n")
            
            if len(links) == 0:
                print("[WARNING] No JSON links found. Trying alternative parsing...\n")
                self._parse_alternative(response.text)
                return
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and 'standardcharges' in href.lower():
                    # Extract hospital name from link text
                    hospital_name = text.replace(' pricing list ', '').replace('(json)', '').strip()
                    
                    # Make URL absolute if needed
                    if href.startswith('/'):
                        href = 'https://www.ohiohealth.com' + href
                    elif not href.startswith('http'):
                        href = 'https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/' + href
                    
                    self.hospitals[hospital_name] = href
                    print(f"  [{len(self.hospitals):2d}] {hospital_name:<40} {href}")
            
            print(f"\n[OK] Extracted {len(self.hospitals)} hospitals")
            return True
            
        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")
            return False
    
    def _parse_alternative(self, html_content):
        """Alternative parsing method - look for patterns in HTML"""
        print("[*] Using alternative parsing method...")
        
        # Find all URLs matching the pattern
        pattern = r'https://[^\s"\'<>]+standardcharges\.json'
        urls = re.findall(pattern, html_content)
        
        print(f"[OK] Found {len(urls)} URLs\n")
        
        for url in urls:
            # Extract hospital name from URL
            match = re.search(r'([^/]+)_standardcharges\.json', url)
            if match:
                hospital_name = match.group(1)
                hospital_name = hospital_name.replace('_', ' ').title()
                self.hospitals[hospital_name] = url
                print(f"  {hospital_name:<40} {url}")
    
    def save_to_config(self):
        """Save hospital URLs to a config file"""
        config_file = self.output_dir / "ohiohealth_hospitals_urls.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.hospitals, f, indent=2)
            
            print(f"\n[OK] Saved to: {config_file}")
            print(f"    Total hospitals: {len(self.hospitals)}")
            return str(config_file)
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return None
    
    def display_urls(self):
        """Display all URLs in Python dict format for easy copying"""
        print("\n[PYTHON DICT FORMAT]")
        print("hospitals = {")
        for name, url in sorted(self.hospitals.items()):
            print(f'    "{name}": "{url}",')
        print("}")
        
        print("\n[BASH ARRAY FORMAT]")
        print("declare -a hospitals=(")
        for name, url in sorted(self.hospitals.items()):
            print(f'    ["{name}"]= "{url}"')
        print(")")


def main():
    print("\n" + "="*80)
    print("OHIOHEALTH HOSPITAL JSON URL SCRAPER")
    print("="*80 + "\n")
    
    scraper = OhioHealthScraper()
    
    if scraper.scrape():
        scraper.save_to_config()
        scraper.display_urls()
        
        print("\n" + "="*80)
        print("DONE!")
        print("="*80)
        print("\nYou can now use these URLs in the batch parser to extract all hospitals")
    else:
        print("\n[ERROR] Scraping failed. Please manually provide URLs.")


if __name__ == "__main__":
    main()
