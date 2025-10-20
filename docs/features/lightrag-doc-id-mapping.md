# Store LightRAG Doc ID During Insertion

## Overview
Capture the LightRAG-generated document ID during insertion and store it in `document_registry.json` for reliable mapping during document-scoped queries.

---

## Step 1: Modify RAG Engine to Return LightRAG Doc ID

**File:** `backend/infrastructure/ai/rag_engine.py`

**Find:** `async def insert(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:`

**Replace entire method with:**

```python
async def insert(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Insert document into RAG and return LightRAG doc ID
    
    Args:
        text: Document text
        metadata: Optional metadata (not used by LightRAG)
        
    Returns:
        LightRAG document ID (e.g., "doc-abc123...")
        
    Raises:
        ServiceNotAvailableError: RAG engine not initialized
        Exception: Failed to retrieve doc ID after insertion
    """
    if not self.is_initialized or not self._rag:
        raise ServiceNotAvailableError(
            "RAG engine not initialized",
            service="rag_engine"
        )
    
    try:
        import json
        from pathlib import Path
        
        # Get existing doc IDs before insertion
        doc_status_file = Path(self.working_dir) / "kv_store_doc_status.json"
        existing_doc_ids = set()
        if doc_status_file.exists():
            with open(doc_status_file, 'r', encoding='utf-8') as f:
                existing_doc_ids = set(json.load(f).keys())
        
        # Insert document into LightRAG
        await self._rag.ainsert(text)
        self.logger.debug(f"Inserted {len(text)} chars into RAG")
        
        # Find the newly created doc ID
        if doc_status_file.exists():
            with open(doc_status_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
                new_doc_ids = set(new_data.keys()) - existing_doc_ids
                
                if new_doc_ids:
                    lightrag_doc_id = list(new_doc_ids)[0]
                    self.logger.info(f"Created LightRAG doc ID: {lightrag_doc_id}")
                    return lightrag_doc_id
        
        # If we can't find new doc ID, raise error
        raise Exception("Failed to retrieve LightRAG doc ID after insertion")
        
    except Exception as e:
        self.logger.error(f"RAG insert failed: {str(e)}")
        raise
```

---

## Step 2: Add Method to Store LightRAG Doc ID in Registry

**File:** `backend/infrastructure/storage/document_registry.py`

**Add this new method** after `register_document()` method:

```python
async def store_lightrag_doc_id(
    self,
    document_id: str,
    lightrag_doc_id: str
) -> bool:
    """
    Store LightRAG document ID for mapping
    
    Args:
        document_id: User document UUID
        lightrag_doc_id: LightRAG-generated doc ID (e.g., "doc-abc123...")
        
    Returns:
        True if successful
    """
    async with self._lock:
        try:
            data = self._read_registry()
            
            if document_id not in data["documents"]:
                self.logger.warning(f"Document not found in registry: {document_id}")
                return False
            
            # Store the LightRAG doc ID
            data["documents"][document_id]["lightrag_doc_id"] = lightrag_doc_id
            data["documents"][document_id]["updated_at"] = datetime.utcnow().isoformat()
            
            self._write_registry(data)
            self.logger.info(f"Stored LightRAG doc ID for {document_id}: {lightrag_doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store LightRAG doc ID: {e}")
            return False
```

---

## Step 3: Capture and Store During Document Processing

**File:** `backend/domain/documents/service.py`

**Find:** The `process_document()` method, locate the RAG insertion section (around line 90-100)

**Find this line:**
```python
success = await self.rag_engine.insert(extracted_content, metadata)
```

**Replace with:**
```python
# Insert into RAG and capture LightRAG doc ID
lightrag_doc_id = await self.rag_engine.insert(extracted_content, metadata)

# Store the mapping in registry
await self.registry.store_lightrag_doc_id(document.id, lightrag_doc_id)
```

---

## Step 4: Update Mapper to Use Stored LightRAG Doc ID

**File:** `backend/infrastructure/ai/document_chunk_mapper.py`

**Replace the `_match_doc_id()` method entirely:**

