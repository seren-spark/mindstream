import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.agent import (
    AgentGenerateRequest,
    AgentGenerationJobResponse,
    AgentVersionResponse,
    ExpertAgentCreate,
    ExpertAgentResponse,
    ExpertAgentUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.agent_generator_service import AgentGeneratorService
from app.services.agent_service import AgentInvalidStateError, AgentNotFoundError, AgentService

router = APIRouter(prefix="/knowledge-bases/{knowledge_base_id}/agents", tags=["agents"])


def _job_response(db: Session, job) -> AgentGenerationJobResponse:
    agent = None
    if job.agent_id:
        try:
            agent = AgentService.get(db, job.knowledge_base_id, job.agent_id)
        except AgentNotFoundError:
            pass
    return AgentGenerationJobResponse(
        id=job.id,
        knowledge_base_id=job.knowledge_base_id,
        agent_id=job.agent_id,
        status=job.status,
        stage=job.stage,
        progress_message=job.progress_message,
        error_message=job.error_message,
        model_name=job.model_name,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
        agent=ExpertAgentResponse.model_validate(agent) if agent else None,
    )


@router.post("/generate", response_model=AgentGenerationJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_generate(
    knowledge_base_id: int,
    _: AgentGenerateRequest | None = None,
    db: Session = Depends(get_db),
) -> AgentGenerationJobResponse:
    job = AgentGeneratorService.create_job(db, knowledge_base_id)
    asyncio.create_task(AgentGeneratorService.run_job(job.id))
    return _job_response(db, job)


@router.get("/generate/{job_id}", response_model=AgentGenerationJobResponse)
def get_generate_job(
    knowledge_base_id: int,
    job_id: str,
    db: Session = Depends(get_db),
) -> AgentGenerationJobResponse:
    try:
        job = AgentService.get_job(db, knowledge_base_id, job_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生成任务不存在") from exc
    return _job_response(db, job)


@router.get("", response_model=PaginatedResponse[ExpertAgentResponse])
def list_agents(
    knowledge_base_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ExpertAgentResponse]:
    items, total = AgentService.list_agents(
        db, knowledge_base_id, status=status_filter, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[ExpertAgentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ExpertAgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    knowledge_base_id: int,
    payload: ExpertAgentCreate,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.create_manual(db, knowledge_base_id, payload)
    except AgentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return ExpertAgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=ExpertAgentResponse)
def get_agent(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    return ExpertAgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=ExpertAgentResponse)
def update_agent(
    knowledge_base_id: int,
    agent_id: str,
    payload: ExpertAgentUpdate,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.update(db, knowledge_base_id, agent_id, payload)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    except AgentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return ExpertAgentResponse.model_validate(agent)


@router.post("/{agent_id}/publish", response_model=ExpertAgentResponse)
def publish_agent(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.publish(db, knowledge_base_id, agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    except AgentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return ExpertAgentResponse.model_validate(agent)


@router.post("/{agent_id}/archive", response_model=ExpertAgentResponse)
def archive_agent(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.archive(db, knowledge_base_id, agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    return ExpertAgentResponse.model_validate(agent)


@router.post("/{agent_id}/regenerate", response_model=ExpertAgentResponse)
async def regenerate_agent(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> ExpertAgentResponse:
    try:
        agent = AgentService.get(db, knowledge_base_id, agent_id)
        agent = await AgentGeneratorService.regenerate_agent(db, agent)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ExpertAgentResponse.model_validate(agent)


@router.get("/{agent_id}/versions", response_model=list[AgentVersionResponse])
def list_versions(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> list[AgentVersionResponse]:
    try:
        versions = AgentService.list_versions(db, knowledge_base_id, agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    return [AgentVersionResponse.model_validate(v) for v in versions]


@router.get("/{agent_id}/versions/{version_id}", response_model=AgentVersionResponse)
def get_version(
    knowledge_base_id: int,
    agent_id: str,
    version_id: str,
    db: Session = Depends(get_db),
) -> AgentVersionResponse:
    try:
        version = AgentService.get_version(db, knowledge_base_id, agent_id, version_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在") from exc
    return AgentVersionResponse.model_validate(version)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    knowledge_base_id: int,
    agent_id: str,
    db: Session = Depends(get_db),
) -> None:
    try:
        AgentService.delete(db, knowledge_base_id, agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent 不存在") from exc
    except AgentInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
