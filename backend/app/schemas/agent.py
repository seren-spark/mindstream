from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

AgentStatus = Literal["draft", "published", "archived"]
AgentTone = Literal["professional", "concise", "detailed"]
JobStatus = Literal["pending", "running", "succeeded", "failed"]


class AgentProfileGenerated(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    persona: str = Field(min_length=10, max_length=2000)
    tone: AgentTone = "professional"
    welcome_message: str = Field(min_length=1, max_length=800)
    suggested_questions: list[str] = Field(min_length=1, max_length=5)
    avatar_emoji: str = Field(default="🤖", max_length=16)

    @field_validator("suggested_questions")
    @classmethod
    def validate_questions(cls, v: list[str]) -> list[str]:
        cleaned = [q.strip() for q in v if q.strip()]
        if not cleaned:
            raise ValueError("至少需要一个示例问题")
        return cleaned[:5]


class ExpertAgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    persona: str = Field(default="", max_length=2000)
    tone: AgentTone = "professional"
    custom_instructions: str | None = Field(default=None, max_length=1000)
    welcome_message: str = Field(default="你好，我是你的知识库助手。", max_length=800)
    suggested_questions: list[str] = Field(default_factory=list)
    avatar_type: str = Field(default="emoji", max_length=20)
    avatar_value: str = Field(default="🤖", max_length=500)


class ExpertAgentUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    persona: str | None = Field(default=None, max_length=2000)
    tone: AgentTone | None = None
    custom_instructions: str | None = Field(default=None, max_length=1000)
    welcome_message: str | None = Field(default=None, max_length=800)
    suggested_questions: list[str] | None = None
    avatar_type: str | None = Field(default=None, max_length=20)
    avatar_value: str | None = Field(default=None, max_length=500)


class ExpertAgentResponse(BaseModel):
    id: str
    knowledge_base_id: int
    slug: str
    name: str
    description: str
    persona: str
    tone: str
    custom_instructions: str | None
    welcome_message: str
    suggested_questions: list[str]
    avatar_type: str
    avatar_value: str
    status: str
    current_version_id: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version_number: int
    source: str
    profile_snapshot: dict
    prompt_snapshot: str
    generation_job_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentGenerationJobResponse(BaseModel):
    id: str
    knowledge_base_id: int
    agent_id: str | None
    status: str
    stage: str | None
    progress_message: str | None
    error_message: str | None
    model_name: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    agent: ExpertAgentResponse | None = None

    model_config = {"from_attributes": True}


class AgentGenerateRequest(BaseModel):
    """可选：指定名称前缀等，当前留空使用全自动生成。"""

    pass
