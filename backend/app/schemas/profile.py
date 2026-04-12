from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    target_role: str = Field(min_length=2, max_length=120)
    skills: list[str] = Field(default_factory=list)
    projects_count: int = Field(default=0, ge=0, le=20)
    candidate_years: float = Field(default=0.0, ge=0, le=20)
    experience_type: str = Field(default="none")


class ProfileOut(BaseModel):
    target_role: str
    skills: list[str]
    projects_count: int
    candidate_years: float
    experience_type: str
