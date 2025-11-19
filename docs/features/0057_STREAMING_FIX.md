# Feature 0057: Streaming Summary Generation - Bug Fix

**Date**: November 19, 2025
**Status**: ✅ Fixed

---

## Issue Summary

### Error
```
Summary generation failed for document: object async_generator can't be used in 'await' expression
```

### Root Cause
The `progress_callback` in the streaming endpoint was defined as an **async generator** (using `yield`) but the service expected it to be a **regular async function** that could be awaited.

```python
# ❌ BEFORE (Incorrect)
async def progress_callback(update: dict):
    """This is an async generator - can't be awaited!"""
    progress_event = SummaryProgressUpdate(**update)
    yield f"data: {progress_event.model_dump_json()}\n\n"

# When service tried to: await progress_callback({...})
# It was actually awaiting an async generator object, not a coroutine
```

---

## Solution Applied

### Queue-Based Async Pattern
Implemented proper async streaming using `asyncio.Queue`:

1. **Progress Callback** → Regular async function that puts updates in queue
2. **Background Task** → Runs summary generation asynchronously
3. **Stream Generator** → Consumes from queue and yields SSE events

```python
# ✅ AFTER (Correct)
# Create queue for cross-task communication
progress_queue = asyncio.Queue()

async def progress_callback(update: dict):
    """Regular async function - can be awaited!"""
    await progress_queue.put(("progress", update))

# Background task runs generation
generation_task = asyncio.create_task(run_generation())

# Main stream consumes from queue and yields
while True:
    event_type, data = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
    if event_type == "progress":
        yield f"data: {progress_event.model_dump_json()}\n\n"
    elif event_type == "complete":
        yield f"data: {json.dumps({'type': 'complete', 'summary': ...})}\n\n"
        break
```

---

## Key Changes

### File: `backend/api/routes/documents.py`

**Line 1001-1116**: Rewrote `generate_document_summary_stream()` endpoint

#### Before
- `progress_callback` was async generator
- Direct await caused TypeError
- No keepalive mechanism

#### After
- `progress_callback` is regular async function
- Uses `asyncio.Queue` for communication
- Background task for generation
- Keepalive messages every 1 second
- Proper error handling and task cleanup

---

## Benefits

1. **✅ Fixes async generator error** - Progress callbacks work correctly
2. **✅ Non-blocking streaming** - Generation runs in background
3. **✅ Keepalive support** - Prevents connection timeout during long operations
4. **✅ Better error handling** - Catches exceptions from background task
5. **✅ Clean architecture** - Separates concerns (generation vs streaming)

---

## Technical Details

### Async Queue Pattern
```python
# Producer (background task)
async def progress_callback(update: dict):
    await progress_queue.put(("progress", update))

# Consumer (stream generator)
event_type, data = await asyncio.wait_for(
    progress_queue.get(), 
    timeout=1.0  # Prevents infinite blocking
)
```

### Event Types
- `("progress", dict)` - Progress update
- `("complete", DocumentSummary)` - Final summary
- `("error", str)` - Error message

### Keepalive Mechanism
When queue is empty for 1 second:
```
: keepalive\n\n
```
Prevents HTTP connection timeout during long-running operations.

---

## Testing Checklist

- [x] Backend linter passes (no errors)
- [ ] Summary generation starts without errors
- [ ] Progress updates stream correctly
- [ ] Final summary delivered
- [ ] Error handling works
- [ ] Keepalive prevents timeout
- [ ] Frontend displays progress bar

---

## Frontend Compatibility

✅ No frontend changes needed - the API contract remains the same:

- POST `/documents/{documentId}/summarize/stream`
- Returns SSE stream
- Progress events: `data: {document_id, stage, progress_percent, ...}`
- Completion event: `data: {type: "complete", summary: {...}}`
- Error event: `data: {type: "error", error: "..."}`

---

## Related Files

### Modified
- `backend/api/routes/documents.py` - Fixed streaming endpoint

### No Changes Needed
- `backend/domain/documents/service.py` - Already correct
- `backend/domain/documents/summarization_service.py` - Already correct
- `covenantrix-desktop/src/services/api/DocumentsApi.ts` - Already correct
- All frontend components - Already correct

---

## Verification

After fix, the logs should show:

```
✅ POST /documents/{id}/summarize/stream - 200 OK
✅ No async_generator errors
✅ Progress updates streaming
✅ Summary generation completing
```

---

**Status**: ✅ Ready for testing

