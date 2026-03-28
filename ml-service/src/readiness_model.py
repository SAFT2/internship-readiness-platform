import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "skill_score",
    "project_score",
    "experience_score",
    "num_skills",
]

LABEL_MAP = {
    "Not Ready": 0,
    "Developing": 1,
    "Ready": 2,
    "Highly Ready": 3,
}


def _encode_label(label):
    if isinstance(label, (int, float)):
        return int(label)
    normalized = str(label).strip()
    if normalized not in LABEL_MAP:
        raise ValueError(
            "Invalid label found. Expected one of: "
            + ", ".join(LABEL_MAP.keys())
            + " or numeric 0-3."
        )
    return LABEL_MAP[normalized]


def train_readiness_model(dataset_path, model_output_path):
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    required_columns = FEATURE_COLUMNS + ["label"]
    missing_cols = [column for column in required_columns if column not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    X = df[FEATURE_COLUMNS].copy()
    y = df["label"].apply(_encode_label)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    model_output_path = Path(model_output_path)
    model_output_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "label_map": LABEL_MAP,
    }

    pd.to_pickle(bundle, model_output_path)

    metrics = {
        "accuracy": round(float(accuracy), 4),
        "classification_report": report,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "model_path": str(model_output_path),
    }
    return metrics


def _build_parser():
    parser = argparse.ArgumentParser(description="Train internship readiness classifier")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to CSV with feature columns and label",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent.parent / "data" / "models" / "readiness_model.pkl"),
        help="Output path for trained model bundle (.pkl)",
    )
    return parser


def main():
    args = _build_parser().parse_args()
    metrics = train_readiness_model(args.dataset, args.output)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()