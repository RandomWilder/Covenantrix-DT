# AI Assistant Feature - Implementation Plan

## Overview
Add AI Assistant chat interface to Covenantrix with three-panel resizable layout, leveraging existing RAG engine and agent framework.

## UI Architecture

### Three-Panel Layout
```
[History 10-30%] | [Chat 40-80%] | [Context 10-30%]
     ↓                  ↓                ↓
 Collapsible       Always Visible    Collapsible
```

**Panel Behavior:**
- **Left (History)**: 10-30% width, collapsible, conversation list
- **Center (Chat)**: 40-80% width, always visible, expands over collapsed panels
- **Right (Context)**: 10-30% width, collapsible, document sources & citations
- **Resizers**: Draggable split bars between panels

### Top Bar Controls
- Model/agent selector dropdown
- New chat button
- Settings gear (existing)
- Clear chat button

### Center Panel Components
- Message list (scrollable, auto-scroll to bottom)
- Typing indicator during response
- Message input with:
  - Text area (multi-line support)
  - Send button
  - Attach document button (link to existing docs)

---

## Backend Implementation

### 1. New API Endpoint
**File:** `backend/api/routes/chat.py` (NEW)

**Endpoints:**
```python
POST   /chat/message          # Send message, get response
GET    /chat/conversations    # List conversation history
POST   /chat/conversations    # Create new conversation
DELETE /chat/conversations/{id} # Delete conversation
GET    /chat/conversations/{id}/messages # Get conversation messages
```

**Request/Response:**
```python
# Send message
Request: { 
  conversation_id?: string,
  message: string,
  agent_id?: string,
  document_ids?: string[]
}
Response: {
  conversation_id: string,
  message_id: string,
  response: string,
  sources: Source[]
}
```

### 2. Conversation Storage
**File:** `backend/infrastructure/storage/chat_storage.py` (NEW)

**Schema:**
```python
Conversation:
  - id: str
  - title: str (auto-generated from first message)
  - created_at: datetime
  - updated_at: datetime
  - messages: List[Message]

Message:
  - id: str
  - role: "user" | "assistant"
  - content: str
  - sources: List[Source]
  - timestamp: datetime
```

**Storage:** JSON files in `{WORKING_DIR}/conversations/`

### 3. Chat Service Integration
**File:** `backend/domain/chat/service.py` (NEW)

**Responsibilities:**
- Route messages to RAG engine or agent orchestrator
- Maintain conversation context
- Handle document context injection
- Format responses with citations

**Key Methods:**
```python
async def send_message(
    message: str,
    conversation_id: Optional[str],
    agent_id: Optional[str],
    document_ids: Optional[List[str]]
) -> ChatResponse

async def get_conversation_history(
    conversation_id: str
) -> List[Message]
```

---

## Frontend Implementation

### 1. New Screen Component
**File:** `covenantrix-desktop/src/features/chat/ChatScreen.tsx` (NEW)

**Structure:**
```tsx
<div className="chat-screen">
  <ChatTopBar />
  <div className="panels-container">
    <HistoryPanel width={leftWidth} collapsed={leftCollapsed} />
    <Resizer onResize={handleLeftResize} />
    <ChatPanel width={centerWidth} />
    <Resizer onResize={handleRightResize} />
    <ContextPanel width={rightWidth} collapsed={rightCollapsed} />
  </div>
</div>
```

### 2. Panel State Management
**File:** `covenantrix-desktop/src/hooks/usePanelLayout.ts` (NEW)

**State:**
```typescript
{
  leftWidth: number,      // 10-30%
  rightWidth: number,     // 10-30%
  leftCollapsed: boolean,
  rightCollapsed: boolean,
  centerWidth: number     // Calculated: 100 - leftWidth - rightWidth
}
```

**Constraints:**
- Center always 40-80% when both panels visible
- Center expands over collapsed panels
- Persist layout to localStorage

### 3. Chat Context
**File:** `covenantrix-desktop/src/contexts/ChatContext.tsx` (NEW)

**Responsibilities:**
- Manage active conversation
- Handle message sending/receiving
- Store conversation list
- Manage selected agent
- Track typing indicator state

### 4. Components to Create
**History Panel** (`features/chat/HistoryPanel.tsx`):
- Conversation list with timestamps
- Search/filter conversations
- New chat button
- Delete conversation

**Chat Panel** (`features/chat/ChatPanel.tsx`):
- Reuse existing MessageList component
- Integrate ChatInput component
- Add typing indicator
- Auto-scroll on new messages

