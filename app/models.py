from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    file_path = Column(String)
    status = Column(String, default="pending") # pending, processing, completed, failed
    
    parsed_data = relationship("ParsedData", back_populates="resume", uselist=False)
    scores = relationship("Score", back_populates="resume")

class ParsedData(Base):
    __tablename__ = "parsed_data"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("resumes.id"))
    skills = Column(JSON)
    experience = Column(JSON)
    education = Column(JSON)
    experience_years = Column(Float, default=0.0)
    
    resume = relationship("Resume", back_populates="parsed_data")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    job_description = Column(Text)
    
    scores = relationship("Score", back_populates="job")

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("resumes.id"))
    job_id = Column(String, ForeignKey("jobs.id"))
    original_score = Column(Float)
    normalized_score = Column(Float)
    adjusted_score = Column(Float)
    rank = Column(Integer)
    
    resume = relationship("Resume", back_populates="scores")
    job = relationship("Job", back_populates="scores")

class JobQueue(Base):
    __tablename__ = "job_queue"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, index=True)
    status = Column(String) # pending, processing, completed, failed
    type = Column(String) # parse, score
