from typing import Any

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    tier: str = Field(default="free")


class RegisterResponse(BaseModel):
    api_key: str
    tier: str


class ResumeRequest(BaseModel):
    raw_experience_text: str = Field(min_length=1)
    export_pdf: bool = False


class CoverLetterRequest(BaseModel):
    job_description: str = Field(min_length=1)
    user_profile: str = Field(min_length=1)
    export_pdf: bool = False


class MeetingSummaryRequest(BaseModel):
    notes: str = Field(min_length=1)
    export_pdf: bool = False


class BusinessIdeaRequest(BaseModel):
    idea_dump: str = Field(min_length=1)
    export_pdf: bool = False


class AdCopyRequest(BaseModel):
    product_description: str = Field(min_length=1)
    export_pdf: bool = False


class GenerateResponse(BaseModel):
    task: str
    result_id: str
    structured_output: dict[str, Any]
    exports: dict[str, str | None]


class UsageResponse(BaseModel):
    api_key: str
    tier: str
    total_requests: int
    monthly_limit: int
    requests_last_minute: int
    per_minute_limit: int
