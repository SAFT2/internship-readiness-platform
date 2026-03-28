import pandas as pd
import numpy as np
import json
import ast
import re
from pathlib import Path
from collections import Counter
import warnings
warnings.filterwarnings('ignore')


class InternshipDataCleaner:
    """
    Cleans raw scraped internship data into analysis-ready format
    """
    
    def __init__(self, input_path):
        self.base_dir = Path(__file__).resolve().parent
        self.input_path = Path(input_path)
        self.df = None
        self.cleaned_df = None
        
        # Role standardization mapping
        self.role_mappings = {
            # Machine Learning
            'ml intern': 'ML Intern',
            'machine learning intern': 'ML Intern',
            'machine learning engineer intern': 'ML Intern',
            'deep learning intern': 'ML Intern',
            'ai intern': 'ML Intern',
            'artificial intelligence intern': 'ML Intern',
            
            # Data Science
            'data science intern': 'Data Science Intern',
            'data scientist intern': 'Data Science Intern',
            'data analyst intern': 'Data Science Intern',
            'analytics intern': 'Data Science Intern',
            'business intelligence intern': 'Data Science Intern',
            
            # Software Engineering
            'software engineer intern': 'Software Engineering Intern',
            'software engineering intern': 'Software Engineering Intern',
            'swe intern': 'Software Engineering Intern',
            'sw engineer intern': 'Software Engineering Intern',
            'developer intern': 'Software Engineering Intern',
            
            # Backend
            'backend intern': 'Backend Intern',
            'back end intern': 'Backend Intern',
            'back-end intern': 'Backend Intern',
            'server side intern': 'Backend Intern',
            'api developer intern': 'Backend Intern',
            
            # Frontend
            'frontend intern': 'Frontend Intern',
            'front end intern': 'Frontend Intern',
            'front-end intern': 'Frontend Intern',
            'ui intern': 'Frontend Intern',
            'ux intern': 'Frontend Intern',
            'web developer intern': 'Frontend Intern',
            
            # Other common roles
            'full stack intern': 'Full Stack Intern',
            'fullstack intern': 'Full Stack Intern',
            'full-stack intern': 'Full Stack Intern',
            'devops intern': 'DevOps Intern',
            'cloud intern': 'Cloud Intern',
            'mobile intern': 'Mobile Intern',
            'ios intern': 'Mobile Intern',
            'android intern': 'Mobile Intern',
            'security intern': 'Security Intern',
            'qa intern': 'QA Intern',
            'test engineer intern': 'QA Intern',
        }
        
        # Skills normalization mapping
        self.skill_normalization = {
            # Framework variations
            'tf': 'tensorflow',
            'tensorflow 2': 'tensorflow',
            'pytorch lightning': 'pytorch',
            'sklearn': 'scikit-learn',
            'scikitlearn': 'scikit-learn',
            'scikit learn': 'scikit-learn',
            
            # Cloud variations
            'gcp': 'google cloud',
            'google cloud platform': 'google cloud',
            'aws lambda': 'aws',
            'amazon web services': 'aws',
            'azure ml': 'azure',
            
            # Language variations
            'js': 'javascript',
            'node': 'nodejs',
            'node.js': 'nodejs',
            'ts': 'typescript',
            'py': 'python',
            'cpp': 'c++',
            'c plus plus': 'c++',
            
            # Tool variations
            'k8s': 'kubernetes',
            'github actions': 'github',
            'git hub': 'github',
            'postgresql': 'postgres',
            'postgre sql': 'postgres',
            
            # Concept variations
            'ml': 'machine learning',
            'deep learning': 'deep learning',  # Keep as is
            'nlp': 'natural language processing',
            'natural language': 'natural language processing',
            'cv': 'computer vision',
            'computer vision': 'computer vision',
        }
    
    def load_data(self):
        """Load raw CSV data"""
        print(f"Loading data from: {self.input_path}")
        self.df = pd.read_csv(self.input_path)
        print(f"✓ Loaded {len(self.df)} rows")
        print(f"Columns: {list(self.df.columns)}")
        return self
    
    def parse_json_columns(self):
        """Convert JSON string columns to Python objects"""
        print("\nParsing JSON columns...")
        
        def safe_parse(x):
            """Safely parse JSON string to list"""
            if pd.isna(x) or x == '':
                return []
            if isinstance(x, list):
                return x
            try:
                # Try ast.literal_eval first (handles single quotes)
                return ast.literal_eval(x)
            except:
                try:
                    # Try json.loads (handles double quotes)
                    return json.loads(x)
                except:
                    # Fallback: split by comma if it's a string
                    if isinstance(x, str):
                        return [s.strip() for s in x.split(',') if s.strip()]
                    return []
        
        # Parse skills columns
        if 'required_skills' in self.df.columns:
            self.df['required_skills_list'] = self.df['required_skills'].apply(safe_parse)
        else:
            self.df['required_skills_list'] = [[] for _ in range(len(self.df))]
            
        if 'preferred_skills' in self.df.columns:
            self.df['preferred_skills_list'] = self.df['preferred_skills'].apply(safe_parse)
        else:
            self.df['preferred_skills_list'] = [[] for _ in range(len(self.df))]
        
        # Parse education if present
        if 'education_required' in self.df.columns:
            self.df['education_list'] = self.df['education_required'].apply(safe_parse)
        else:
            self.df['education_list'] = [[] for _ in range(len(self.df))]
        
        print("✓ Parsed JSON columns")
        return self
    
    def normalize_skills(self, skills_list):
        """Normalize skill names to standard format"""
        normalized = []
        for skill in skills_list:
            skill_lower = skill.lower().strip()
            # Check for normalization
            normalized_skill = self.skill_normalization.get(skill_lower, skill_lower)
            normalized.append(normalized_skill)
        return list(set(normalized))  # Remove duplicates
    
    def clean_skills(self):
        """Clean and normalize all skills"""
        print("\nCleaning skills...")
        
        self.df['required_skills_clean'] = self.df['required_skills_list'].apply(self.normalize_skills)
        self.df['preferred_skills_clean'] = self.df['preferred_skills_list'].apply(self.normalize_skills)
        
        # Create combined skills list
        self.df['all_skills'] = self.df.apply(
            lambda x: list(set(x['required_skills_clean'] + x['preferred_skills_clean'])), 
            axis=1
        )
        
        # Count skills
        self.df['num_required_skills'] = self.df['required_skills_clean'].apply(len)
        self.df['num_preferred_skills'] = self.df['preferred_skills_clean'].apply(len)
        self.df['num_total_skills'] = self.df['all_skills'].apply(len)
        
        print("✓ Normalized skills")
        print(f"  Avg required skills: {self.df['num_required_skills'].mean():.1f}")
        print(f"  Avg preferred skills: {self.df['num_preferred_skills'].mean():.1f}")
        return self
    
    def standardize_roles(self):
        """Standardize job titles into categories"""
        print("\nStandardizing job roles...")
        
        def categorize_role(title):
            if pd.isna(title):
                return 'Other'
            
            title_lower = title.lower().strip()
            
            # Check exact matches first
            if title_lower in self.role_mappings:
                return self.role_mappings[title_lower]
            
            # Check partial matches
            for key, value in self.role_mappings.items():
                if key in title_lower:
                    return value
            
            # Extract from keyword presence
            if any(x in title_lower for x in ['machine learning', 'ml ', 'deep learning', 'neural', 'ai ', 'artificial intelligence']):
                return 'ML Intern'
            elif any(x in title_lower for x in ['data science', 'data scientist']):
                return 'Data Science Intern'
            elif any(x in title_lower for x in ['backend', 'back end', 'back-end', 'server']):
                return 'Backend Intern'
            elif any(x in title_lower for x in ['frontend', 'front end', 'front-end', 'ui ', 'ux ', 'web developer']):
                return 'Frontend Intern'
            elif any(x in title_lower for x in ['software engineer', 'software engineering', 'swe ', 'developer']):
                return 'Software Engineering Intern'
            elif any(x in title_lower for x in ['full stack', 'fullstack', 'full-stack']):
                return 'Full Stack Intern'
            elif any(x in title_lower for x in ['project manager', 'pm ', 'product manager']):
                return 'Project Manager Intern'
            elif any(x in title_lower for x in ['data analyst', 'data analysis', 'analyst', 'analytics']):
                return 'Data Analyst Intern'
            elif any(x in title_lower for x in ['devops', 'sre ', 'site reliability']):
                return 'DevOps Intern'
            elif any(x in title_lower for x in ['mobile', 'ios', 'android']):
                return 'Mobile Intern'
            elif any(x in title_lower for x in ['security', 'cybersecurity']):
                return 'Security Intern'
            elif any(x in title_lower for x in ['qa ', 'quality assurance', 'test']):
                return 'QA Intern'
            else:
                return 'Other'
        
        self.df['role_category'] = self.df['role'].apply(categorize_role)
        
        print("✓ Standardized roles")
        print(self.df['role_category'].value_counts())
        return self
    
    def clean_location(self):
        """Extract clean location information"""
        print("\nCleaning locations...")
        
        def extract_location_info(location_str):
            if pd.isna(location_str):
                return {'city': '', 'state': '', 'country': '', 'remote': False}
            
            location_str = str(location_str).strip()
            remote = 'remote' in location_str.lower()
            
            # Remove "Remote in" prefix
            clean = re.sub(r'remote\s*(in)?\s*', '', location_str, flags=re.IGNORECASE)
            
            # Split by comma
            parts = [p.strip() for p in clean.split(',')]
            
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1]
                country = parts[2] if len(parts) > 2 else 'United States'
            else:
                city = clean
                state = ''
                country = 'United States'
            
            return {
                'city': city,
                'state': state,
                'country': country,
                'remote': remote
            }
        
        location_info = self.df['location'].apply(extract_location_info)
        self.df['city'] = location_info.apply(lambda x: x['city'])
        self.df['state'] = location_info.apply(lambda x: x['state'])
        self.df['country_clean'] = location_info.apply(lambda x: x['country'])
        self.df['is_remote'] = location_info.apply(lambda x: x['remote'])
        
        print("✓ Cleaned locations")
        print(f"  Remote jobs: {self.df['is_remote'].sum()}")
        return self
    
    def clean_experience(self):
        """Clean experience level data"""
        print("\nCleaning experience data...")
        
        # Ensure numeric
        if 'years_experience' in self.df.columns:
            self.df['years_experience'] = pd.to_numeric(self.df['years_experience'], errors='coerce')
            self.df['years_experience'] = self.df['years_experience'].fillna(0)
        else:
            self.df['years_experience'] = 0
        
        # Categorize experience
        def exp_category(years):
            if years == 0:
                return 'Entry (0 years)'
            elif years <= 1:
                return 'Junior (0-1 years)'
            elif years <= 3:
                return 'Mid (1-3 years)'
            else:
                return 'Senior (3+ years)'
        
        self.df['experience_category'] = self.df['years_experience'].apply(exp_category)
        
        # New grad friendly
        if 'new_grad_friendly' in self.df.columns:
            self.df['new_grad_friendly'] = self.df['new_grad_friendly'].fillna(False)
        else:
            self.df['new_grad_friendly'] = self.df['years_experience'] <= 1
        
        print("✓ Cleaned experience data")
        print(self.df['experience_category'].value_counts())
        return self
    
    def remove_duplicates(self):
        """Remove duplicate job postings"""
        print("\nRemoving duplicates...")
        
        before = len(self.df)
        
        # Consider duplicates if same company + similar title + same location
        self.df['title_clean'] = self.df['role'].str.lower().str[:30]
        self.df['company_clean'] = self.df['company'].str.lower().str[:20]
        
        self.df = self.df.drop_duplicates(
            subset=['title_clean', 'company_clean', 'location'],
            keep='first'
        )
        
        # Drop helper columns
        self.df = self.df.drop(['title_clean', 'company_clean'], axis=1)
        
        after = len(self.df)
        print(f"✓ Removed {before - after} duplicates")
        print(f"  Remaining: {after} jobs")
        return self
    
    def filter_quality(self):
        """Filter out low-quality postings"""
        print("\nFiltering quality...")
        
        before = len(self.df)
        
        # Must have at least some description
        if 'job_description_snippet' in self.df.columns:
            has_desc = self.df['job_description_snippet'].notna()
            has_desc = has_desc & (self.df['job_description_snippet'].str.len() > 50)
        else:
            has_desc = True
        
        # Must have company name
        has_company = self.df['company'].notna() & (self.df['company'] != '')
        
        # Must have at least 1 skill identified OR it's a very short description
        has_skills = (self.df['num_total_skills'] > 0) | ~has_desc
        
        self.df = self.df[has_desc & has_company & has_skills]
        
        after = len(self.df)
        print(f"✓ Removed {before - after} low-quality postings")
        return self
    
    def select_final_columns(self):
        """Select and order final columns"""
        desired_columns = [
            # Identifiers
            'role', 'role_category', 'company', 'company_url',
            
            # Location
            'location', 'city', 'state', 'country_clean', 'is_remote',
            
            # Skills (main data for your project)
            'required_skills_clean', 'preferred_skills_clean', 'all_skills',
            'num_required_skills', 'num_preferred_skills', 'num_total_skills',
            
            # Experience
            'years_experience', 'experience_category', 'new_grad_friendly',
            'education_list', 'seniority_level',
            
            # Metadata
            'posted', 'search_keyword', 'source_url', 'job_description_snippet'
        ]
        
        # Only keep columns that exist
        existing_cols = [c for c in desired_columns if c in self.df.columns]
        self.cleaned_df = self.df[existing_cols].copy()
        
        # Rename for clarity
        self.cleaned_df = self.cleaned_df.rename(columns={
            'country_clean': 'country',
            'required_skills_clean': 'required_skills',
            'preferred_skills_clean': 'preferred_skills',
            'education_list': 'education_required'
        })
        
        return self
    
    def save_cleaned_data(self, output_dir=None):
        """Save cleaned data to CSV"""
        if output_dir is None:
            output_dir = self.base_dir.parent / 'data' / 'processed'
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"internships_cleaned_{timestamp}.csv"

        self.cleaned_df.to_csv(output_file, index=False)
        print(f"\n✓ Saved cleaned data to: {output_file}")

        # Also save as latest
        latest_file = output_dir / "internships_cleaned_latest.csv"
        self.cleaned_df.to_csv(latest_file, index=False)

        # store paths if needed later
        self.output_file = output_file
        self.latest_file = latest_file

        return self
    
    def generate_summary(self):
        """Generate data summary statistics"""
        print("\n" + "="*60)
        print("DATA CLEANING SUMMARY")
        print("="*60)
        
        print(f"\nTotal job postings: {len(self.cleaned_df)}")
        print(f"\nRole distribution:")
        print(self.cleaned_df['role_category'].value_counts())
        
        print(f"\nTop 10 Required Skills:")
        all_required = []
        for skills in self.cleaned_df['required_skills']:
            all_required.extend(skills)
        top_required = Counter(all_required).most_common(10)
        for skill, count in top_required:
            print(f"  {skill}: {count}")
        
        print(f"\nTop 10 Preferred Skills:")
        all_preferred = []
        for skills in self.cleaned_df['preferred_skills']:
            all_preferred.extend(skills)
        top_preferred = Counter(all_preferred).most_common(10)
        for skill, count in top_preferred:
            print(f"  {skill}: {count}")
        
        print(f"\nRemote vs On-site:")
        print(self.cleaned_df['is_remote'].value_counts())
        
        print(f"\nExperience requirements:")
        print(self.cleaned_df['experience_category'].value_counts())
        
        print("\n" + "="*60)
        
        return {
            'total_jobs': len(self.cleaned_df),
            'role_distribution': self.cleaned_df['role_category'].value_counts().to_dict(),
            'top_required_skills': dict(top_required),
            'top_preferred_skills': dict(top_preferred),
            'remote_percentage': self.cleaned_df['is_remote'].mean() * 100
        }
    
    def run_full_pipeline(self):
        """Execute complete cleaning pipeline"""
        return (self
            .load_data()
            .parse_json_columns()
            .clean_skills()
            .standardize_roles()
            .clean_location()
            .clean_experience()
            .remove_duplicates()
            .filter_quality()
            .select_final_columns()
            .save_cleaned_data()
            .generate_summary()
        )


# Main execution
if __name__ == "__main__":
    import sys
    base_dir = Path(__file__).resolve().parent
    
    # Find the most recent raw file
    raw_dir = base_dir.parent / "data" / "raw"
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in data/raw/")
        print("Please put your scraped LinkedIn data there")
        sys.exit(1)
    
    # Use most recent file
    latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"Using file: {latest_file}")
    
    # Run cleaning
    cleaner = InternshipDataCleaner(latest_file)
    summary = cleaner.run_full_pipeline()
    
    print("\n✓ Phase 1 Complete!")