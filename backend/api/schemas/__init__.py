"""
API Schemas
All Pydantic request/response models
"""
from api.schemas.common import (
    BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse
)
from api.schemas.documents import (
    DocumentUploadResponse, DocumentResponse, DocumentListResponse,
    QueryRequest, QueryResponse
)
from api.schemas.analytics import (
    ClassificationRequest, ClassificationResponse,
    ExtractionRequest, ExtractionResponse,
    AnalyticsRequest, AnalyticsResponse,
    PortfolioSummaryResponse, UpdateClassificationRequest
)
from api.schemas.agents import (
    AgentCreateRequest, AgentResponse, AgentListResponse,
    TaskSubmitRequest, TaskResponse, TaskStatusResponse,
    TaskResultResponse, SystemStatusResponse
)
from api.schemas.integrations import (
    OAuthUrlResponse, OAuthCallbackRequest, OAuthCallbackResponse,
    AccountResponse, AccountListResponse,
    DriveFileResponse, DriveFileListResponse,
    DriveDownloadRequest, DriveDownloadResponse,
    IntegrationStatusResponse
)

__all__ = [
    # Common
    "BaseResponse", "ErrorResponse", "PaginationParams", "PaginatedResponse",
    # Documents
    "DocumentUploadResponse", "DocumentResponse", "DocumentListResponse",
    "QueryRequest", "QueryResponse",
    # Analytics
    "ClassificationRequest", "ClassificationResponse",
    "ExtractionRequest", "ExtractionResponse",
    "AnalyticsRequest", "AnalyticsResponse",
    "PortfolioSummaryResponse", "UpdateClassificationRequest",
    # Agents
    "AgentCreateRequest", "AgentResponse", "AgentListResponse",
    "TaskSubmitRequest", "TaskResponse", "TaskStatusResponse",
    "TaskResultResponse", "SystemStatusResponse",
    # Integrations
    "OAuthUrlResponse", "OAuthCallbackRequest", "OAuthCallbackResponse",
    "AccountResponse", "AccountListResponse",
    "DriveFileResponse", "DriveFileListResponse",
    "DriveDownloadRequest", "DriveDownloadResponse",
    "IntegrationStatusResponse"
]