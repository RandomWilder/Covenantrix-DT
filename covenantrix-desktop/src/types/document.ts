/**
 * Document Type Definitions
 * Matches backend/models/document_models.py Pydantic models
 */

// ===== ENUMS (matching backend) =====

export enum DocumentType {
    CONTRACT = "contract",
    LEASE_AGREEMENT = "lease_agreement",
    EMPLOYMENT = "employment",
    LEGAL = "legal",
    GENERAL = "general",
    FINANCIAL = "financial",
    TECHNICAL = "technical"
  }
  
  export enum QueryMode {
    NAIVE = "naive",      // Basic vector similarity search
    LOCAL = "local",      // Entity-focused local search
    GLOBAL = "global",    // Community-based global search
    HYBRID = "hybrid",    // Combines local and global (recommended)
    MIX = "mix"          // Integrates knowledge graph and vector retrieval
  }
  
  export enum OCRProvider {
    GOOGLE_VISION = "google_vision",
    NONE = "none"
  }
  
  export enum RiskLevel {
    HIGH = "high",
    MEDIUM = "medium",
    LOW = "low",
    UNKNOWN = "unknown"
  }
  
  // ===== REQUEST MODELS (matching backend Pydantic) =====
  
  export interface DocumentUploadRequest {
    filename: string;
    document_type?: DocumentType;
    enable_ocr?: boolean;
    ocr_provider?: OCRProvider;
    metadata?: Record<string, any>;
  }
  
  export interface DocumentQueryRequest {
    query: string;
    mode?: QueryMode;
    only_need_context?: boolean;
    document_ids?: string[];
    max_tokens?: number;
  }
  
  export interface AnalysisRequest {
    query_mode?: QueryMode;
    focus_areas?: string[];
    document_ids?: string[];
    include_summary?: boolean;
  }
  
  export interface ResetStorageRequest {
    confirm: boolean;
  }
  
  // ===== RESPONSE MODELS (matching backend Pydantic) =====
  
  export interface DocumentUploadResponse {
    success: boolean;
    processing_id: string;
    filename: string;
    char_count?: number;
    message: string;
    timestamp?: string;
  }
  
  export interface DocumentQueryResponse {
    success: boolean;
    query: string;
    response: string;
    mode: string;
    processing_time: number;
    timestamp: string;
    documents_available: number;
    error?: string;
  }
  
  export interface AnalysisResponse {
    success: boolean;
    query_mode: QueryMode;
    analysis_summary: string;
    key_findings: string[];
    documents_analyzed: number;
    processing_time: number;
    timestamp: string;
    error?: string;
  }
  
  export interface DocumentInfo {
    document_id: string;
    filename: string;
    document_type?: DocumentType; // Optional since API doesn't always provide it
    file_size_mb: number;
    char_count: number;
    chunk_count: number;
    processed_at: string | null;
    ocr_used?: boolean; // Optional since API uses ocr_applied
    ocr_applied?: boolean; // From API response
    status?: string; // From API response
    uploaded_at?: string; // From API response
    ocr_cost?: number;
    legal_intelligence_applied?: boolean;
    complexity_score?: number;
    risk_level?: RiskLevel;
    legal_entity_count?: number;
    key_insights?: string[];
    metadata_summary?: Record<string, any>;
  }
  
  export interface DocumentListResponse {
    success: boolean;
    documents: DocumentInfo[];
    total_count: number;
    timestamp: string;
    error?: string;
  }
  
  export interface DocumentDetailsResponse {
    success: boolean;
    document: Record<string, any>;
    timestamp: string;
    error?: string;
  }
  
  export interface DocumentDeleteResponse {
    success: boolean;
    document_id: string;
    message: string;
    timestamp: string;
    warning?: string;
    error?: string;
  }
  
  export interface ResetStorageResponse {
    success: boolean;
    message: string;
    timestamp: string;
    error?: string;
  }
  
  export interface HealthResponse {
    status: string;
    timestamp: string;
    python_version: string;
    working_directory: string;
    platform: string;
    dependencies: Record<string, string>;
  }
  
  export interface SystemHealthResponse {
    success: boolean;
    rag_engine: Record<string, any>;
    document_processor: Record<string, any>;
    supported_formats?: Record<string, any>;
    performance_summary?: Record<string, any>;
    error?: string;
  }
  
  export interface ProcessingStatusResponse {
    processing_id: string;
    stage: string;
    progress: number;
    message: string;
    status: 'processing' | 'completed' | 'error';
    timestamp: string;
    result?: any;
    error?: string;
  }
  
  // ===== COMPONENT MODELS =====
  
  export interface ProcessingStats {
    total_documents: number;
    total_chunks: number;
    total_queries: number;
    average_processing_time: number;
  }
  
  export interface RAGHealthStatus {
    engine_initialized: boolean;
    working_directory: string;
    total_documents: number;
    storage_mode: string;
  }
  
  export interface ErrorDetail {
    code: string;
    message: string;
    details?: Record<string, any>;
  }
  
  export interface APIResponse<T = any> {
    success: boolean;
    data?: T;
    error?: ErrorDetail;
    timestamp: string;
  }
  
  export interface OCRCostEstimate {
    estimated_pages: number;
    cost_per_page: number;
    total_cost: number;
    currency: string;
  }

  // ===== UPLOAD TYPES =====

  export interface BatchUploadItem {
    filename: string;
    document_id?: string;
    success: boolean;
    error?: string;
    file_size?: number;
  }

  export interface BatchUploadResponse {
    success: boolean;
    total_files: number;
    successful_uploads: number;
    failed_uploads: number;
    results: BatchUploadItem[];
    message: string;
  }

  export interface GoogleDriveFileInfo {
    file_id: string;
    name: string;
    mime_type: string;
    size?: number;
    modified_time?: string;
    web_view_link?: string;
  }

  export interface GoogleDriveListResponse {
    success: boolean;
    files: GoogleDriveFileInfo[];
    next_page_token?: string;
  }

  export interface UploadFileItem {
    id: string;
    file: File;
    status?: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
    progress?: number;
    error?: string;
    stage?: DocumentProgressStage;
    stageMessage?: string;
  }

  export interface UploadProgress {
    total: number;
    completed: number;
    failed: number;
    current?: string;
    files: UploadFileItem[];
  }

  // ===== PROGRESS STREAMING TYPES =====

  export type DocumentProgressStage = 
    | 'initializing'
    | 'reading' 
    | 'understanding'
    | 'building_connections'
    | 'finalizing'
    | 'completed'
    | 'failed';

  export interface DocumentProgressEvent {
    filename: string;
    document_id?: string;
    stage: DocumentProgressStage;
    message: string;
    progress_percent: number;
    timestamp: string;
    error?: string;
  }

  export interface BatchProgressEvent {
    total_files: number;
    current_file_index: number;
    file_progress: DocumentProgressEvent;
    overall_progress_percent: number;
  }

  // ===== ENTITY EXTRACTION TYPES =====

  export interface EntityInfo {
    name: string;
    description: string;
  }

  export interface EntitySummary {
    people: EntityInfo[];
    organizations: EntityInfo[];
    locations: EntityInfo[];
    financial: EntityInfo[];
    dates_and_terms: EntityInfo[];
  }

  export interface DocumentEntitiesResponse {
    document_id: string;
    document_name: string;
    entity_summary: EntitySummary;
  }