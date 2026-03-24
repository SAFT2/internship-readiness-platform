import argparse
import json
import re
from pathlib import Path

from readiness_assessor import ReadinessAssessor


class ResumeParser:
    """
    Parse resume PDF files and extract structured candidate profile data.
    """

    def __init__(self, profile_path=None):
        self.assessor = ReadinessAssessor(profile_path=profile_path)
        self.skill_vocabulary = self._build_skill_vocabulary(self.assessor.market_profile)
        self.skill_aliases = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "node": "nodejs",
            "node.js": "nodejs",
            "tf": "tensorflow",
            "sklearn": "scikit-learn",
            "gcp": "google cloud",
            "k8s": "kubernetes",
            "nlp": "natural language processing",
            "cv": "computer vision",
            "postgresql": "postgres",
            "postgres": "postgres",
        }

    @staticmethod
    def _build_skill_vocabulary(market_profile):
        skills = set(
            [
                "python", "java", "javascript", "typescript", "sql", "git", "github",
                "docker", "kubernetes", "aws", "azure", "google cloud", "linux", "bash",
                "react", "nodejs", "flask", "fastapi", "django", "spring", "pytorch",
                "tensorflow", "scikit-learn", "pandas", "numpy", "statistics",
                "machine learning", "deep learning", "natural language processing",
                "computer vision", "tableau", "powerbi", "spark", "airflow",
            ]
        )

        for role_data in market_profile.values():
            skills.update(role_data.get("top_required_skills", []))
            skills.update(role_data.get("top_preferred_skills", []))
            skills.update(role_data.get("required_skill_frequency", {}).keys())
            skills.update(role_data.get("preferred_skill_frequency", {}).keys())

        return sorted({str(skill).strip().lower() for skill in skills if str(skill).strip()})

    @staticmethod
    def extract_text_from_pdf(pdf_path):
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Resume not found: {pdf_path}")

        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise ImportError(
                "pypdf is required for resume parsing. Install with: pip install pypdf"
            ) from exc

        reader = PdfReader(str(pdf_path))
        text_chunks = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)

        text = "\n".join(text_chunks).strip()
        if not text:
            raise ValueError("No text could be extracted from the PDF resume")
        return text

    @staticmethod
    def _normalize_text(text):
        normalized = text.lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _extract_skills(self, resume_text):
        text = self._normalize_text(resume_text)
        found = set()

        for skill in self.skill_vocabulary:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text):
                found.add(skill)

        alias_hits = self._extract_alias_skills(text)
        section_hits = self._extract_skills_from_sections(resume_text)

        merged = found.union(alias_hits).union(section_hits)
        return sorted(self._canonicalize_skills(merged))

    def _extract_alias_skills(self, normalized_text):
        alias_hits = set()
        for alias, canonical in self.skill_aliases.items():
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, normalized_text):
                alias_hits.add(canonical)
        return alias_hits

    def _extract_skills_from_sections(self, resume_text):
        section_hits = set()
        lines = [line.strip().lower() for line in resume_text.splitlines() if line.strip()]

        capture = False
        for line in lines:
            if any(header in line for header in ["skills", "technical skills", "tech stack", "tools"]):
                capture = True

            if capture:
                tokens = re.split(r"[,|/•·;-]", line)
                for token in tokens:
                    skill = token.strip()
                    if not skill:
                        continue
                    normalized = self.skill_aliases.get(skill, skill)
                    if normalized in self.skill_vocabulary:
                        section_hits.add(normalized)

            if any(header in line for header in ["experience", "education", "projects", "certifications"]):
                if "skills" not in line and "technical" not in line:
                    capture = False

        return section_hits

    def _canonicalize_skills(self, skills):
        canonical = set()
        for skill in skills:
            lowered = str(skill).strip().lower()
            if not lowered:
                continue
            canonical.add(self.skill_aliases.get(lowered, lowered))
        return canonical

    @staticmethod
    def _extract_email(resume_text):
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_phone(resume_text):
        match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", resume_text)
        return match.group(0).strip() if match else None

    @staticmethod
    def _estimate_projects_count(resume_text):
        text = resume_text.lower()

        heading_bonus = 0
        if re.search(r"\bprojects?\b", text):
            heading_bonus = 1

        project_signals = len(
            re.findall(
                r"\b(built|developed|implemented|designed|deployed|created|engineered)\b",
                text,
            )
        )

        estimated = min(6, heading_bonus + max(0, project_signals // 2))
        return int(estimated)

    @staticmethod
    def _extract_candidate_years(resume_text):
        text = resume_text.lower()
        year_values = []

        patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*years?\s+of\s+experience",
            r"experience\s+of\s+(\d+(?:\.\d+)?)\+?\s*years?",
            r"(\d+(?:\.\d+)?)\+?\s*yrs?\s+experience",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    year_values.append(float(match))
                except ValueError:
                    continue

        if year_values:
            return float(max(year_values))
        return 0.0

    @staticmethod
    def _extract_experience_type(resume_text):
        text = resume_text.lower()
        if "internship" in text or "intern " in text:
            return "internship"
        if "research" in text or "research assistant" in text:
            return "research"
        if "part-time" in text or "part time" in text:
            return "part-time"
        if "full-time" in text or "full time" in text:
            return "full-time"
        return "none"

    @staticmethod
    def _extract_education(resume_text):
        text = resume_text.lower()
        education = []

        if any(token in text for token in ["phd", "ph.d", "doctorate"]):
            education.append("PhD")
        if any(token in text for token in ["master", "m.s", "ms "]):
            education.append("Masters")
        if any(token in text for token in ["bachelor", "b.s", "bs ", "undergraduate"]):
            education.append("Bachelors")

        return education

    def parse_resume(self, pdf_path):
        resume_text = self.extract_text_from_pdf(pdf_path)
        return self.parse_resume_text(resume_text)

    def parse_resume_text(self, resume_text):
        profile = {
            "email": self._extract_email(resume_text),
            "phone": self._extract_phone(resume_text),
            "skills": self._extract_skills(resume_text),
            "projects_count": self._estimate_projects_count(resume_text),
            "candidate_years": self._extract_candidate_years(resume_text),
            "experience_type": self._extract_experience_type(resume_text),
            "education": self._extract_education(resume_text),
            "text_length": len(resume_text),
        }
        return profile

    def parse_and_assess(self, pdf_path, target_role):
        profile = self.parse_resume(pdf_path)
        assessment = self.assessor.assess(
            target_role=target_role,
            candidate_skills=profile["skills"],
            candidate_years=profile["candidate_years"],
            projects_count=profile["projects_count"],
            experience_type=profile["experience_type"],
        )
        return {
            "profile": profile,
            "assessment": assessment,
        }


def _build_parser():
    parser = argparse.ArgumentParser(description="Parse resume PDF and extract candidate profile")
    parser.add_argument("--resume", required=True, help="Path to resume PDF")
    parser.add_argument(
        "--role",
        default=None,
        help="Optional target role; if provided, parser also runs readiness assessment",
    )
    parser.add_argument(
        "--profile-path",
        default=None,
        help="Optional path to market_profile.json",
    )
    return parser


def main():
    args = _build_parser().parse_args()
    parser = ResumeParser(profile_path=args.profile_path)

    if args.role:
        result = parser.parse_and_assess(args.resume, args.role)
    else:
        result = parser.parse_resume(args.resume)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()