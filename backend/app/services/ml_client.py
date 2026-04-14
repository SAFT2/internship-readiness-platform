from typing import Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings


class MLServiceClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.ml_service_url).rstrip("/")
        self.session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=0.5,
            allowed_methods=frozenset({"GET", "POST"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method: str, path: str, timeout: int, **kwargs: Any) -> requests.Response:
        response = self.session.request(method=method, url=f"{self.base_url}{path}", timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def health(self) -> dict[str, Any]:
        response = self._request("GET", "/health", timeout=10)
        return response.json()

    def parse_resume_and_assess(self, resume_bytes: bytes, filename: str, role: str) -> dict[str, Any]:
        files = {
            "resume": (filename, resume_bytes, "application/pdf"),
        }
        data = {
            "role": role,
        }

        response = self._request(
            "POST",
            "/parse-resume",
            files=files,
            data=data,
            timeout=90,
        )
        return response.json()

    def list_roles(self) -> list[str]:
        response = self._request("GET", "/roles", timeout=15)
        payload = response.json()

        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            return []

        return [str(role) for role in roles if str(role).strip()]

    def get_role_details(self, role_name: str) -> dict[str, Any]:
        safe_role_name = quote(role_name, safe="")
        response = self._request("GET", f"/roles/{safe_role_name}", timeout=15)
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
        response = self.session.request(
            method="POST",
            url=f"{self.base_url}/assess-profile",
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
