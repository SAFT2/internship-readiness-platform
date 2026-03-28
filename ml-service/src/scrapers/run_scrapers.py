from pathlib import Path

from linkedin_scraper import scrape_linkedin_jobs
import pandas as pd


def main():
    # Get project root
    PROJECT_ROOT = Path(__file__).resolve().parents[3]

    # Data path
    output_dir = PROJECT_ROOT / "ml-service" / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "linkedin_internships.csv"

    print("=== Scraping LinkedIn ===")
    jobs = scrape_linkedin_jobs()
    if not jobs:
        print("No jobs scraped")
        return

    df = pd.DataFrame(jobs)
    df.to_csv(output_path, index=False)

    print(f"\n✓ Total internships scraped: {len(df)}")
    print(f"✓ Saved to: {output_path}")


if __name__ == "__main__":
    main()