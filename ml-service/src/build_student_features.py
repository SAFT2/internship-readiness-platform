import argparse
import json
from pathlib import Path

import pandas as pd

from readiness_assessor import ReadinessAssessor


def build_feature_dataframe(input_path, profile_path=None):
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    assessor = ReadinessAssessor(profile_path=profile_path)

    if input_path.suffix.lower() == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(input_path)

    required = ["target_role", "skills", "projects_count", "candidate_years", "experience_type"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    feature_rows = []
    for _, row in df.iterrows():
        raw_skills = row["skills"]
        if isinstance(raw_skills, str):
            try:
                parsed = json.loads(raw_skills)
                if isinstance(parsed, list):
                    skills = [str(item) for item in parsed]
                else:
                    skills = [segment.strip() for segment in raw_skills.split(",") if segment.strip()]
            except Exception:
                skills = [segment.strip() for segment in raw_skills.split(",") if segment.strip()]
        elif isinstance(raw_skills, list):
            skills = [str(item) for item in raw_skills]
        else:
            skills = []

        assessment = assessor.assess(
            target_role=str(row["target_role"]),
            candidate_skills=skills,
            candidate_years=float(row.get("candidate_years", 0) or 0),
            projects_count=int(row.get("projects_count", 0) or 0),
            experience_type=str(row.get("experience_type", "none") or "none"),
        )

        output_row = {
            "target_role": row["target_role"],
            "skill_score": assessment["feature_vector"]["skill_score"],
            "project_score": assessment["feature_vector"]["project_score"],
            "experience_score": assessment["feature_vector"]["experience_score"],
            "num_skills": assessment["feature_vector"]["num_skills"],
            "overall_score": assessment["overall_score"],
            "readiness_level": assessment["readiness_level"],
        }

        if "label" in df.columns:
            output_row["label"] = row["label"]

        feature_rows.append(output_row)

    return pd.DataFrame(feature_rows)


def _build_parser():
    parser = argparse.ArgumentParser(description="Build feature vectors for student profiles")
    parser.add_argument("--input", required=True, help="Path to CSV/JSON student profile data")
    parser.add_argument("--output", required=True, help="Output CSV for engineered feature vectors")
    parser.add_argument("--profile-path", default=None, help="Optional path to market_profile.json")
    return parser


def main():
    args = _build_parser().parse_args()
    features_df = build_feature_dataframe(args.input, profile_path=args.profile_path)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)

    print(json.dumps({"rows": len(features_df), "output": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
