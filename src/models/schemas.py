from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    name: str
    url: str


class StartupData(BaseModel):
    employeeCount: Optional[int] = None


class StartupEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source: Source
    content: dict
    collectedAt: datetime


class ProductEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source: Source
    content: dict
    collectedAt: datetime


class ResearchPaperContent(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    paper_url: str
    github_url: Optional[str] = None
    github_stars: Optional[int] = None
    published_date: datetime


class ResearchPaperEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    content: ResearchPaperContent
    collectedAt: datetime


class JobContent(BaseModel):
    company: str
    date: datetime
    is_remote: bool
    role_family: str


class JobEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    content: JobContent
    collectedAt: datetime