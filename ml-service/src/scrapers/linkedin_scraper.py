from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import csv
import re
import json

# ==================== CONFIG ====================

JOB_KEYWORDS = [
    "machine learning intern",
    "data science intern", 
    "software engineer intern",
    "backend developer intern",
    "frontend developer intern",
    "project manager intern",
    "product manager intern",
    "data analyst intern"
]

COUNTRIES = [
    "United States",
    "Canada",
    "United Kingdom",
    "Australia",
    "Germany",
    "France",
    "Japan",
]
MAX_JOBS_PER_KEYWORD = 100     # Limit for testing
DATE_POSTED = "month"          # "any", "24h", "week", "month"

# Filter codes
EXPERIENCE_LEVELS = ["1"]      # 1 = Internship
WORKPLACE_TYPES = []           # 1=On-site, 2=Remote, 3=Hybrid

# Scroll settings
MAX_SCROLL_ATTEMPTS = 50       # Reduced for stability
SCROLL_PAUSE = 3               # Seconds between scrolls
DETAIL_PAUSE = 2               # Seconds to load job details

# ==================== SKILL DATABASE ====================

TECH_SKILLS = {
    # Programming Languages
    'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'c++', 'c#', 
    'go', 'rust', 'scala', 'r', 'matlab', 'julia', 'php', 'ruby', 'swift',
    
    # Data/ML
    'sql', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly',
    'tensorflow', 'tf', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
    'xgboost', 'lightgbm', 'catboost', 'spacy', 'nltk', 'hugging face',
    'transformers', 'opencv', 'mlflow', 'kubeflow',
    
    # ML Concepts
    'machine learning', 'deep learning', 'neural networks', 'nlp', 
    'computer vision', 'cv', 'reinforcement learning', 'statistics',
    'a/b testing', 'experimental design', 'time series', 'forecasting',
    
    # Big Data
    'spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'snowflake', 'bigquery',
    'databricks', 'hive', 'presto',
    
    # Databases
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
    'dynamodb', 'sqlite', 'firebase', 'supabase',
    
    # Cloud/DevOps
    'aws', 'gcp', 'google cloud', 'azure', 'docker', 'kubernetes', 'k8s',
    'terraform', 'jenkins', 'github actions', 'gitlab ci', 'circleci',
    'prometheus', 'grafana', 'nginx',
    
    # Web/Frameworks
    'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'django',
    'flask', 'fastapi', 'spring boot', 'express', 'nodejs', 'graphql',
    'rest api', 'html', 'css', 'tailwind', 'bootstrap',
    
    # Tools/Other
    'git', 'github', 'linux', 'bash', 'jupyter', 'tableau', 'powerbi',
    'excel', 'figma', 'postman', 'selenium', 'pytest', 'unittest'
}

PREFERRED_INDICATORS = [
    'preferred', 'plus', 'nice to have', 'bonus', 'desired', 
    'familiarity with', 'exposure to', 'knowledge of'
]

# ==================== SETUP ====================

def setup_driver():
    """Configure and return Chrome driver"""
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Uncomment after testing
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    return webdriver.Chrome(options=options)


# ==================== URL BUILDER ====================

def build_linkedin_url(keyword, location, exp_levels, workplace_types, date_posted):
    """Construct LinkedIn search URL with filters"""
    
    base = "https://www.linkedin.com/jobs/search/"
    params = [f"?keywords={quote_plus(keyword)}"]
    params.append(f"&location={quote_plus(location)}")
    
    if exp_levels:
        params.append(f"&f_E={','.join(exp_levels)}")
    if workplace_types:
        params.append(f"&f_WT={','.join(workplace_types)}")
    
    # Date posted filter
    date_codes = {"24h": "r86400", "week": "r604800", "month": "r2592000"}
    if date_posted in date_codes:
        params.append(f"&f_TPR={date_codes[date_posted]}")
    
    params.append("&position=1&pageNum=0")
    
    return base + "".join(params)


# ==================== SCROLLING ====================

def scroll_page(driver, max_attempts=MAX_SCROLL_ATTEMPTS):
    """Scroll to load all job cards"""
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    attempts = 0
    
    while attempts < max_attempts:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        
        # Click "Show more" if present
        try:
            show_more = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "infinite-scroller__show-more-button"))
            )
            show_more.click()
            time.sleep(SCROLL_PAUSE)
        except:
            pass
        
        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
            
        last_height = new_height
        attempts += 1
    
    print(f"  Scrolled {attempts} times")


# ==================== SKILL EXTRACTION ====================

