# Document-Specific Query Implementation Plan
## Smart Mode Switching with Naive Mode

---

## Objective
Achieve 95%+ document isolation by automatically switching to **NAIVE mode** when documents are selected, eliminating entity cross-contamination while maintaining optimal performance.

---

## Key Insight
**NAIVE mode = pure chunk retrieval = zero entity leakage**
- No graph traversal
- No entity/relationship extraction at query time
- Direct chunk vector similarity only
- Perfect for document-specific queries

---

## Implementation Strategy

### **Phase 1: Core Engine Changes** (3-4 hours)

#### **File 1: `backend/infrastructure/ai/rag_engine.py`**

**Modify: `query()` method (line ~398)**

```python
async def query(
    self,
    query: str,
    mode: Optional[str] = None,
    top_k: Optional[int] = None,
    only_context: bool = False,
    document_ids: Optional[List[str]] = None  # NEW
) -> Dict[str, Any]:
    """Query with automatic mode optimization"""
    
    # Smart mode selection
    if document_ids:
        # Document-specific → FORCE naive mode
        effective_mode = "naive"
        
        # Map documents to chunk IDs
        from infrastructure.ai.document_chunk_mapper import DocumentChunkMapper
        mapper = DocumentChunkMapper(Path(self.working_dir))
        chunk_ids, _ = mapper.map_documents_to_chunk_ids(document_ids)
        
        # Build params with chunk filtering
        params = QueryParam(
            mode="naive",
            top_k=top_k or self.top_k or 5,
            only_need_context=only_context,
            ids=chunk_ids if chunk_ids else None
        )
        
        self.logger.info(
            f"📄 Document-scoped query: {len(document_ids)} docs → "
            f"{len(chunk_ids)} chunks (NAIVE mode)"
        )
    else:
        # Global query → use configured mode
        effective_mode = mode or self.search_mode or "hybrid"
        
        params = QueryParam(
            mode=effective_mode,
            top_k=top_k or self.top_k or 5,
            only_need_context=only_context,
            enable_rerank=self.use_reranking and effective_mode in ["hybrid", "mix"]
        )
        
        self.logger.info(f"🌐 Cross-document query (mode: {effective_mode})")
    
    # Execute query (existing code)
    try:
        result = await self._rag.aquery(query, param=params)
    except Exception as e:
        # Existing error handling
        ...
    
    return {
        "success": True,
        "query": query,
        "response": result,
        "mode": effective_mode,
        "document_scope": "filtered" if document_ids else "all"
    }
```

**Modify: `query_stream()` method (line ~472)**

Apply identical logic:
- Add `document_ids` parameter
- Same smart mode selection
- Same chunk ID filtering
- Log scoped vs unscoped

---

#### **File 2: `backend/infrastructure/ai/document_chunk_mapper.py`**

**Status:** Already implemented (per project knowledge)

**Verify:**
- `map_documents_to_chunk_ids()` returns chunk IDs correctly
- Handles invalid document IDs gracefully
- Logs mapping operations

---

### **Phase 2: Service Integration** (1-2 hours)

#### **File 3: `backend/domain/chat/service.py`**

**Modify: `send_message_stream()` (line ~241-244)**

Already extracts `document_ids` from context. Just ensure it passes to RAG:

```python
# Existing: selected_documents = context.get("selectedDocuments", [])

# Ensure this flows to RAG query:
async for chunk in self.rag_engine.query_stream(
    query=final_query,
    document_ids=selected_documents  # ADD THIS
):
    yield chunk
```

**Modify: Line ~376 (non-streaming path if exists)**

Same change for synchronous query.

---

#### **File 4: `backend/domain/documents/service.py`**

**Modify: `query_documents()` (line ~523)**

```python
async def query_documents(
    self,
    query: str,
    document_ids: Optional[List[str]] = None  # ADD
) -> Dict[str, Any]:
    """Query with optional document filtering"""
    
    # Remove old warning (lines 518-520)
    
    return await self.rag_engine.query(
        query=query,
        document_ids=document_ids  # ADD
    )
```

---

#### **File 5: `backend/infrastructure/ai/agent_data_access.py`**

**Modify: `query_documents()` calls (lines ~108, 114)**

Add `document_ids` parameter, default to `None`:

```python
async def query_documents(
    self,
    query: str,
    document_ids: Optional[List[str]] = None  # ADD
) -> str:
    result = await self.rag_engine.query(
        query,
        document_ids=document_ids  # ADD
    )
    return result.get("response", "")
```

---

