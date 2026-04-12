from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    target_role = Column(String(120), nullable=False, default="ML Intern")
    skills_csv = Column(Text, nullable=False, default="")
    projects_count = Column(Integer, nullable=False, default=0)
    candidate_years = Column(Float, nullable=False, default=0.0)
    experience_type = Column(String(40), nullable=False, default="none")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")
