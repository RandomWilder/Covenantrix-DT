# Critical Fix: LightRAG Queue Race Condition

**Date**: November 15, 2024  
**Priority**: CRITICAL  
**Status**: Fixed  
**Related**: 0053_PARALLEL_UPLOAD_OPTIMIZATION.md

## Summary

Fixed a critical race condition where parallel document uploads caused documents to hang after appearing "processed" due to LightRAG's internal queueing mechanism returning immediately before actual processing completion.

## The Bug

### What Users Saw
- Upload 2 documents
- Document 1: Completes successfully
- Document 2: Shows as "processed" in UI, but actually hangs
- Log shows: `"Another process is already processing the document queue. Request queued."`
- Document 2 gets stuck after "Chunk 36/36 extracted"

### Log Evidence

```
Line 588: Inserting document into RAG (44627 chars)
Line 589: ⚠️ "Another process is already processing the document queue. Request queued."
Line 590: Document inserted successfully with LightRAG doc ID  <-- LIES!
Line 593: Document processed: (44627 chars, 37 chunks)        <-- PREMATURE!
...
Lines 595-1004: Document 1 STILL processing chunks 13-36
Line 928: Batch upload completed: 1/2 successful, 1 failed
```

## Root Cause Analysis

### LightRAG Internal Behavior

LightRAG has an internal document processing queue with mutex locking:

```python
# Inside LightRAG (simplified)
async def ainsert(self, text):
    if self._processing_lock.locked():
        logger.info("Another process is already processing. Request queued.")
        # ADD TO QUEUE
        return  # ← Returns immediately!
    
    async with self._processing_lock:
        # Actually process document
        await self._process_entity_relation_graph(chunks)
```

**The Problem**: When a document is queued, `ainsert()` returns **immediately** without waiting for processing to complete.

### Our Code's Assumption

```python
# backend/domain/documents/service.py line 255
await self.rag_engine.insert(extracted_content)
# ← We assumed this waits for completion
# ← But it returns immediately when queued!

# Service marks document as "processed"
document.mark_processed(...)  # ← STATE MISMATCH!
```

### The Race Condition

**Timeline**:
```
T0: Document 1 calls rag_engine.insert()
    └─> Acquires LightRAG lock
    └─> Starts entity extraction (duration scales with document size - no hard limit)

T1: Document 2 (parallel) calls rag_engine.insert()
    └─> LightRAG lock is held by Doc 1
    └─> ainsert() returns immediately ("Request queued")
    └─> Our service thinks Doc 2 is done
    └─> Marks Doc 2 as "processed" ✗ WRONG!

T180: Document 1 finishes
      └─> LightRAG releases lock
      └─> LightRAG starts processing queued Doc 2
      └─> But Doc 2 is already marked "processed"
      └─> State inconsistency → hangs
```

## The Fix

### Solution: Two-Tier Semaphore System

Added a **RAG-level semaphore** that ensures only ONE document enters LightRAG at a time:

```python
# backend/api/routes/documents.py

# Semaphore for parallel upload + text extraction (2 concurrent)
processing_semaphore = asyncio.Semaphore(2)

# CRITICAL: Semaphore for RAG operations (1 concurrent)
# Prevents LightRAG queueing race condition
rag_insert_semaphore = asyncio.Semaphore(1)

async def process_single_document(...):
    async with processing_semaphore:
        # Upload and extract text (can happen in parallel)
        document = await service.upload_document(...)
        extracted_text = await processor.extract_text(...)
        
        # CRITICAL: Acquire RAG semaphore before processing
        async with rag_insert_semaphore:
            # Only ONE document at a time enters here
            await service.process_document(...)
            # Document won't be marked "processed" until actually done
```

### Why This Works

**Before Fix**:
```
Doc 1: Upload → Extract → RAG Insert (starts) ──────────┐
Doc 2: Upload → Extract → RAG Insert (queued)           │
                          ↓                              │
                     Returns immediately                 │
                     Marked "processed" ✗                │
                                                    (2 minutes)
                                                         │
                                                         ↓
                                                  Doc 1 finishes
                                                  Doc 2 starts (but already "processed")
                                                  → HANG
```

**After Fix**:
```
Doc 1: Upload → Extract ──┐
Doc 2: Upload → Extract ──┼→ Both can happen in parallel
                          │
                          ↓
                    Wait for rag_insert_semaphore
                          │
                          ↓
            Doc 1: RAG Insert (takes 2 min) → Mark "processed" ✓
                          │
                          ↓
            Doc 2: RAG Insert (takes 2 min) → Mark "processed" ✓
                          
Result: Both documents fully processed, proper state management
```

## Performance Impact

### Before Fix
- Documents uploaded in parallel ✓
- Text extraction in parallel ✓
- RAG insertion in parallel ✗ (caused race condition)
- **Result**: 1/2 documents failed

### After Fix
- Documents uploaded in parallel ✓
- Text extraction in parallel ✓
- RAG insertion sequential ✓ (no race condition)
- **Result**: 2/2 documents succeed

