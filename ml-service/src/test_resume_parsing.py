import argparse
import json
from pathlib import Path

from resume_parser import ResumeParser


def _build_parser():
    parser = argparse.ArgumentParser(description="Test resume parsing against PDF samples")
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing resume PDFs",
    )
    parser.add_argument(
        "--role",
        default=None,
        help="Optional target role for readiness scoring",
    )
    parser.add_argument(
        "--profile-path",
        default=None,
        help="Optional path to market_profile.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output JSON file for aggregate results",
    )
    return parser


def main():
    args = _build_parser().parse_args()
    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Invalid input directory: {input_dir}")

    parser = ResumeParser(profile_path=args.profile_path)
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {input_dir}")

    results = []
    for pdf in pdf_files:
        try:
            if args.role:
                result = parser.parse_and_assess(pdf, args.role)
            else:
                result = parser.parse_resume(pdf)
            results.append({"resume": str(pdf), "status": "ok", "result": result})
        except Exception as exc:
            results.append({"resume": str(pdf), "status": "error", "error": str(exc)})

    summary = {
        "total": len(results),
        "successful": sum(1 for item in results if item["status"] == "ok"),
        "failed": sum(1 for item in results if item["status"] == "error"),
        "results": results,
    }

    print(json.dumps(summary, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
