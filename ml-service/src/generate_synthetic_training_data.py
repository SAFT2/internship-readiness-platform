import argparse
import json
import random
from pathlib import Path

import pandas as pd


LABELS = ["Not Ready", "Developing", "Ready", "Highly Ready"]


def _derive_label(score):
    if score >= 85:
        return "Highly Ready"
    if score >= 70:
        return "Ready"
    if score >= 45:
        return "Developing"
    return "Not Ready"


def generate_dataset(size=500, seed=42):
    random.seed(seed)
    rows = []

    for _ in range(size):
        skill_score = round(random.uniform(0, 50), 2)
        project_score = round(random.choice([0, 12, 20, 30]), 2)
        experience_score = round(random.choice([5, 10, 14, 16, 20]), 2)
        num_skills = random.randint(0, 20)

        total = round(skill_score + project_score + experience_score, 2)
        label = _derive_label(total)

        rows.append(
            {
                "skill_score": skill_score,
                "project_score": project_score,
                "experience_score": experience_score,
                "num_skills": num_skills,
                "label": label,
            }
        )

    return pd.DataFrame(rows)


def _build_parser():
    parser = argparse.ArgumentParser(description="Generate synthetic readiness training data")
    parser.add_argument("--size", type=int, default=500, help="Number of synthetic rows")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "data" / "processed" / "synthetic_training_data.csv"),
        help="Output CSV path",
    )
    return parser


def main():
    args = _build_parser().parse_args()
    df = generate_dataset(size=args.size, seed=args.seed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(
        json.dumps(
            {
                "rows": len(df),
                "output": str(output_path),
                "label_distribution": df["label"].value_counts().to_dict(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