#### **File 6: `backend/infrastructure/storage/lightrag_storage.py`**

**Modify: `query_documents()` (line ~89)**

Pass through `document_ids`:

```python
async def query_documents(
    self,
    query: str,
    document_ids: Optional[List[str]] = None  # ADD
) -> Dict[str, Any]:
    return await self.rag_engine.query(
        query,
        document_ids=document_ids  # ADD
    )
```

---

### **Phase 3: UI Feedback** (1 hour)

#### **File 7: `covenantrix-desktop/src/features/chat/ChatScreen.tsx`**

**Add visual indicator** (non-breaking, optional but recommended):

```tsx
{/* Below chat input or in header */}
{selectedDocuments.length > 0 && (
  <div className="query-mode-indicator">
    <FileIcon className="w-4 h-4" />
    <span className="text-sm text-muted-foreground">
      Searching in {selectedDocuments.length} document(s) · Focused mode
    </span>
  </div>
)}

{selectedDocuments.length === 0 && (
  <div className="query-mode-indicator">
    <GlobeIcon className="w-4 h-4" />
    <span className="text-sm text-muted-foreground">
      Searching all documents · Graph-enhanced mode
    </span>
  </div>
)}
```

**Styling:**
- Subtle, non-intrusive
- Uses existing design system
- Optional: tooltip explaining modes

---

## Performance Considerations

### **No Overhead When Not Filtering:**
- `document_ids=None` → direct pass-through to existing logic
- Zero performance impact on global queries

### **Naive Mode is FASTER:**
- No graph traversal
- No entity/relationship queries
- Smaller context (chunks only)
- Lower token usage

### **Chunk Mapping is O(n):**
- Where n = number of selected documents
- Typically < 10 documents
- File I/O cached by OS
- ~5-10ms overhead

---

## Testing Strategy

### **Test Case 1: Single Document Isolation**
1. Upload 2 docs: Doc A (ML intro), Doc B (ML datasets)
2. Select Doc A only
3. Query: "What is machine learning?"
4. **Expected:** Only content from Doc A, no mention of datasets
5. **Verify:** Check response contains ONLY Doc A content

### **Test Case 2: Multi-Document Scope**
1. Select Doc A + Doc B
2. Query: "What is machine learning?"
3. **Expected:** Content from both documents
4. **Verify:** Response mentions both intro AND datasets

### **Test Case 3: Global Query**
1. Deselect all documents
2. Query: "What is machine learning?"
3. **Expected:** Cross-document insights, entity connections
4. **Verify:** Response uses graph relationships

### **Test Case 4: Hebrew Language**
1. Upload Hebrew document
2. Select it
3. Query in Hebrew
4. **Expected:** Document-specific response in Hebrew

---

## Validation Checklist

- [ ] NAIVE mode activated when documents selected
- [ ] HYBRID/MIX mode used when no selection
- [ ] Chunk IDs correctly mapped
- [ ] No entity leakage in document-specific queries
- [ ] Backward compatibility maintained
- [ ] Performance acceptable (< 3s queries)
- [ ] UI indicator shows mode
- [ ] Logging tracks scoped vs unscoped queries
- [ ] Hebrew queries work correctly
- [ ] Error handling for invalid document IDs

---

## Rollback Plan

If issues arise:
1. Set `document_ids=None` in all service calls
2. System reverts to current behavior
3. No data loss, no breaking changes

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Document Isolation Accuracy | 95%+ |
| Query Speed (Scoped) | < 2.5s |
| Query Speed (Global) | < 3s |
| Zero Cross-Document Leaks | 100% |
| Backward Compatibility | 100% |

---

## Timeline

- **Phase 1:** 3-4 hours
- **Phase 2:** 1-2 hours  
- **Phase 3:** 1 hour
- **Testing:** 2-3 hours

**Total: 1 day of focused work**

---

## Files Modified Summary

**6 Backend Files:**
1. `backend/infrastructure/ai/rag_engine.py` - Smart mode selection
2. `backend/domain/chat/service.py` - Pass document_ids
3. `backend/domain/documents/service.py` - Add parameter
4. `backend/infrastructure/ai/agent_data_access.py` - Add parameter
5. `backend/infrastructure/storage/lightrag_storage.py` - Pass through
6. *(Existing)* `backend/infrastructure/ai/document_chunk_mapper.py` - Already implemented

**1 Frontend File:**
1. `covenantrix-desktop/src/features/chat/ChatScreen.tsx` - UI indicator

**Total: 7 files, minimal changes, zero breaking changes**
