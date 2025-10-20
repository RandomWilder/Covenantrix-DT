# Document-Scoped Query - Technical Plan

## Overview

Implement document-scoped queries using LightRAG's native `ids` parameter to filter retrieval to specific documents. When user selects one or more documents in the UI, queries will only return content from those documents. When no documents are selected, queries operate across the entire knowledge base as normal.

---

## Core Mapping Strategy

**Mapping Chain:**
```
User Document ID (UUID) 
  → content_hash (document_registry.json)
  → LightRAG doc-XXXXX (computed from hash)
  → chunks_list (kv_store_doc_status.json)
  → chunk IDs passed to LightRAG QueryParam.ids
```

**Key Files:**
- `document_registry.json`: User doc ID → content_hash
- `kv_store_doc_status.json`: LightRAG doc ID → chunks_list[]
- LightRAG native filtering via `QueryParam(ids=chunk_ids)`

---

## Backend Changes

### 1. Document-to-Chunk ID Mapper

**New File:** `backend/infrastructure/ai/document_chunk_mapper.py`

Create mapper utility that:
- Accepts list of user document IDs (UUIDs)
- Returns list of LightRAG chunk IDs

**Algorithm:**
1. Read `document_registry.json` to get `content_hash` for each user doc ID
2. Compute LightRAG doc ID format: `doc-{hash_prefix}` where hash_prefix is derived from content_hash (must match LightRAG's internal hashing algorithm)
3. Read `kv_store_doc_status.json`
4. For each computed LightRAG doc ID, extract `chunks_list`
5. Return flattened list of all chunk IDs from selected documents

**Key Function:**
```python
async def map_document_ids_to_chunk_ids(
    document_ids: List[str],
    storage_path: Path
) -> List[str]:
```

**Edge Cases:**
- Document ID not found in registry → skip with warning
- LightRAG doc ID not found in kv_store_doc_status.json → skip with warning
- Empty document_ids list → return empty list (signals "no filtering")
- Invalid/corrupted JSON files → raise exception

---

### 2. RAG Engine Query Modification

**File:** `backend/infrastructure/ai/rag_engine.py`

**Modify Function:** `query()` (line ~398-440)

Add `document_ids` parameter and implement chunk filtering:

**Changes:**
- Add parameter: `document_ids: Optional[List[str]] = None`
- Before calling LightRAG query:
  - If `document_ids` is provided and not empty:
    - Call `document_chunk_mapper.map_document_ids_to_chunk_ids()`
    - Get list of chunk IDs
    - Pass to `QueryParam(ids=chunk_ids)`
  - If `document_ids` is None or empty:
    - Use `QueryParam` without `ids` (current behavior)
- Update logging to indicate filtered vs unfiltered queries

**Modify Function:** `query_stream()` (line ~472-530)

Apply identical logic for streaming queries:
- Add same `document_ids` parameter
- Apply same chunk ID filtering before streaming
- Ensure filtered context flows through streaming response

---

### 3. Chat Service Integration

**File:** `backend/domain/chat/service.py`

**Modify Function:** `send_message_stream()` (line ~200-260)

Changes:
- Extract `document_ids` from chat context (already present in code at line ~220: `selected_documents = context.get("selectedDocuments", [])`)
- Pass `document_ids` to RAG query calls:
  - Line ~241-244: `query_stream()` call
  - Line ~376: `query()` call (if used in non-streaming path)

**No new parameters needed** - `document_ids` already flows from frontend via chat context.

---

### 4. Document Service Query Method

**File:** `backend/domain/documents/service.py`

**Modify Function:** `query_documents()` (line ~523-550)

Changes:
- Add `document_ids: Optional[List[str]] = None` parameter
- Pass `document_ids` to `rag_engine.query()` call
- Remove warning about filtering not being supported (line ~518-520)
- Update docstring to reflect filtering capability

---

### 5. Agent Data Access

**File:** `backend/infrastructure/ai/agent_data_access.py`

**Modify Function:** `query_documents()` calls (lines ~108, 114)

Changes:
- Add `document_ids` parameter to function signature
- Pass through to RAG engine queries
- Default to `None` to maintain current behavior for agents

---

### 6. LightRAG Storage Wrapper

**File:** `backend/infrastructure/storage/lightrag_storage.py`

**Modify Function:** `query_documents()` (line ~89-120)

Changes:
- Add `document_ids: Optional[List[str]] = None` parameter
- Pass through to underlying `rag_engine.query()` call
- Update method signature to match new interface

---

## Algorithm: LightRAG Doc ID Computation

**Critical:** Must replicate LightRAG's internal doc ID generation algorithm.

**Approach:**
1. LightRAG generates doc IDs as: `doc-{content_hash_prefix}`
2. The hash is computed from the document content text
3. Must use identical hashing to ensure match

**Implementation in `document_chunk_mapper.py`:**
```python
def compute_lightrag_doc_id(content_hash: str) -> str:
    """
    Compute LightRAG doc ID from content hash.
    Must match LightRAG's internal algorithm.
    
    Algorithm: doc-{first_32_chars_of_content_hash}
    """
    return f"doc-{content_hash[:32]}"
```

**Validation:** Test against existing documents in `kv_store_doc_status.json` to confirm algorithm matches.

---

## Frontend Changes

### 7. Chat Context Document Selection

**File:** `covenantrix-desktop/src/features/chat/ChatScreen.tsx`

**Current State:** Already sends `selectedDocuments` in chat context (verified in project knowledge).

**Required Changes:** None - document selection already flows to backend.

**Verification Points:**
- Confirm `selectedDocuments` array contains document UUIDs (not doc names)
- Ensure empty array is sent when no documents selected
- Validate selection state persists across messages in same conversation

---

### 8. UI Feedback for Scoped Queries

**File:** `covenantrix-desktop/src/features/chat/ChatScreen.tsx`

**Enhancement (Optional):**
Add visual indicator showing which documents are in scope:
- Display document names above chat input when documents selected
- Show "All documents" indicator when no selection
- Clear indication that query is scoped vs unscoped

**Implementation:** Display component similar to filter chips showing active document scope.

---

## Error Handling

### Backend Error Cases

1. **Invalid Document ID:**
   - Log warning and skip document
   - Continue processing remaining valid IDs
   - Don't fail entire query

2. **Missing kv_store_doc_status.json:**
   - Raise exception: "LightRAG storage not initialized"
   - Return error to frontend

3. **Empty chunk list after filtering:**
   - Allow query to proceed (LightRAG handles empty `ids` gracefully)
   - Return empty results with appropriate message

4. **Corrupted JSON files:**
   - Catch JSON parsing errors
   - Log error with file path
   - Raise exception with user-friendly message

### Frontend Error Handling

1. **No results from scoped query:**
   - Show message: "No relevant information found in the selected document(s)"
   - Suggest expanding search to all documents

2. **Backend filtering error:**
   - Display error message from backend
   - Fall back to unfiltered query with user confirmation

---

## Backward Compatibility

**Zero Breaking Changes:**
- All functions default `document_ids=None` (current behavior)
- Existing API calls work unchanged
- Frontend works without modification (sends empty array when no selection)
- Query behavior unchanged when `document_ids` not provided

---

## Testing Strategy

### Unit Tests

1. **Document Chunk Mapper:**
   - Test single document mapping
   - Test multiple document mapping
   - Test invalid document ID handling
   - Test empty input handling

2. **RAG Engine:**
   - Test filtered query with valid chunk IDs
   - Test unfiltered query (document_ids=None)
   - Test empty chunk ID list

### Integration Tests

1. **End-to-End Query Flow:**
   - Upload 3 documents
   - Select document 1 → query → verify results only from doc 1
   - Select documents 1+2 → query → verify results only from docs 1+2
   - Deselect all → query → verify results from all 3 documents

2. **Cross-Document Entity Queries:**
   - Query for entity present in multiple documents
   - With selection: verify entity context limited to selected docs
   - Without selection: verify entity shows cross-document relationships

### Manual Testing

1. **User Flow Validation:**
   - Select single document, ask document-specific question
   - Verify no content from other documents appears
   - Deselect, ask same question
   - Verify full knowledge base is used

2. **Performance Testing:**
   - Test with 10+ documents selected
   - Verify chunk ID list size is reasonable
   - Measure query latency vs unfiltered queries

---

## Logging Strategy

Add structured logging at key points:

1. **Mapper:** Log user doc IDs → chunk IDs mapping
2. **RAG Engine:** Log filtered vs unfiltered query indication
3. **Query Results:** Log number of documents in scope for query
4. **Errors:** Log all mapping failures with document IDs

**Log Format:**
```
[DocumentFilter] Mapping 2 documents to chunks
[DocumentFilter] Found 45 chunks from documents: [doc-abc..., doc-def...]
[RAGEngine] Executing FILTERED query (45 chunks in scope)
[RAGEngine] Executing UNFILTERED query (all documents)
```

---

## Files Modified Summary

### New Files (1)
- `backend/infrastructure/ai/document_chunk_mapper.py`

### Modified Files (6)
1. `backend/infrastructure/ai/rag_engine.py` - Add chunk filtering to query methods
2. `backend/domain/chat/service.py` - Pass document_ids to RAG queries
3. `backend/domain/documents/service.py` - Add document_ids parameter
4. `backend/infrastructure/ai/agent_data_access.py` - Add document_ids parameter
5. `backend/infrastructure/storage/lightrag_storage.py` - Add document_ids parameter
6. `covenantrix-desktop/src/features/chat/ChatScreen.tsx` - Optional UI feedback

### Storage Files (Read-Only)
- `document_registry.json` - Read for content_hash lookup
- `kv_store_doc_status.json` - Read for chunks_list lookup

---

## Success Criteria

- ✅ User selects single document → query returns only content from that document
- ✅ User selects multiple documents → query returns only content from those documents  
- ✅ User deselects all documents → query returns content from entire knowledge base
- ✅ Cross-document entities remain connected when no selection active
- ✅ No breaking changes to existing functionality
- ✅ Query performance acceptable with 10+ documents selected
