from typing import Any

import requests

from app.core.config import settings


class MLServiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ml_service_url).rstrip("/")

    def health(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/health", timeout=10)
        response.raise_for_status()
        return response.json()

    def parse_resume_and_assess(self, resume_bytes: bytes, filename: str, role: str) -> dict[str, Any]:
        files = {
            "resume": (filename, resume_bytes, "application/pdf"),
        }
        data = {
            "role": role,
        }

        response = requests.post(
            f"{self.base_url}/parse-resume",
            files=files,
            data=data,
            timeout=90,
        )
        response.raise_for_status()
        return response.json()

    def list_roles(self) -> list[str]:
        response = requests.get(f"{self.base_url}/roles", timeout=15)
        response.raise_for_status()
        payload = response.json()

        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            return []

        return [str(role) for role in roles if str(role).strip()]

    def get_role_details(self, role_name: str) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/roles/{role_name}", timeout=15)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return {}
        return payload

    def assess_profile(
        self,
        target_role: str,
        candidate_skills: list[str],
        candidate_years: float,
        projects_count: int,
        experience_type: str,
    ) -> dict[str, Any]:
        payload = {
            "target_role": target_role,
            "candidate_skills": candidate_skills,
            "candidate_years": candidate_years,
            "projects_count": projects_count,
            "experience_type": experience_type,
        }
        response = requests.post(
            f"{self.base_url}/assess-profile",
            json=payload,
            timeout=60,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if response.status_code < 500:
                detail = "Invalid profile assessment request"
                try:
                    error_payload = response.json()
                    detail = str(error_payload.get("detail") or detail)
                except ValueError:
                    if response.text:
                        detail = response.text.strip()
                raise ValueError(detail) from exc
            raise
        return response.json()
