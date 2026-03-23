import argparse
import json
from pathlib import Path


class ReadinessAssessor:
    """
    Evaluates internship readiness against a target role market profile.
    """

    def __init__(self, profile_path=None):
        base_dir = Path(__file__).resolve().parent
        default_profile = base_dir.parent / "data" / "market_profile.json"
        self.profile_path = Path(profile_path) if profile_path else default_profile

        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"Market profile not found: {self.profile_path}. Run market_analyzer.py first."
            )

        with self.profile_path.open("r", encoding="utf-8") as profile_file:
            self.market_profile = json.load(profile_file)

    @staticmethod
    def _normalize_skill(skill):
        normalization = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "tf": "tensorflow",
            "sklearn": "scikit-learn",
            "gcp": "google cloud",
            "aws lambda": "aws",
            "node.js": "nodejs",
            "node": "nodejs",
            "k8s": "kubernetes",
            "postgresql": "postgres",
            "ml": "machine learning",
            "nlp": "natural language processing",
            "cv": "computer vision",
        }
        cleaned = str(skill).strip().lower()
        return normalization.get(cleaned, cleaned)

    def _normalize_skills(self, skills):
        return {self._normalize_skill(skill) for skill in skills if str(skill).strip()}

    @staticmethod
    def _safe_ratio(numerator, denominator):
        if denominator <= 0:
            return 0.0
        return max(0.0, min(1.0, numerator / denominator))

    def _score_required_skills(self, candidate_skills, role_data):
        required_frequency = role_data.get("required_skill_frequency", {})
        if not required_frequency:
            return 0.0, 0.0, [], []

        total_weight = sum(required_frequency.values())
        if total_weight == 0:
            return 0.0, 0.0, [], []

        weighted_match = 0
        matched = []
        missing = []

        for skill, frequency in required_frequency.items():
            normalized = self._normalize_skill(skill)
            if normalized in candidate_skills:
                weighted_match += frequency
                matched.append(skill)
            else:
                missing.append((skill, frequency))

        coverage = self._safe_ratio(weighted_match, total_weight)
        score = coverage * 40
        missing_sorted = [skill for skill, _ in sorted(missing, key=lambda x: x[1], reverse=True)]
        return round(score, 2), round(coverage, 4), matched, missing_sorted

    def _score_preferred_skills(self, candidate_skills, role_data):
        preferred_frequency = role_data.get("preferred_skill_frequency", {})
        if not preferred_frequency:
            return 0.0, 0.0, []

        total_weight = sum(preferred_frequency.values())
        if total_weight == 0:
            return 0.0, 0.0, []

        weighted_match = 0
        matched = []

        for skill, frequency in preferred_frequency.items():
            normalized = self._normalize_skill(skill)
            if normalized in candidate_skills:
                weighted_match += frequency
                matched.append(skill)

        coverage = self._safe_ratio(weighted_match, total_weight)
        score = coverage * 10
        return round(score, 2), round(coverage, 4), matched

    def _score_projects(self, projects_count):
        if projects_count <= 0:
            return 0.0
        if projects_count == 1:
            return 12.0
        if projects_count == 2:
            return 20.0
        return 30.0

    def _score_experience(self, experience_type, candidate_years):
        experience_map = {
            "none": 5.0,
            "research": 10.0,
            "internship": 20.0,
            "part-time": 14.0,
            "full-time": 20.0,
        }

        base_score = experience_map.get(str(experience_type).strip().lower(), 5.0)
        if candidate_years >= 1 and base_score < 20.0:
            base_score = min(20.0, base_score + 2.0)
        return round(base_score, 2)

    @staticmethod
    def _readiness_level(score):
        if score >= 85:
            return "Highly Ready"
        if score >= 70:
            return "Ready"
        if score >= 45:
            return "Developing"
        return "Not Ready"

    @staticmethod
    def _recommendations(missing_required):
        recommendations = []
        for index, skill in enumerate(missing_required[:8], start=1):
            if index <= 3:
                priority = "High"
            elif index <= 6:
                priority = "Medium"
            else:
                priority = "Low"

            recommendations.append(
                {
                    "skill": skill,
                    "priority": priority,
                    "action": f"Build at least one project showcasing {skill}."
                }
            )
        return recommendations

    def assess(
        self,
        target_role,
        candidate_skills,
        candidate_years=0,
        projects_count=0,
        experience_type="none",
    ):
        if target_role not in self.market_profile:
            available_roles = sorted(self.market_profile.keys())
            raise ValueError(
                f"Unknown role '{target_role}'. Available roles: {', '.join(available_roles)}"
            )

        role_data = self.market_profile[target_role]
        normalized_candidate_skills = self._normalize_skills(candidate_skills)

        required_score, required_coverage, matched_required, missing_required = self._score_required_skills(
            normalized_candidate_skills,
            role_data,
        )
        preferred_score, preferred_coverage, matched_preferred = self._score_preferred_skills(
            normalized_candidate_skills,
            role_data,
        )
        skill_score = round(required_score + preferred_score, 2)
        projects_score = self._score_projects(projects_count)
        experience_score = self._score_experience(experience_type, candidate_years)

        overall_score = round(skill_score + projects_score + experience_score, 2)

        feature_vector = {
            "skill_score": skill_score,
            "project_score": projects_score,
            "experience_score": experience_score,
            "num_skills": len(normalized_candidate_skills),
            "required_skill_coverage": required_coverage,
            "preferred_skill_coverage": preferred_coverage,
            "projects_count": int(projects_count),
            "candidate_years": float(candidate_years),
        }

        return {
            "target_role": target_role,
            "overall_score": overall_score,
            "readiness_level": self._readiness_level(overall_score),
            "score_breakdown": {
                "skills_total": skill_score,
                "required_skills": required_score,
                "preferred_skills": preferred_score,
                "projects": projects_score,
                "experience": experience_score,
            },
            "feature_vector": feature_vector,
            "matched_skills": {
                "required": matched_required,
                "preferred": matched_preferred,
            },
            "missing_required_skills": missing_required,
            "recommendations": self._recommendations(missing_required),
            "role_snapshot": {
                "total_postings": role_data.get("total_postings", 0),
                "top_required_skills": role_data.get("top_required_skills", [])[:10],
                "new_grad_friendly_percentage": role_data.get("experience", {}).get(
                    "new_grad_friendly_percentage", 0
                ),
            },
        }


def _build_parser():
    parser = argparse.ArgumentParser(description="Assess internship readiness from market profile")
    parser.add_argument("--role", required=True, help="Target role, e.g. 'ML Intern'")
    parser.add_argument(
        "--skills",
        required=True,
        help="Comma-separated skills, e.g. 'python,pytorch,sql,git'",
    )
    parser.add_argument("--years", type=float, default=0, help="Years of experience")
    parser.add_argument("--projects", type=int, default=0, help="Number of relevant projects")
    parser.add_argument(
        "--experience-type",
        default="none",
        choices=["none", "research", "internship", "part-time", "full-time"],
        help="Type of practical experience",
    )
    parser.add_argument(
        "--profile-path",
        default=None,
        help="Optional path to market_profile.json",
    )
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    skills = [skill.strip() for skill in args.skills.split(",") if skill.strip()]
    assessor = ReadinessAssessor(profile_path=args.profile_path)
    result = assessor.assess(
        args.role,
        skills,
        candidate_years=args.years,
        projects_count=args.projects,
        experience_type=args.experience_type,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()