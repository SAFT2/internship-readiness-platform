from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_role = Column(String(120), nullable=False)
    overall_score = Column(Float, nullable=False)
    readiness_level = Column(String(40), nullable=False)
    source_type = Column(String(20), nullable=False, default="profile")
    resume_filename = Column(String(255), nullable=True)
    resume_sha256 = Column(String(64), nullable=True)
    resume_uri = Column(String(500), nullable=True)
    score_breakdown_json = Column(Text, nullable=False)
    missing_required_skills_json = Column(Text, nullable=False)
    recommendations_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="assessments")