```python
def _match_doc_id(self, user_doc_id: str, doc_status: Dict) -> Optional[str]:
    """
    Get LightRAG doc ID from stored mapping in registry.
    Falls back to hash-based matching for legacy documents.
    
    Args:
        user_doc_id: User document UUID
        doc_status: Loaded kv_store_doc_status.json data
        
    Returns:
        LightRAG doc ID if found, None otherwise
    """
    try:
        # Load registry to get stored LightRAG doc ID
        registry_data = self._load_json(self.registry_file)
        doc_entry = registry_data.get("documents", {}).get(user_doc_id)
        
        if not doc_entry:
            logger.warning(f"Document {user_doc_id} not found in registry")
            return None
        
        # First, try to use stored LightRAG doc ID (new documents)
        lightrag_doc_id = doc_entry.get("lightrag_doc_id")
        if lightrag_doc_id:
            if lightrag_doc_id in doc_status:
                logger.debug(f"Found stored LightRAG doc ID: {lightrag_doc_id}")
                return lightrag_doc_id
            else:
                logger.warning(f"Stored LightRAG doc ID not found in kv_store: {lightrag_doc_id}")
        
        # Fallback: hash-based matching for legacy documents (uploaded before this change)
        content_hash = doc_entry.get("content_hash")
        if content_hash:
            logger.debug(f"Attempting hash-based fallback for legacy document {user_doc_id}")
            for candidate in self._candidate_lightrag_doc_ids(content_hash):
                if candidate in doc_status:
                    logger.info(f"Legacy document matched via hash: {candidate}")
                    return candidate
        
        return None
        
    except Exception as e:
        logger.error(f"Error matching doc ID for {user_doc_id}: {e}")
        return None
```

**Update `map_documents_to_chunk_ids()` method:**

**Find the loop that processes each document_id, replace:**

```python
for doc_id in document_ids:
    content_hash = content_hashes.get(doc_id)
    if not content_hash:
        logger.warning(f"Skipping doc without content_hash: {doc_id}")
        per_doc[doc_id] = []
        continue

    lightrag_doc_id = self._match_doc_id(content_hash, doc_status)
```

**With:**

```python
for doc_id in document_ids:
    # Use doc_id directly (not content_hash) for matching
    lightrag_doc_id = self._match_doc_id(doc_id, doc_status)
```

**Remove or simplify `_get_content_hashes()` method (no longer needed):**

```python
def _get_content_hashes(self, document_ids: Iterable[str]) -> Dict[str, str]:
    """
    Simplified: just return doc_ids as-is since we now use direct mapping.
    Kept for backward compatibility.
    """
    return {doc_id: doc_id for doc_id in document_ids}
```

---

## Step 5: Handle Return Type Change

**File:** `backend/infrastructure/storage/lightrag_storage.py`

**Find:** `store_document()` method

**Update to handle new return type:**

```python
async def store_document(
    self,
    document_id: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Store document in RAG
    
    Args:
        document_id: Document UUID
        text: Document text
        metadata: Optional metadata
        
    Returns:
        True if successful
    """
    if not self.rag_engine:
        self.logger.warning("RAG engine not available")
        return False
    
    try:
        lightrag_doc_id = await self.rag_engine.insert(text, metadata)
        if lightrag_doc_id:
            self.logger.info(f"Stored document in RAG: {document_id} -> {lightrag_doc_id}")
            return True
        return False
        
    except Exception as e:
        self.logger.error(f"Failed to store document: {e}")
        return False
```

---

## Testing Steps

### For New Documents:
1. Upload a new document
2. Check `document_registry.json` - should have `lightrag_doc_id` field
3. Query with that document selected - should work!

### For Existing Documents:
1. Existing documents will use hash-based fallback (legacy support)
2. To update them: Re-upload or manually add `lightrag_doc_id` to registry
3. OR: Wait for users to re-upload naturally

### Verify Mapping:
1. After uploading, check logs for: `"Created LightRAG doc ID: doc-XXXXX"`
2. Check `document_registry.json` for the document:
   ```json
   {
     "document_id": "...",
     "lightrag_doc_id": "doc-XXXXX",
     ...
   }
   ```
3. Try document-scoped query - should see: `"RAG QUERY FILTERED: 1 docs → 18 chunks"`

---

## Summary of Changes

**4 Files Modified:**
1. ✅ `rag_engine.py` - Return LightRAG doc ID from insert()
2. ✅ `document_registry.py` - Add store_lightrag_doc_id() method
3. ✅ `service.py` - Capture and store doc ID during processing
4. ✅ `document_chunk_mapper.py` - Use stored ID for mapping

**Result:** Direct, reliable mapping with legacy fallback support.