### Time Comparison

**Scenario: Upload 2 documents**

| Phase | Before Fix | After Fix |
|-------|------------|-----------|
| Upload | Parallel (~5s) | Parallel (~5s) |
| Text Extract | Parallel (~10s) | Parallel (~10s) |
| RAG Insert | "Parallel" (broken) | Sequential |
| Total | ~2min (1 fails) | ~4min (both succeed) |

**Trade-off**: Slightly slower (sequential RAG), but **reliable** (no hangs).

## Code Changes

### 1. Added RAG Semaphore Declaration
```python
# Line 256-259 in backend/api/routes/documents.py
# CRITICAL: Semaphore for RAG engine operations (max 1)
# LightRAG has internal queueing that returns immediately when a document is queued
# We MUST ensure only ONE document enters RAG at a time to avoid state inconsistencies
rag_insert_semaphore = asyncio.Semaphore(1)
```

### 2. Wrapped RAG Processing
```python
# Line 346-361 in backend/api/routes/documents.py
# CRITICAL: Acquire RAG semaphore before processing
# This ensures only ONE document at a time enters LightRAG
# Prevents "Request queued" race condition where ainsert() returns immediately
async with rag_insert_semaphore:
    # SMART TIMEOUT: Only timeout if no progress for 5 minutes
    # This allows large documents (300+ pages) to process without time limits
    # as long as they're making progress (chunks being extracted)
    try:
        # Create the processing task
        processing_task = asyncio.create_task(
            service.process_document(
                document_id=document_id,
                extracted_content=extracted_text,
                processing_time=time.time() - start_time,
                ocr_applied=ocr_used,
                progress_callback=document_progress_callback
            )
        )
        
        # Monitor task with progress-based timeout
        inactivity_timeout = 300.0  # 5 minutes of no progress = stuck
        check_interval = 10.0  # Check every 10 seconds
        
        while not processing_task.done():
            try:
                await asyncio.wait_for(
                    asyncio.shield(processing_task),
                    timeout=check_interval
                )
            except asyncio.TimeoutError:
                # Check if progress is being made
                time_since_progress = time.time() - last_progress_time['time']
                if time_since_progress > inactivity_timeout:
                    # No progress for 5 minutes - process is stuck
                    processing_task.cancel()
                    raise asyncio.TimeoutError("No progress detected")
        
        # Task completed successfully
        await processing_task
```

## Testing & Verification

### Test Case 1: Upload 2 Documents
**Expected**:
- Both documents upload in parallel
- Both extract text in parallel
- Document 1 processes through RAG first
- Document 2 waits, then processes through RAG
- **Both succeed**

### Test Case 2: Upload 3 Documents with One Timeout
**Expected**:
- All 3 upload and extract in parallel
- Document 1 processes through RAG
- Document 2 processes through RAG
- Document 3 processes through RAG
- If one times out, others continue
- **2/3 succeed**

### Log Verification

**Success Log Pattern**:
```
Document 1: Inserting document into RAG (44627 chars)
Document 1: Document inserted successfully with LightRAG doc ID: doc-xxx
Document 1: Document processed: abc-123 (44627 chars, 37 chunks)
Document 2: Inserting document into RAG (32541 chars)
Document 2: Document inserted successfully with LightRAG doc ID: doc-yyy
Document 2: Document processed: def-456 (32541 chars, 27 chunks)
Batch upload completed: 2/2 successful, 0 failed
```

**NO MORE** `"Another process is already processing. Request queued."` messages!

## Lessons Learned

### 1. External Library Assumptions
- Don't assume async functions wait for completion
- Verify behavior with concurrent calls
- Check for internal queueing/locking mechanisms

### 2. State Management
- Never mark something complete based on API return alone
- Verify actual completion before state updates
- Use proper synchronization primitives

### 3. Parallel Processing Pitfalls
- Not all operations can be parallelized safely
- Some libraries have single-threaded constraints
- Use semaphores to enforce sequential access where needed

## Future Considerations

### Alternative Solutions Considered

1. **Patch LightRAG to wait for completion**
   - ❌ Requires modifying third-party library
   - ❌ Breaks on LightRAG updates

2. **Poll for completion**
   - ❌ Complex implementation
   - ❌ Adds latency

3. **Sequential processing (original)**
   - ❌ Slow for multiple documents
   - ✓ But no race conditions

4. **Two-tier semaphore (chosen)**
   - ✓ Clean implementation
   - ✓ No library modifications
   - ✓ Optimal parallelism
   - ✓ Reliable

### Monitoring

Watch for these log patterns:
- ✓ `"Document inserted successfully"` followed by `"Document processed"`
- ✗ `"Another process is already processing"` (should never appear now)
- ✓ `"Batch upload completed: X/Y successful"` with X=Y

---

**Status**: Fixed and tested  
**Risk**: Low - Fix prevents race condition without breaking existing functionality  
**Rollback**: Revert semaphore addition (but original parallel code has race condition)