**Context Panel** (`features/chat/ContextPanel.tsx`):
- List active documents in context
- Show citation sources from responses
- Document preview on click
- Clear context button

**Panel Resizer** (`components/ui/Resizer.tsx`):
- Draggable split bar
- Visual feedback on hover/drag
- Snap to min/max widths
- Double-click to reset

---

## Integration Points

### Existing Components to Reuse
✅ `features/chat/ChatInput.tsx` - Already exists
✅ `features/chat/ChatInterface.tsx` - Refactor for new layout
✅ `features/chat/Message.tsx` - Already exists
✅ `features/chat/MessageList.tsx` - Already exists
✅ `features/chat/SourceCitation.tsx` - Already exists

### Backend Integration
1. **RAG Engine**: Use existing `/queries` endpoint for document Q&A
2. **Agent Orchestrator**: Use existing `/agents/tasks` endpoint for agent queries
3. **Document Service**: Use existing endpoints to list/access documents

### Router Integration
**File:** `covenantrix-desktop/src/App.tsx`

Add route:
```tsx
{ screen: 'chat', component: <ChatScreen /> }
```

Update Sidebar navigation item (already exists with MessageSquare icon)

---

## Implementation Phases

### Phase 1: Backend Foundation
1. Create `chat_storage.py` - conversation persistence
2. Create `chat/service.py` - chat logic and routing
3. Create `routes/chat.py` - API endpoints
4. Add schemas in `api/schemas/chat.py`
5. Wire to `main.py` router

### Phase 2: Frontend Layout
1. Create `usePanelLayout.ts` hook
2. Create `Resizer.tsx` component
3. Create `ChatScreen.tsx` shell
4. Implement panel collapse/expand
5. Test responsive behavior

### Phase 3: Chat Functionality
1. Create `ChatContext.tsx`
2. Build `HistoryPanel.tsx`
3. Build `ChatPanel.tsx` (integrate existing components)
4. Build `ContextPanel.tsx`
5. Wire API calls

### Phase 4: Polish & Testing
1. Add typing indicators
2. Implement auto-title generation
3. Add conversation search
4. Error handling
5. Loading states
6. Integration testing

---

## Safety Guardrails

### ⚠️ DO NOT BREAK
- Existing document upload/processing flow
- Current RAG query endpoint
- Agent orchestrator task system
- Document context management
- Settings and configuration

### ✅ SAFE TO MODIFY
- Add new routes (don't modify existing)
- Add new storage modules (separate from document storage)
- Create new frontend components
- Add new context providers

### 🔍 CAREFUL INTEGRATION
- **RAG Engine**: Only read, don't modify core functionality
- **Agent Orchestrator**: Use existing task submission, don't change orchestrator
- **Document Service**: Use existing methods, don't alter schemas
- **Navigation**: Add route, maintain existing screens

---

## Data Flow Example

```
User sends message
    ↓
ChatContext.sendMessage()
    ↓
API: POST /chat/message
    ↓
ChatService.send_message()
    ↓
[If agent selected] → AgentOrchestrator.submit_task()
[If no agent] → RAGEngine.query()
    ↓
Format response with sources
    ↓
Save to ChatStorage
    ↓
Return response
    ↓
Update ChatContext
    ↓
Render in MessageList
```

---

## Technical Considerations

### Conversation Context
- Include last 10 messages in RAG query for context
- Reset context on "New Chat"
- Maintain document context across conversation

### Performance
- Lazy load conversation history (paginate old conversations)
- Debounce panel resize events
- Virtual scrolling for long message lists (optional)

### State Persistence
- Save panel layout to localStorage
- Auto-save draft messages
- Persist active conversation ID

### Error Handling
- Network failure recovery
- API timeout handling
- Invalid agent selection fallback
- Missing document context warning

---

## Success Criteria

✅ User can start new conversation
✅ User can send messages and receive responses
✅ Responses include document citations
✅ User can select different agents
✅ Conversation history persists and loads
✅ Panels resize and collapse correctly
✅ Context panel shows active documents
✅ Typing indicator shows during response
✅ No disruption to existing features
✅ Clean error messages on failure

---

## Dependencies

### New Backend Dependencies
None - use existing packages

### New Frontend Dependencies
- `react-resizable-panels` (optional, for advanced panel management)
- OR implement custom resize with native React hooks

Recommend: Custom implementation to avoid dependency bloat

---

## Estimated Complexity

**Backend**: Medium (2-3 days)
- New storage module
- New service layer
- New API routes
- Integration wiring

**Frontend**: Medium-High (3-4 days)
- Panel layout system
- Context management
- Component integration
- Polish and UX

**Total**: ~1 week of development
