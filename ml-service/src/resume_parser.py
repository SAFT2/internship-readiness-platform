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

    @staticmethod
    def _extract_section_text(resume_text, section_headers):
        lines = resume_text.splitlines()
        collected = []
        capture = False

        stop_headers = [
            "experience", "education", "projects", "certifications", "skills", "summary",
            "achievements", "publications", "activities", "leadership",
        ]

        for raw_line in lines:
            line = raw_line.strip()
            lowered = line.lower()
            if not line:
                continue

            if any(header in lowered for header in section_headers):
                capture = True
                continue

            if capture and any(header in lowered for header in stop_headers):
                break

            if capture:
                collected.append(line)

        return "\n".join(collected)

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

    def _estimate_project_quality_score(self, resume_text):
        project_text = self._extract_section_text(resume_text, ["project", "projects"])
        text = (project_text or resume_text).lower()

        action_hits = len(
            re.findall(
                r"\b(built|developed|implemented|designed|deployed|optimized|improved|created|engineered|led|integrated)\b",
                text,
            )
        )
        impact_hits = len(
            re.findall(
                r"(\b\d+(?:\.\d+)?%\b|\b\d+(?:\.\d+)?x\b|\b\d+[kKmM]?\+?\s*(?:users|requests|downloads|transactions)\b)",
                text,
            )
        )
        production_hits = len(
            re.findall(
                r"\b(deployed|production|scalable|monitoring|ci/cd|pipeline|kubernetes|docker|aws|azure|gcp)\b",
                text,
            )
        )

        action_score = min(1.0, action_hits / 6.0)
        impact_score = min(1.0, impact_hits / 3.0)
        production_score = min(1.0, production_hits / 3.0)

        quality = (0.45 * action_score) + (0.35 * impact_score) + (0.20 * production_score)
        return round(min(1.0, max(0.0, quality)), 4)

    def _estimate_project_relevance_score(self, resume_text, target_role):
        role_data = self.assessor.market_profile.get(target_role, {})
        required = {
            self.assessor._normalize_skill(skill)
            for skill in role_data.get("top_required_skills", [])
            if str(skill).strip()
        }
        preferred = {
            self.assessor._normalize_skill(skill)
            for skill in role_data.get("top_preferred_skills", [])
            if str(skill).strip()
        }

        project_text = self._extract_section_text(resume_text, ["project", "projects"]) or resume_text
        normalized_project_text = self._normalize_text(project_text)

        found_skills = set()
        for skill in self.skill_vocabulary:
            normalized_skill = self.assessor._normalize_skill(skill)
            if re.search(r"\b" + re.escape(skill) + r"\b", normalized_project_text):
                found_skills.add(normalized_skill)

        required_hits = len(required.intersection(found_skills))
        preferred_hits = len(preferred.intersection(found_skills))

        required_denominator = max(1, min(8, len(required)))
        preferred_denominator = max(1, min(8, len(preferred)))

        required_ratio = required_hits / required_denominator
        preferred_ratio = preferred_hits / preferred_denominator

        relevance = (0.75 * required_ratio) + (0.25 * preferred_ratio)
        return round(min(1.0, max(0.0, relevance)), 4)

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

        internship_hits = len(
            re.findall(
                r"\b(internship|intern|summer analyst|co-op|coop|trainee|apprentice|externship|fellowship)\b",
                text,
            )
        )
        research_hits = len(
            re.findall(
                r"\b(research assistant|research intern|research engineer|undergraduate researcher|graduate researcher|lab assistant)\b",
                text,
            )
        )
        part_time_hits = len(
            re.findall(r"\b(part[- ]time|contract|freelance)\b", text)
        )

        full_time_role_hits = len(
            re.findall(
                r"\b(software engineer|backend engineer|frontend engineer|full stack developer|data engineer|data analyst|machine learning engineer|devops engineer)\b",
                text,
            )
        )
        full_time_marker_hits = len(re.findall(r"\b(full[- ]time|permanent role)\b", text))

        # Heuristic role-history signal: lines with date ranges + professional role titles.
        role_history_hits = len(
            re.findall(
                r"((20\d{2}|19\d{2}).{0,20}(present|current|20\d{2}|19\d{2})).{0,80}(engineer|developer|analyst|scientist)",
                text,
            )
        )

        full_time_hits = full_time_marker_hits + full_time_role_hits + role_history_hits

        if full_time_hits >= 2:
            return "full-time"
        if internship_hits >= 1:
            return "internship"
        if research_hits >= 1:
            return "research"
        if part_time_hits >= 1:
            return "part-time"
        if full_time_hits == 1:
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
        resume_text = self.extract_text_from_pdf(pdf_path)
        project_quality_score = self._estimate_project_quality_score(resume_text)
        project_relevance_score = self._estimate_project_relevance_score(resume_text, target_role)

        assessment = self.assessor.assess(
            target_role=target_role,
            candidate_skills=profile["skills"],
            candidate_years=profile["candidate_years"],
            projects_count=profile["projects_count"],
            experience_type=profile["experience_type"],
            project_quality_score=project_quality_score,
            project_relevance_score=project_relevance_score,
        )

        profile["project_quality_score"] = project_quality_score
        profile["project_relevance_score"] = project_relevance_score
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