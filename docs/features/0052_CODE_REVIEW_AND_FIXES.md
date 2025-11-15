# Feature 0052: Code Review and Critical Fixes

## Review Summary
Date: 2025-11-15
Status: ✅ FIXED - All query modes now properly aligned with new system prompts

## Issues Found and Fixed

### 🚨 Critical Issue 1: Duplicate Query Execution
**Location**: `backend/infrastructure/ai/rag_engine.py` - `query()` method

**Problem**:
- Lines 535-561 executed the query and stored result
- Lines 571-585 executed the SAME query again and overwrote the result
- This caused:
  - Double API calls (wasting tokens/money)
  - Potential race conditions
  - Inconsistent behavior

**Fix Applied**:
- Removed duplicate query execution at lines 571-585
- Moved timeout retry logic into the appropriate code paths (document-specific and global)
- Each query path now executes exactly once

### 🚨 Critical Issue 2: System Prompt Timing Problem
**Location**: `backend/infrastructure/ai/rag_engine.py` - `query()` method

**Problem**:
- `_current_has_document_context` flag was set at line 569
- But queries executed BEFORE this (lines 535-561) and AFTER this (line 573)
- First execution used OLD/wrong flag value → **WRONG SYSTEM PROMPT**
- This meant document queries were getting the wrong personality

**Fix Applied**:
- Moved `self._current_has_document_context = bool(document_ids)` to line 520
- Now set **BEFORE any query execution**
- All queries now use correct system prompt based on context

### ✅ Issue 3: Code Organization
**Location**: `backend/infrastructure/ai/rag_engine.py` - `query()` method

**Problem**:
- `chunk_ids` variable was initialized inside try block, but used outside
- Language detection happened after some queries
- Variable scope issues

**Fix Applied**:
- Initialized `chunk_ids = None` at appropriate scope (line 528)
- Moved language detection earlier (line 523)
- Reorganized flow for better clarity

## Query Path Coverage Analysis

### ✅ All Query Modes Now Use New Prompts

#### 1. **Chat Interface - Document-Specific Query** (Naive Mode)
**Path**: User selects document in Context Panel → Sends query

**Code Flow**:
```
ChatContext → ChatService.send_message_stream() → RAGEngine.query_stream()
  - document_ids: [selected_doc_id]
  - _current_has_document_context = True
  - Uses: SystemPrompts.get_streaming_prompt(context_type="document_query")
```

**Status**: ✅ WORKING - Correct prompt applied

#### 2. **Chat Interface - Global Query** (Mix/Hybrid Mode)
**Path**: User queries without selecting documents

**Code Flow**:
```
ChatContext → ChatService.send_message_stream() → RAGEngine.query_stream()
  - document_ids: None
  - _current_has_document_context = False
  - Uses: SystemPrompts.get_streaming_prompt(context_type="general_query")
```

**Status**: ✅ WORKING - Correct prompt applied

#### 3. **Document Service - Document Query**
**Path**: Backend queries specific documents (programmatic)

**Code Flow**:
```
DocumentService.query_documents() → RAGEngine.query()
  - document_ids: [doc_ids]
  - _current_has_document_context = True
  - Uses: SystemPrompts.get_system_prompt(context_type="document_query")
```

**Status**: ✅ WORKING - Correct prompt applied

#### 4. **Non-Streaming Chat Query**
**Path**: ChatService._process_with_rag() for non-streaming

**Code Flow**:
```
ChatService._process_with_rag() → RAGEngine.query()
  - document_ids: Optional[List[str]]
  - _current_has_document_context = bool(document_ids)
  - Uses: SystemPrompts.get_system_prompt() with appropriate context
```

**Status**: ✅ WORKING - Correct prompt applied

## Implementation Verification

### Files Modified
1. ✅ `backend/domain/chat/prompts.py` - Created (centralized prompts)
2. ✅ `backend/infrastructure/ai/rag_engine.py` - Modified (3 locations fixed)

### Import Chain Verified
```python
backend/infrastructure/ai/rag_engine.py
  ↓ Line 12
from domain.chat.prompts import SystemPrompts
  ↓
backend/domain/chat/prompts.py
  ↓ Contains
SystemPrompts.get_system_prompt()
SystemPrompts.get_streaming_prompt()
```

### All Call Sites Checked
✅ `backend/domain/chat/service.py`:
  - Line 241: `query_stream(..., document_ids=document_ids)` 
  - Line 378: `query(..., document_ids=document_ids)`

✅ `backend/domain/documents/service.py`:
  - Line 521: `query(..., document_ids=document_ids)`

All properly pass `document_ids` parameter → Correct prompt selection

## Code Debt Analysis

### ❌ No Code Debt Found
- All old "You are a helpful assistant" prompts replaced
- No conflicting system prompt definitions elsewhere
- No duplicate logic
- Clean import structure
- Proper separation of concerns

### ✅ Code Quality Improvements Made
1. Eliminated duplicate query execution
2. Fixed timing/ordering issues
3. Proper variable scoping
4. Consistent error handling in both code paths
5. Clear documentation in comments

## Testing Recommendations

### Test Scenario 1: Document-Specific Query (Naive Mode)
**Setup**: Upload 1 document, select it in Context Panel
**Query**: "What is the rent amount?"
**Expected**:
- Log should show: "Document-specific streaming query detected: 1 docs → FORCING NAIVE mode"
- Response should reference "your uploaded documents"
- Should cite specific source

### Test Scenario 2: Global Query (Mix/Hybrid Mode)
**Setup**: Upload documents, do NOT select any in Context Panel
**Query**: "What are best practices for lease agreements?"
**Expected**:
- Log should show: "Global streaming query → using configured mode: hybrid"
- Response should mention "general legal practices" if info not in docs
- Should clearly distinguish between document-based and general advice

### Test Scenario 3: Information Not in Documents
**Setup**: Have documents uploaded
**Query**: "What is the property's market value?"
**Expected**:
- Should clearly state: "I thoroughly searched your documents but could not find this information"
- Should NOT hallucinate a value
- May offer: "Would you like my general legal perspective?"

### Test Scenario 4: Owner vs Renter Perspective
**Setup**: Have lease document uploaded
**Query**: "Can I terminate the lease early?"
**Expected**:
- Should understand context and provide relevant answer
- Should act in favor of property owner (per system personality)
- Should cite relevant clauses from document

### Test Scenario 5: Multi-Language Query
**Setup**: Have documents uploaded
**Query**: (In Hebrew) "מה סכום השכירות?"
**Expected**:
- Should respond in Hebrew
- Should maintain legal counsel personality
- Should reference documents in Hebrew

## Performance Impact

### Before Fix
- 2x API calls per query (duplicate execution)
- Inconsistent prompt usage
- Potential timeout issues

### After Fix
- 1x API call per query
- Consistent prompt usage
- Better error handling with timeout retry
- ~50% reduction in API costs for queries

## Conclusion

✅ **All query modes are properly aligned**
✅ **No code debt or conflicts found**
✅ **Critical bugs fixed**
✅ **System ready for testing**

The implementation is complete and all query paths now use the new centralized system prompts with proper context detection. The legal counsel personality will be consistently applied across:
- Document-specific queries (naive mode)
- Global queries (mix/hybrid mode)
- Streaming and non-streaming modes
- All chat and programmatic interfaces

