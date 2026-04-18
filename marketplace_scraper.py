#!/usr/bin/env python3
"""
Facebook Marketplace Scraper with Selenium
Monitors for used cars (2010-2015) Toyota, Honda, Lexus under $12,500
in Ohio locations with Telegram notifications.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Selenium not installed!")
    print("Install it with: pip install selenium")
    sys.exit(1)

# Telegram imports
try:
    import requests
except ImportError:
    print("❌ requests library not installed!")
    print("Install it with: pip install requests")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marketplace_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "brands": ["Toyota", "Honda", "Lexus"],
    "year_min": 2010,
    "year_max": 2015,
    "price_max": 12500,
    "locations": ["Columbus", "Johnstown", "Newark", "New Albany"],
    "state": "Ohio",
}

LISTINGS_DB = Path(__file__).parent / "marketplace_listings.json"
CHROME_DRIVER_PATH = r"C:\Users\Owner\Downloads\chromedriver.exe"  # You'll need to set this


class MarketplaceMonitor:
    def __init__(self, config: Dict, db_path: Path):
        self.config = config
        self.db_path = db_path
        self.driver = None
        self.seen_listings = self.load_listings()
        
    def load_listings(self) -> Dict:
        """Load previously seen listings from database."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"listings": []}
        return {"listings": []}
    
    def save_listings(self):
        """Save listings to database."""
        with open(self.db_path, 'w') as f:
            json.dump(self.seen_listings, f, indent=2)
    
    def initialize_driver(self) -> webdriver.Chrome:
        """Initialize Selenium Chrome WebDriver."""
        logger.info("Initializing Chrome WebDriver...")
        
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✓ Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error(f"Make sure ChromeDriver is installed at: {CHROME_DRIVER_PATH}")
            raise
    
    def login_to_facebook(self, username: str, password: str) -> bool:
        """Login to Facebook."""
        try:
            logger.info("Logging into Facebook...")
            self.driver.get("https://www.facebook.com/login/")
            
            wait = WebDriverWait(self.driver, 15)
            time.sleep(2)  # Wait for page to fully load
            
            # Try multiple selectors for username field
            username_field = None
            try:
                username_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            except:
                try:
                    username_field = self.driver.find_element(By.NAME, "email")
                except:
                    try:
                        username_field = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='Email address or phone number']")
                    except:
                        logger.error("Could not find username field")
                        return False
            
            logger.info("Found username field, entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            # Try multiple selectors for password field
            password_field = None
            try:
                password_field = self.driver.find_element(By.ID, "pass")
            except:
                try:
                    password_field = self.driver.find_element(By.NAME, "pass")
                except:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    except:
                        logger.error("Could not find password field")
                        return False
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            logger.info("Submitted login form...")
            # Try multiple selectors for login button
            login_button = None
            try:
                login_button = self.driver.find_element(By.NAME, "login")
            except:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                except:
                    try:
                        # Press Enter instead
                        password_field.submit()
                        time.sleep(5)
                    except:
                        logger.error("Could not find login button")
                        return False
            
            if login_button:
                login_button.click()
            
            # Wait for page to load after login
            time.sleep(8)
            
            # Check if login was successful
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "checkpoint" in current_url:
                logger.error(f"Login may have failed - current URL: {self.driver.current_url}")
                logger.error("Facebook may require checkpoint verification (2FA, security check, etc.)")
                return False
            
            logger.info(f"✓ Successfully logged into Facebook - Current URL: {self.driver.current_url}")
            return True
            
        except TimeoutException:
            logger.error("Timeout during Facebook login")
            return False
        except Exception as e:
            logger.error(f"Error logging into Facebook: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def build_marketplace_url(self, location: str) -> str:
        """Build Facebook Marketplace URL for a location."""
        # This is a template - actual FB Marketplace URLs are complex
        # Format: facebook.com/marketplace/[location]/
        location_clean = location.lower().replace(" ", "-")
        return f"https://www.facebook.com/marketplace/{location_clean}-{self.config['state'].lower()}/"
    
    def scrape_listings(self, url: str) -> List[Dict]:
        """Scrape marketplace listings from a URL."""
        logger.info(f"Scraping: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for page to fully load
            time.sleep(5)
            
            # Try multiple selectors for listing containers
            listing_elements = []
            selectors_to_try = [
                (By.CSS_SELECTOR, "div[data-testid='marketplace_feed_item']"),
                (By.CSS_SELECTOR, "div[role='article']"),
                (By.CSS_SELECTOR, "a[data-testid='marketplace_listing_card']"),
                (By.CSS_SELECTOR, "div.x1iyjqo2"),  # Facebook's dynamic class
                (By.XPATH, "//div[contains(@class, 'x1iyjqo2')]"),
                (By.CSS_SELECTOR, "[data-pagelet]"),
            ]
            
            for selector_type, selector_value in selectors_to_try:
                try:
                    logger.info(f"Trying selector: {selector_type}={selector_value}")
                    listing_elements = self.driver.find_elements(selector_type, selector_value)
                    if len(listing_elements) > 0:
                        logger.info(f"Found {len(listing_elements)} elements with selector: {selector_value}")
                        break
                except:
                    logger.debug(f"Selector failed: {selector_value}")
                    continue
            
            if len(listing_elements) == 0:
                logger.warning(f"No listing elements found with any selector. Trying to extract from page source...")
                # Try to find any links or divs that might be listings
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                listing_elements = [link for link in all_links if "marketplace" in link.get_attribute("href").lower() if link.get_attribute("href")][:10]
                logger.info(f"Found {len(listing_elements)} potential listing links")
            
            listings = []
            
            for element in listing_elements:
                try:
                    listing = self.parse_listing_element(element)
                    if listing and self.matches_criteria(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Error parsing listing element: {e}")
                    continue
            
            logger.info(f"Extracted {len(listings)} matching listings from {len(listing_elements)} elements")
            return listings
            
        except TimeoutException:
            logger.error(f"Timeout loading listings from {url}")
            return []
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def parse_listing_element(self, element) -> Optional[Dict]:
        """Parse individual listing element."""
        try:
            # Get text content
            text_content = element.text
            
            # Try multiple ways to get title
            title = None
            try:
                title = element.find_element(By.CSS_SELECTOR, "h3, h2, [role='heading']").text
            except:
                try:
                    title = element.find_element(By.TAG_NAME, "span").text
                except:
                    title = text_content.split('\n')[0] if text_content else None
            
            if not title or len(title) < 3:
                return None
            
            # Try to find price in text
            price = None
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, "[role='status'], span[aria-label*='$']")
                price_text = price_elem.text
                price = self.extract_price(price_text)
            except:
                # Try to extract price from text content
                import re
                price_match = re.search(r'\$[\d,]+', text_content)
                if price_match:
                    price = self.extract_price(price_match.group())
            
            # Try to get image
            image_url = None
            try:
                img = element.find_element(By.TAG_NAME, "img")
                image_url = img.get_attribute("src")
            except:
                pass
            
            # Try to get URL - multiple approaches
            url = None
            try:
                # Direct link in element
                link = element.find_element(By.TAG_NAME, "a")
                url = link.get_attribute("href")
                if not url or "marketplace" not in url.lower():
                    url = None
            except:
                pass
            
            # Only return if we have at least title and price
            if not title or price is None:
                return None
            
            return {
                "title": title[:100],  # Limit title length
                "price": price,
                "image_url": image_url,
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "location": "Unknown"  # Will be set by caller
            }
        except Exception as e:
            logger.debug(f"Error parsing listing: {e}")
            return None
    
    def extract_price(self, price_text: str) -> Optional[int]:
        """Extract numeric price from price text."""
        import re
        match = re.search(r'\$?([\d,]+)', price_text)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def matches_criteria(self, listing: Dict) -> bool:
        """Check if listing matches search criteria."""
        title = listing.get('title', '').lower()
        price = listing.get('price', float('inf'))
        
        # Check price
        if price > self.config['price_max']:
            return False
        
        # Check brand
        brand_found = any(brand.lower() in title for brand in self.config['brands'])
        if not brand_found:
            return False
        
        # Check year range (look for 4-digit numbers in title)
        import re
        years = re.findall(r'\b(20\d{2}|19\d{2})\b', title)
        if years:
            year = int(years[0])
            if not (self.config['year_min'] <= year <= self.config['year_max']):
                return False
        else:
            # If no year found, skip listing
            return False
        
        return True
    
    def is_new_listing(self, listing: Dict) -> bool:
        """Check if listing is new (not seen before)."""
        listing_id = listing.get('url', listing.get('title'))
        
        for seen in self.seen_listings.get('listings', []):
            if seen.get('url') == listing.get('url'):
                return False
        
        return True
    
    def add_to_seen(self, listing: Dict):
        """Add listing to seen listings."""
        if 'listings' not in self.seen_listings:
            self.seen_listings['listings'] = []
        
        self.seen_listings['listings'].append(listing)
        
        # Keep only last 30 days
        cutoff_time = datetime.now() - timedelta(days=30)
        self.seen_listings['listings'] = [
            l for l in self.seen_listings['listings']
            if datetime.fromisoformat(l.get('scraped_at', '')) > cutoff_time
        ]
        
        self.save_listings()
    
    def run_check(self, fb_username: str = None, fb_password: str = None) -> List[Dict]:
        """Run a complete marketplace check."""
        logger.info("=" * 60)
        logger.info("Starting marketplace check")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        all_new_listings = []
        
        try:
            self.driver = self.initialize_driver()
            
            # Login to Facebook if credentials provided
            if fb_username and fb_password:
                login_success = self.login_to_facebook(fb_username, fb_password)
                if not login_success:
                    logger.warning("Facebook login failed, attempting to scrape without login...")
            
            for location in self.config['locations']:
                url = self.build_marketplace_url(location)
                logger.info(f"\nChecking {location}, Ohio...")
                
                listings = self.scrape_listings(url)
                
                # Filter to new listings only
                new_listings = [l for l in listings if self.is_new_listing(l)]
                logger.info(f"Found {len(new_listings)} new listings in {location}")
                
                for listing in new_listings:
                    listing['location'] = location
                    self.add_to_seen(listing)
                    all_new_listings.append(listing)
                
                # Be nice to Facebook servers
                time.sleep(3)
        
        except Exception as e:
            logger.error(f"Error during check: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return all_new_listings
    
    def send_email_notification(self, listings: List[Dict], sender_email: str, sender_password: str, recipient_email: str):
        """Send notification via email."""
        if not listings:
            logger.info("No new listings to report")
            return
        
        try:
            logger.info(f"Sending email to {recipient_email}...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚗 Found {len(listings)} NEW Marketplace Vehicles!"
            msg['From'] = sender_email
            msg['To'] = recipient_email
            
            # Create HTML version of email
            html = self.format_email_html(listings)
            
            part = MIMEText(html, 'html')
            msg.attach(part)
            
            # Send email via Gmail
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"✓ Email sent to {recipient_email} ({len(listings)} listings)")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def send_telegram_notification(self, listings: List[Dict], telegram_token: str, chat_id: str):
        """Send notification to Telegram."""
        if not listings:
            logger.info("No new listings to report")
            return
        
        message = self.format_notification(listings)
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✓ Telegram notification sent ({len(listings)} listings)")
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def format_notification(self, listings: List[Dict]) -> str:
        """Format listings for Telegram notification."""
        message = f"🚗 *Found {len(listings)} NEW matching vehicles!*\n\n"
        
        # Sort by price (best deals first)
        sorted_listings = sorted(listings, key=lambda x: x.get('price', float('inf')))
        
        for i, listing in enumerate(sorted_listings[:5], 1):
            message += f"*{i}. {listing.get('title')}*\n"
            message += f"💰 Price: ${listing.get('price', 'N/A'):,}\n"
            message += f"📍 Location: {listing.get('location')}\n"
            
            if listing.get('url'):
                message += f"🔗 [View Listing]({listing.get('url')})\n"
            
            message += "\n"
        
        message += f"⏰ Check completed: {datetime.now().strftime('%I:%M %p')}"
        
        return message
    
    def format_email_html(self, listings: List[Dict]) -> str:
        """Format listings as HTML email."""
        # Sort by price (best deals first)
        sorted_listings = sorted(listings, key=lambda x: x.get('price', float('inf')))
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1f77f3; text-align: center;">🚗 Found {len(listings)} NEW Matching Vehicles!</h2>
                    <p style="text-align: center; color: #666;">Matching your criteria: Toyota/Honda/Lexus, 2010-2015, Under $12,500</p>
                    <hr style="border: none; border-top: 2px solid #1f77f3;">
        """
        
        for i, listing in enumerate(sorted_listings[:10], 1):
            price = listing.get('price', 'N/A')
            if isinstance(price, int):
                price = f"${price:,}"
            
            html += f"""
                    <div style="border-left: 4px solid #1f77f3; padding: 15px; margin: 15px 0; background-color: #f9f9f9;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{i}. {listing.get('title', 'Unknown')}</h3>
                        <p style="margin: 5px 0; color: #666;">
                            <strong>💰 Price:</strong> {price}<br>
                            <strong>📍 Location:</strong> {listing.get('location', 'Unknown')}<br>
                            <strong>⏰ Posted:</strong> {listing.get('scraped_at', 'Unknown')[:10]}
                        </p>
            """
            
            if listing.get('url'):
                html += f"""
                        <a href="{listing.get('url')}" style="display: inline-block; background-color: #1f77f3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 10px;">View Listing on Facebook</a>
                """
            
            html += """
                    </div>
            """
        
        html += f"""
                    <hr style="border: none; border-top: 2px solid #1f77f3;">
                    <p style="text-align: center; color: #999; font-size: 12px;">
                        Check completed: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}<br>
                        Next check: Every 4 hours (8 AM - 8 PM)
                    </p>
                </div>
            </body>
        </html>
        """
        
        return html


def main():
    """Main entry point."""
    logger.info("Marketplace Monitor Starting...")
    
    # Check for required tools
    if not Path(CHROME_DRIVER_PATH).exists():
        logger.error(f"ChromeDriver not found at: {CHROME_DRIVER_PATH}")
        logger.error("Please download ChromeDriver from: https://chromedriver.chromium.org/")
        logger.error("Make sure it matches your Chrome version")
        sys.exit(1)
    
    monitor = MarketplaceMonitor(CONFIG, LISTINGS_DB)
    
    # Get Facebook credentials from environment
    fb_username = os.environ.get('FB_USERNAME')
    fb_password = os.environ.get('FB_PASSWORD')
    
    if not fb_username or not fb_password:
        logger.warning("Facebook credentials not set. Set FB_USERNAME and FB_PASSWORD environment variables for better results")
    
    # Get email credentials from environment
    email_sender = os.environ.get('EMAIL_SENDER')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_recipient = "funeraldirector@columbus.rr.com"  # Default recipient
    
    if not email_sender or not email_password:
        logger.warning("Email credentials not set. Set EMAIL_SENDER and EMAIL_PASSWORD environment variables")
    
    # Run check with Facebook credentials
    new_listings = monitor.run_check(fb_username, fb_password)
    
    # Send email notification if we have new listings and credentials
    if email_sender and email_password:
        monitor.send_email_notification(new_listings, email_sender, email_password, email_recipient)
    else:
        # Just log them
        if new_listings:
            logger.info(f"Found {len(new_listings)} new listings (Email not configured)")
            for listing in new_listings:
                logger.info(f"  - {listing.get('title')} - ${listing.get('price', 'N/A'):,}")
    
    logger.info("Check completed")


if __name__ == "__main__":
    main()
