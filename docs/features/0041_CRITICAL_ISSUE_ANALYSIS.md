# CRITICAL ISSUE: Document Filtering Bypass Analysis

## 🚨 Issue Summary
**Document filtering is being bypassed due to LightRAG QueryParam compatibility issues, resulting in cross-document contamination.**

## Evidence from Terminal Logs
```
[1] 18:14:51.055 > [Backend] 2025-10-20 18:14:51 - infrastructure.ai.document_chunk_mapper - INFO - [N/A] - Mapped 1 docs to 1 chunks; non-empty docs: 1
[1] 18:14:51.843 > [Backend Error] INFO: Naive query: 2 chunks (chunk_top_k: 20)
[1] 18:14:52.712 > [Backend Error] INFO: Successfully reranked: 2 chunks from 2 original chunks
[1] 18:14:52.715 > [Backend Error] INFO: Final context: 2 chunks
```

**Analysis:**
- ✅ DocumentChunkMapper: 1 document → 1 chunk (correct)
- ❌ LightRAG Query: 2 chunks in final context (contamination)
- ❌ **95%+ isolation requirement VIOLATED**

## Root Cause Analysis

### 1. QueryParam Compatibility Issue
**Location:** `backend/infrastructure/ai/rag_engine.py` lines 498-515

**Problem:** The code attempts to create QueryParam with `ids` parameter, but if LightRAG doesn't support it, it falls back to **unfiltered mode**.

```python
try:
    params = QueryParam(
        mode=query_mode,
        top_k=effective_top_k,
        only_need_context=only_context,
        enable_rerank=use_reranking and self._rag.rerank_model_func is not None,
        ids=ids_param  # ← This may not be supported
    )
except TypeError:
    # ← FALLBACK: Creates QueryParam WITHOUT ids parameter
    self.logger.warning("LightRAG QueryParam does not support 'ids'; proceeding UNFILTERED for this query")
    params = QueryParam(
        mode=query_mode,
        top_k=effective_top_k,
        only_need_context=only_context,
        enable_rerank=use_reranking and self._rag.rerank_model_func is not None
        # ← NO ids parameter = NO filtering
    )
```

### 2. Missing Log Evidence
The terminal logs don't show the warning message, which suggests either:
- The QueryParam creation succeeded but LightRAG ignored the `ids` parameter
- The `ids` parameter is supported but not working as expected
- The fallback is happening silently

### 3. LightRAG Behavior Issue
Even if the `ids` parameter is passed correctly, LightRAG may not be respecting it in naive mode, or there may be a bug in how LightRAG handles chunk filtering.

## Impact Assessment

### 🚨 CRITICAL: Document Isolation Failure
- **Expected:** 1 chunk (from selected document only)
- **Actual:** 2 chunks (cross-document contamination)
- **Isolation Rate:** 0% (complete failure)
- **Target:** 95%+ isolation

### 🚨 CRITICAL: Security/Privacy Risk
- Users selecting specific documents expect complete isolation
- Cross-document contamination violates user expectations
- Potential data leakage between documents

## Immediate Actions Required

### 1. Verify QueryParam Support
Check if the current LightRAG version supports the `ids` parameter in QueryParam.

### 2. Add Debug Logging
Add explicit logging to track:
- Whether QueryParam creation succeeds or fails
- What chunk IDs are being passed to LightRAG
- Whether LightRAG respects the `ids` parameter

### 3. Implement Alternative Filtering
If LightRAG doesn't support `ids` parameter, implement post-processing filtering:
- Retrieve all chunks from LightRAG
- Filter results to only include chunks from selected documents
- This ensures 100% isolation even if LightRAG doesn't support native filtering

## Recommended Fix

### Option 1: Post-Processing Filter (Immediate)
```python
# After LightRAG query, filter results to only selected document chunks
if document_ids and chunk_ids:
    # Filter the response to only include chunks from selected documents
    filtered_response = self._filter_response_by_chunks(result, chunk_ids)
    return filtered_response
```

### Option 2: LightRAG Version Check (Long-term)
- Verify LightRAG version and QueryParam support
- Update LightRAG if needed
- Implement proper `ids` parameter usage

### Option 3: Alternative LightRAG API (Research)
- Investigate if LightRAG has alternative filtering mechanisms
- Use different API endpoints that support document filtering

## Testing Strategy

### 1. Immediate Verification
- Add debug logging to track QueryParam creation
- Verify if `ids` parameter is being passed correctly
- Check if LightRAG is respecting the parameter

### 2. Isolation Testing
- Test with 2+ documents in the system
- Select 1 document for query
- Verify only chunks from that document are returned
- Measure isolation percentage

### 3. Regression Testing
- Ensure global queries still work correctly
- Verify performance is not significantly impacted
- Test error handling scenarios

## Priority: 🚨 CRITICAL
This issue completely undermines the document-specific query functionality and violates the core requirement of 95%+ document isolation. Immediate action is required.

---
**Status:** 🚨 CRITICAL ISSUE IDENTIFIED  
**Priority:** IMMEDIATE FIX REQUIRED  
**Impact:** COMPLETE ISOLATION FAILURE
