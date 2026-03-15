import pandas as pd
import json
import ast

def clean_internship_data(input_file):
    """Clean and prepare scraped internship data"""
    df = pd.read_csv(input_file)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['role', 'company', 'location'])
    
    # Parse JSON skill columns
    def safe_parse(x):
        try:
            if isinstance(x, str):
                return ast.literal_eval(x)
            return x
        except:
            return []
    
    df['required_skills_list'] = df['required_skills'].apply(safe_parse)
    df['preferred_skills_list'] = df['preferred_skills'].apply(safe_parse)
    
    # Standardize role titles
    def standardize_role(title):
        title = title.lower()
        if any(x in title for x in ['machine learning', 'ml ', 'deep learning', 'ai', 'ml-ai engineering intern', 'arteficial intelligence']):
            return 'ML Intern'
        elif any(x in title for x in ['data science', 'data scientist']):
            return 'Data Science Intern'
        elif any(x in title for x in ['backend', 'back-end', 'back end']):
            return 'Backend Intern'
        elif any(x in title for x in ['frontend', 'front-end', 'front end']):
            return 'Frontend Intern'
        elif any(x in title for x in ['software engineer', 'swe ', 'sw intern', 'software', 'full stack', 'developer']):
            return 'Software Engineering Intern'
        elif any(x in title for x in ['project manager', 'pm ', 'product manager']):
            return 'Project Manager Intern'
        elif any(x in title for x in ['data analyst', 'data analysis', 'analyst', 'analytics']):
            return 'Data Analyst Intern'
        else:
            return 'Other'
    
    df['role_category'] = df['role'].apply(standardize_role)
    
    # Create master skills list
    df['all_skills'] = df['required_skills_list'] + df['preferred_skills_list']
    
    # Save cleaned version
    output = input_file.replace('.csv', '_cleaned.csv')
    df.to_csv(output, index=False)
    print(f"✓ Cleaned data saved: {output}")
    print(f"✓ Total unique postings: {len(df)}")
    print(f"✓ Role distribution:\n{df['role_category'].value_counts()}")
    
    return df

# Run it
df = clean_internship_data('scrapers/linkedin_internships_structured.csv')