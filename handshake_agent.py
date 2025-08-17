from typing import List
from logger import logger
import os
import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from login_helpers import save_cookies, load_cookies
# # Helper Functions
# def save_cookies(driver, filename):
#     with open(filename, 'wb') as filehandler:
#         pickle.dump(driver.get_cookies(), filehandler)

# def load_cookies(driver, filename, url):
#     driver.get(url)
#     with open(filename, 'rb') as cookiesfile:
#         cookies = pickle.load(cookiesfile)
#         for cookie in cookies:
#             driver.add_cookie(cookie)
            
class HandshakeJobAgent:
    def __init__(self,  config):
        # self.google_sheet_url = google_sheet_url
        self.fernet_key = config["FERNET_KEY"]
        self.credentials_path = config["CREDENTIALS_PATH"]
        self.school_email = config["SCHOOL_EMAIL"]
        self.school_name = config["SCHOOL_NAME"]
        self.driver = None
        self.gc = None 
        self.worksheet = None
        self.setup_driver()
        # self.setup_google_sheets()
        
    def setup_driver(self):
        """Initialize Chrome driver with webdriver-manager. webdriver-manager handles chrome updates. 
        
        - initializes self.driver with path to chrome driver. 
        - updates chrome options
        """
        
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Find chromedriver for the version of chrome installed
        # Set up service with path to chrome driver binary
        service = Service(ChromeDriverManager().install())
        
        # Use service to start up chrome window 
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def login_to_handshake(self):
        cookies_file = "handshake_cookies.pkl"
        handshake_url = "https://ucdavis.joinhandshake.com"

        if os.path.exists(cookies_file):
            # self.driver.get(handshake_url)
            self.driver.get("https://ucdavis.joinhandshake.com/login")
            load_cookies(self.driver, cookies_file, handshake_url)
            self.driver.refresh()
            logger.info("Loaded cookies — should already be logged in")
            # print(self.driver.current_url)
        else:
            logger.info("No saved cookies. Performing manual login...")
            self.driver.get("https://ucdavis.joinhandshake.com/login")
            input("Complete login in the browser, then press Enter here...")
            save_cookies(self.driver, cookies_file)
            logger.info("Cookies saved for next login")
         
    def scrape_job_listings(self, limit=10):
        base_domain = self.driver.current_url.split("/")[2]
        jobs_url = f"https://{base_domain}/job-search?page=1&per_page=25"
        self.driver.get(jobs_url)
        logger.info(f"Navigated to jobs page: {jobs_url}")

        # Wait for at least one job card
        job_cards = WebDriverWait(self.driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '[data-hook^="job-result-card"]')
            )
        )

        results = []
        seen_ids = set()
        last_height = 0

        while len(results) < limit:
            # Get all visible job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-hook^="job-result-card"]')

            for job in job_cards:
                try:
                    job_id = job.get_attribute("data-hook").split("|")[1].strip()
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    company = job.find_element(By.CSS_SELECTOR, 'span.sc-cMCtBX').text.strip()
                    title = job.find_element(By.CSS_SELECTOR, 'div.sc-hnLruu').text.strip()
                    link = job.find_element(By.TAG_NAME, "a").get_attribute("href")

                    results.append({"id": job_id, "title": title, "company": company, "link": link})

                    logger.info(f"id: {job_id} | title: {title} | company: {company} | link: {link}")

                    if len(results) >= limit:
                        break
                except Exception as e:
                    logger.warning(f"Could not parse job card: {e}")

            if len(results) >= limit:
                break

            # Scroll down to load more
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Check if scroll height changes 
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("No more jobs to load.")
                break
            last_height = new_height

        logger.info(f"Scraped {len(results)} jobs")
        logger.info("===== All jobs scraped =====")
        for job in results:
            logger.info(f"{job['id']} | {job['title']} | {job['company']} | {job['link']}")

        return results
            
    def run_agent(self, search_keywords: List[str] = None, limit: int = 10):
        """Main method to run the job scraping agent"""
        try:
            logger.info("Starting Handshake Job Agent")
            
            # Login to Handshake
            self.login_to_handshake()
            
            current_url = self.driver.current_url
            print(f"Logged in at: {current_url}")


            # Scrape job listings
            # jobs = self.scrape_job_listings(search_keywords, limit)
            jobs = self.scrape_job_listings(limit)
            logger.info(f"Scraped {len(jobs)} jobs")
            
            # Update Google Sheet
            if jobs:
                self.update_google_sheet_with_jobs(jobs)
            
            logger.info("Job agent completed successfully")
            
        except Exception as e:
            logger.error(f"Error running job agent: {e}")
        finally:
            if self.driver:
                self.driver.quit()

