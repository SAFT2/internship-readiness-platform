import pandas as pd
import json
from collections import Counter
from pathlib import Path


class MarketProfileBuilder:
    """
    Analyzes cleaned internship data to create market requirements profile
    """
    
    def __init__(self, cleaned_data_path):
        self.base_dir = Path(__file__).resolve().parent
        self.df = pd.read_csv(cleaned_data_path)
        self.profile = {}
        
        # Convert string representations back to lists
        import ast
        def safe_eval(x):
            try:
                return ast.literal_eval(x)
            except:
                return []
        
        self.df['required_skills'] = self.df['required_skills'].apply(safe_eval)
        self.df['preferred_skills'] = self.df['preferred_skills'].apply(safe_eval)
    
    def build_role_profile(self, role_category, min_frequency=2):
        """
        Build profile for a specific role category
        
        min_frequency: skill must appear in at least N postings to be considered
        """
        role_df = self.df[self.df['role_category'] == role_category]
        
        if len(role_df) == 0:
            return None
        
        # Required skills analysis
        all_required = []
        for skills in role_df['required_skills']:
            all_required.extend(skills)
        
        required_counts = Counter(all_required)
        # Filter by frequency and get top 15
        top_required = [
            skill for skill, count in required_counts.most_common(15)
            if count >= min_frequency
        ]
        
        # Preferred skills analysis
        all_preferred = []
        for skills in role_df['preferred_skills']:
            all_preferred.extend(skills)
        
        preferred_counts = Counter(all_preferred)
        top_preferred = [
            skill for skill, count in preferred_counts.most_common(15)
            if count >= min_frequency
        ]
        
        # Experience analysis
        avg_years = role_df['years_experience'].mean()
        new_grad_pct = role_df['new_grad_friendly'].mean() * 100
        
        # Education requirements
        all_education = []
        for edu_list in role_df['education_required']:
            if isinstance(edu_list, list):
                all_education.extend(edu_list)
        education_counts = Counter(all_education)
        
        # Location distribution
        location_dist = role_df['state'].value_counts().head(5).to_dict()
        
        # Remote availability
        remote_pct = role_df['is_remote'].mean() * 100
        
        profile = {
            'total_postings': len(role_df),
            'top_required_skills': top_required,
            'required_skill_frequency': dict(required_counts.most_common(10)),
            'top_preferred_skills': top_preferred,
            'preferred_skill_frequency': dict(preferred_counts.most_common(10)),
            'experience': {
                'average_years': round(avg_years, 2),
                'new_grad_friendly_percentage': round(new_grad_pct, 1),
                'distribution': role_df['experience_category'].value_counts().to_dict()
            },
            'education_requirements': dict(education_counts.most_common()),
            'top_locations': location_dist,
            'remote_percentage': round(remote_pct, 1),
            'sample_job_titles': role_df['role'].unique()[:5].tolist()
        }
        
        return profile
    
    def build_all_profiles(self):
        """Build profiles for all role categories"""
        print("Building market profiles...")
        
        categories = self.df['role_category'].unique()
        
        for category in categories:
            print(f"\nAnalyzing: {category}")
            profile = self.build_role_profile(category)
            if profile:
                self.profile[category] = profile
                print(f"  ✓ {profile['total_postings']} postings")
                print(f"  Top skills: {', '.join(profile['top_required_skills'][:5])}")
        
        return self
    
    def save_profile(self, output_path=None):
        """Save profile to JSON"""
        if output_path is None:
            output_path = self.base_dir.parent / 'data' / 'market_profile.json'
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.profile, f, indent=2)
        
        print(f"\n✓ Saved market profile to: {output_path}")
        return output_path
    
    def generate_skill_matrix(self):
        """Generate skill vs role matrix for visualization"""
        all_skills = set()
        for skills in self.df['required_skills']:
            all_skills.update(skills)
        
        categories = self.df['role_category'].unique()
        
        matrix = []
        for skill in sorted(all_skills):
            row = {'skill': skill}
            for cat in categories:
                cat_df = self.df[self.df['role_category'] == cat]
                total = len(cat_df)
                if total > 0:
                    has_skill = sum(1 for skills in cat_df['required_skills'] if skill in skills)
                    row[cat] = round(has_skill / total * 100, 1)
                else:
                    row[cat] = 0
            matrix.append(row)
        
        matrix_df = pd.DataFrame(matrix)
        output_path = self.base_dir.parent / 'data' / 'processed' / 'skill_role_matrix.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_df.to_csv(output_path, index=False)
        print("✓ Saved skill-role matrix")
        return matrix_df
    
    def run(self):
        """Execute full analysis"""
        self.build_all_profiles()
        self.save_profile()
        self.generate_skill_matrix()
        print("\n✓ Market analysis complete!")
        return self.profile


# Main execution
if __name__ == "__main__":
    import sys
    base_dir = Path(__file__).resolve().parent
    processed_dir = base_dir.parent / "data" / "processed"
    
    # Find cleaned data
    cleaned_files = list(processed_dir.glob("*cleaned*.csv"))
    if not cleaned_files:
        print("No cleaned data found. Run data_cleaning.py first")
        sys.exit(1)
    
    latest = max(cleaned_files, key=lambda p: p.stat().st_mtime)
    print(f"Using: {latest}")
    
    builder = MarketProfileBuilder(latest)
    profile = builder.run()
    
    # Print summary
    print("\n" + "="*60)
    print("MARKET PROFILE SUMMARY")
    print("="*60)
    for role, data in profile.items():
        print(f"\n{role}:")
        print(f"  Postings: {data['total_postings']}")
        print(f"  Must-have: {', '.join(data['top_required_skills'][:5])}")
        print(f"  Nice-to-have: {', '.join(data['top_preferred_skills'][:3])}")