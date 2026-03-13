from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

class LinkedInScraper:
    def __init__(self, email=None, password=None):
        # Headless browser setup
        options = Options()
        options.add_argument('--headless')  # Run without opening window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0...')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.email = email
        self.password = password
    
    def login(self):
        """Login to LinkedIn (optional, helps avoid some blocks)"""
        if not self.email or not self.password:
            return
        
        self.driver.get("https://www.linkedin.com/login")
        
        self.driver.find_element(By.ID, "username").send_keys(self.email)
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(3)
    
    def search_jobs(self, keywords="machine learning intern", location="United States"):
        """Search for internship listings"""
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&f_JT=I"
        
        self.driver.get(search_url)
        time.sleep(3)
        
        # Scroll to load more jobs
        jobs = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(3):  # Scroll 3 times
            # Find job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "base-card")
            
            for card in job_cards:
                try:
                    title = card.find_element(By.CLASS_NAME, "base-search-card__title").text
                    company = card.find_element(By.CLASS_NAME, "base-search-card__subtitle").text
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'link': link
                    })
                except:
                    continue
            
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        return jobs
    
    def extract_details(self, job_url):
        """Extract full job details"""
        self.driver.get(job_url)
        time.sleep(2)
        
        try:
            # Click "Show more" if present
            show_more = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Show more')]")
            if show_more:
                show_more[0].click()
                time.sleep(1)
            
            description = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "show-more-less-html__markup"))
            ).text
            
            # Extract skills from description (same method as Indeed)
            skills = self._parse_skills(description)
            
            return {
                'description': description,
                'required_skills': skills['required'],
                'preferred_skills': skills['preferred']
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def _parse_skills(self, text):
        """Same skill extraction logic as Indeed scraper"""
        # ... (reuse the same skill extraction code)
        pass
    
    def close(self):
        self.driver.quit()