def extract_skills_from_text(text):
    """
    Extract and categorize skills from job description
    Returns: {'required': [], 'preferred': []}
    """
    if not text:
        return {'required': [], 'preferred': []}
    
    lines = text.split('\n')
    
    required_skills = set()
    preferred_skills = set()
    
    # Find "Requirements" or "Qualifications" section
    in_requirements = False
    in_preferred = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Detect section headers
        if any(x in line_lower for x in ['requirement', 'qualification', 'what you need', 'must have']):
            in_requirements = True
            in_preferred = False
            continue
            
        if any(x in line_lower for x in ['preferred', 'nice to have', 'plus', 'bonus', 'beneficial']):
            in_requirements = False
            in_preferred = True
            continue
            
        if any(x in line_lower for x in ['responsibility', 'what you will do', 'benefit']):
            in_requirements = False
            in_preferred = False
            continue
        
        # Check for preferred indicators in line
        is_preferred_line = any(ind in line_lower for ind in PREFERRED_INDICATORS)
        
        # Extract skills from this line
        found_skills = set()
        for skill in TECH_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, line_lower):
                found_skills.add(skill)
        
        # Categorize based on context
        for skill in found_skills:
            if in_preferred or is_preferred_line:
                preferred_skills.add(skill)
            elif in_requirements:
                required_skills.add(skill)
            else:
                # Default: if in first half of description, likely required
                # This is a heuristic
                required_skills.add(skill)
    
    # Post-processing: clean up
    # Remove 'tf' if 'tensorflow' present, etc.
    final_required = clean_skill_set(required_skills)
    final_preferred = clean_skill_set(preferred_skills - required_skills)
    
    return {
        'required': sorted(list(final_required)),
        'preferred': sorted(list(final_preferred))
    }
def clean_skill_set(skills):
    """Remove duplicates and normalize skill names"""
    cleaned = set()
    
    # Mapping for normalization
    normalize = {
        'tf': 'tensorflow',
        'sklearn': 'scikit-learn',
        'cv': 'computer vision',
        'k8s': 'kubernetes',
        'js': 'javascript',
        'ts': 'typescript',
        'gcp': 'google cloud',
        'rest api': 'api'
    }
    
    for skill in skills:
        # Skip if longer form exists
        if skill == 'tf' and 'tensorflow' in skills:
            continue
        if skill == 'sklearn' and 'scikit-learn' in skills:
            continue
            
        normalized = normalize.get(skill, skill)
        cleaned.add(normalized)
    
    return cleaned


def infer_experience_level(text):
    """Infer experience level from description"""
    text_lower = text.lower()
    
    # Education indicators
    education = []
    if any(x in text_lower for x in ['phd', 'ph.d', 'doctorate']):
        education.append('PhD')
    if any(x in text_lower for x in ['master', 'ms ', 'm.s', 'mba']):
        education.append('Masters')
    if any(x in text_lower for x in ['bachelor', 'bs ', 'b.s', 'ba ', 'b.a', 'undergraduate']):
        education.append('Bachelors')
    
    # Years of experience
    years = []
    patterns = [
        r'(\d+)\+?\s*years?.*experience',
        r'(\d+)\+?\s*yrs?.*experience',
        r'experience.*(\d+)\+?\s*years?'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        years.extend([int(m) for m in matches])
    
    max_years = max(years) if years else 0
    
    return {
        'education_required': education if education else ['Not Specified'],
        'years_experience': max_years,
        'is_new_grad_friendly': max_years <= 1 or 'new grad' in text_lower
    }


# ==================== JOB DETAIL FETCHING ====================

def fetch_job_details(driver, job_url):
    """Extract structured data from individual job page"""
    
    if not job_url:
        return None
    
    try:
        driver.get(job_url)
        time.sleep(DETAIL_PAUSE)
        
        # Wait for description to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "description__text"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Job description
        desc_div = soup.find("div", class_="description__text")
        job_description = desc_div.get_text(separator="\n", strip=True) if desc_div else ""
        
        # Company description (optional)
        company_div = soup.find("div", class_="show-more-less-html__markup")
        company_description = company_div.get_text(separator="\n", strip=True) if company_div else ""
        
        # Seniority level (if available)
        try:
            seniority = soup.find("span", class_="job-posting-benefits__text")
            seniority_text = seniority.text.strip() if seniority else ""
        except:
            seniority_text = ""
        
        # Extract structured data
        skills = extract_skills_from_text(job_description)
        exp_info = infer_experience_level(job_description)
        
        return {
            'job_description': job_description,
            'company_description': company_description,
            'seniority_level': seniority_text,
            'required_skills': skills['required'],
            'preferred_skills': skills['preferred'],
            'education_required': exp_info['education_required'],
            'years_experience': exp_info['years_experience'],
            'new_grad_friendly': exp_info['is_new_grad_friendly']
        }
        
    except Exception as e:
        print(f"    ⚠️ Error fetching details: {e}")
        return None


# ==================== MAIN SCRAPING ====================

def scrape_linkedin_jobs():
    """Main scraping function"""
    
    driver = setup_driver()
    all_jobs = []
    
    try:
        for keyword in JOB_KEYWORDS:
            print(f"\n{'='*60}")
            print(f"🔍 Searching: {keyword}")
            print(f"{'='*60}")
            
            for country in COUNTRIES:
                url = build_linkedin_url(
                    keyword, country, 
                    EXPERIENCE_LEVELS, WORKPLACE_TYPES, DATE_POSTED
                )
                print(f"\n📍 Location: {country}")
                print(f"🔗 {url[:80]}...")
                
                driver.get(url)
                time.sleep(3)
                
                # Scroll to load jobs
                scroll_page(driver)
                
                # Parse job cards
                soup = BeautifulSoup(driver.page_source, "html.parser")
                job_cards = soup.find_all("div", class_="base-card")
                
                print(f"  Found {len(job_cards)} job cards")
                
                # Process each job
                for idx, card in enumerate(job_cards[:MAX_JOBS_PER_KEYWORD]):
                    
                    # Extract basic info from card
                    a_tag = card.find("a", class_="base-card__full-link")
                    job_url = a_tag["href"].split('?')[0] if a_tag else ""  # Clean URL
                    
                    # Job title
                    title_span = a_tag.find("span", class_="sr-only") if a_tag else None
                    job_title = title_span.text.strip() if title_span else ""
                    
                    # Company
                    company_tag = card.find("h4", class_="base-search-card__subtitle")
                    company_a = company_tag.find("a") if company_tag else None
                    company_name = company_a.text.strip() if company_a else ""
                    
                    # Location
                    location_tag = card.find("span", class_="job-search-card__location")
                    location = location_tag.text.strip() if location_tag else ""
                    
                    # Posted date
                    posted_tag = card.find("time", class_="job-search-card__listdate")
                    posted = posted_tag.text.strip() if posted_tag else ""
                    
                    print(f"  [{idx+1}/{min(len(job_cards), MAX_JOBS_PER_KEYWORD)}] {job_title[:50]}...")
                    
                    # Fetch detailed info
                    details = fetch_job_details(driver, job_url)
                    
                    if details:
                        job_record = {
                            'search_keyword': keyword,
                            'role': job_title,
                            'company': company_name,
                            'location': location,
                            'posted': posted,
                            'country': country,
                            
                            # Structured skills (YOUR PROJECT NEEDS THIS)
                            'required_skills': json.dumps(details['required_skills']),
                            'preferred_skills': json.dumps(details['preferred_skills']),
                            'num_required': len(details['required_skills']),
                            'num_preferred': len(details['preferred_skills']),
                            
                            # Experience info
                            'education_required': json.dumps(details['education_required']),
                            'years_experience': details['years_experience'],
                            'new_grad_friendly': details['new_grad_friendly'],
                            'seniority_level': details['seniority_level'],
                            
                            # Raw descriptions (for debugging)
                            'job_description_snippet': details['job_description'][:500],
                            'source_url': job_url
                        }
                        
                        all_jobs.append(job_record)
                        
                        # Save incrementally (safety)
                        if len(all_jobs) % 10 == 0:
                            save_to_csv(all_jobs, f"temp_{len(all_jobs)}.csv")
                    
                    time.sleep(1)  # Be polite
                
                print(f"  ✓ Completed {country}: {len([j for j in all_jobs if j['search_keyword'] == keyword])} jobs")
                
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
        
    finally:
        driver.quit()
    
    # Final save
    final_file = save_to_csv(all_jobs, "linkedin_internships_structured.csv")
    print(f"\n{'='*60}")
    print(f"✅ TOTAL JOBS SCRAPED: {len(all_jobs)}")
    print(f"📁 Saved to: {final_file}")
    print(f"{'='*60}")
    
    return all_jobs


def save_to_csv(jobs, filename=None):
    """Save jobs to CSV with proper formatting"""
    
    if not jobs:
        print("No jobs to save")
        return None
    
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"data/internships_linkedin_{timestamp}.csv"
    
    # Ensure data directory exists
    import os
    os.makedirs('data', exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)
    
    return filename


# ==================== RUN ====================

if __name__ == "__main__":
    print("🚀 LinkedIn Internship Scraper for ML Project")
    print("=" * 60)
    print(f"Keywords: {JOB_KEYWORDS}")
    print(f"Countries: {COUNTRIES}")
    print(f"Max jobs per keyword: {MAX_JOBS_PER_KEYWORD}")
    print("=" * 60)
    
    jobs = scrape_linkedin_jobs()