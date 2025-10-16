"""
Chat Routes
Chat and conversation management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
import logging
import json

from domain.chat.service import ChatService
from domain.chat.exceptions import MessageProcessingError
from core.dependencies import get_chat_service, get_subscription_service
from api.schemas.chat import (
    ChatMessageRequest, ChatMessageResponse,
    ConversationResponse, ConversationListResponse,
    MessageListResponse, CreateConversationRequest,
    ConversationCreatedResponse, ConversationDeletedResponse
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    service: ChatService = Depends(get_chat_service),
    subscription_service = Depends(get_subscription_service)
) -> ChatMessageResponse:
    """
    Send a message and get response
    
    Args:
        request: Message request
        service: Chat service
        
    Returns:
        Chat response with assistant message and sources
    """
    # Check subscription query limits
    try:
        allowed, reason = await subscription_service.check_query_allowed()
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Query limit exceeded: {reason}"
            )
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        # Continue if subscription service is unavailable
    
    # Pre-operation global state check (DO NOT re-resolve keys)
    from core.dependencies import get_rag_engine
    if get_rag_engine() is None:
        logger.warning("Chat message blocked - no valid OpenAI API key configured")
        raise HTTPException(
            status_code=400,
            detail="No valid OpenAI API key configured. Please configure your API key in Settings to start chatting."
        )
    
    try:
        response = await service.send_message(
            message=request.message,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id,
            document_ids=request.document_ids
        )
        
        # Convert domain Source objects to dictionaries for Pydantic serialization
        sources_dict = []
        for source in response.sources:
            sources_dict.append({
                "document_id": source.document_id,
                "document_name": source.document_name,
                "page_number": source.page_number,
                "confidence": source.confidence,
                "excerpt": source.excerpt
            })
        
        # NEW: Record query usage
        await subscription_service.record_query()
        
        return ChatMessageResponse(
            success=True,
            conversation_id=response.conversation_id,
            message_id=response.message_id,
            response=response.response,
            sources=sources_dict,
            agent_used=response.agent_used,
            message="Message processed successfully"
        )
        
    except MessageProcessingError as e:
        logger.error(f"Message processing failed: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Send message failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Send a message and stream response
    
    Args:
        request: Message request
        service: Chat service
        
    Returns:
        Server-Sent Events stream with token-by-token response
    """
    # Pre-operation global state check (DO NOT re-resolve keys)
    from core.dependencies import get_rag_engine
    if get_rag_engine() is None:
        logger.warning("Chat streaming blocked - no valid OpenAI API key configured")
        raise HTTPException(
            status_code=400,
            detail="No valid OpenAI API key configured. Please configure your API key in Settings to start chatting."
        )
    
    # NEW: Check query limits
    from core.dependencies import get_subscription_service
    subscription_service = get_subscription_service()
    
    can_query, reason = await subscription_service.check_query_allowed()
    if not can_query:
        remaining = await subscription_service.get_remaining_queries()
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail={
                "error": "query_limit_reached",
                "message": reason,
                "remaining_monthly": remaining["monthly_remaining"],
                "remaining_daily": remaining["daily_remaining"],
                "reset_dates": remaining["reset_dates"]
            }
        )
    
    async def generate_stream():
        """Generate SSE stream"""
        try:
            async for chunk in service.send_message_stream(
                message=request.message,
                conversation_id=request.conversation_id,
                agent_id=request.agent_id,
                document_ids=request.document_ids
            ):
                # Format as Server-Sent Event
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"
            
            # NEW: Record query usage after streaming completes
            await subscription_service.record_query()
                
        except MessageProcessingError as e:
            logger.error(f"Streaming message processing failed: {e}")
            error_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            error_data = json.dumps({"error": "Internal server error", "done": True})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    service: ChatService = Depends(get_chat_service)
) -> ConversationListResponse:
    """
    List all conversations
    
    Args:
        service: Chat service
        
    Returns:
        List of conversation summaries
    """
    try:
        conversations = await service.list_conversations()
        
        # Convert conversations to dictionaries with ISO string dates
        conversations_dict = []
        for conv in conversations:
            conv_dict = {
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': conv.message_count,
                'last_message_preview': conv.last_message_preview
            }
            conversations_dict.append(conv_dict)
        
        return ConversationListResponse(
            success=True,
            conversations=conversations_dict,
            total_count=len(conversations),
            message="Conversations retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"List conversations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations", response_model=ConversationCreatedResponse)
async def create_conversation(
    request: CreateConversationRequest,
    service: ChatService = Depends(get_chat_service)
) -> ConversationCreatedResponse:
    """
    Create a new conversation
    
    Args:
        request: Conversation creation request
        service: Chat service
        
    Returns:
        Created conversation
    """
    try:
        conversation = await service.create_conversation(request.title)
        
        # Convert to summary for response
        from domain.chat.models import ConversationSummary
        summary = ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages)
        )
        
        # Convert to dictionary with ISO string dates
        summary_dict = {
            'id': summary.id,
            'title': summary.title,
            'created_at': summary.created_at.isoformat(),
            'updated_at': summary.updated_at.isoformat(),
            'message_count': summary.message_count,
            'last_message_preview': summary.last_message_preview
        }
        
        return ConversationCreatedResponse(
            success=True,
            conversation=summary_dict,
            message="Conversation created successfully"
        )
        
    except Exception as e:
        logger.error(f"Create conversation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", response_model=ConversationDeletedResponse)
async def delete_conversation(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service)
) -> ConversationDeletedResponse:
    """
    Delete a conversation
    
    Args:
        conversation_id: Conversation ID
        service: Chat service
        
    Returns:
        Deletion confirmation
    """
    try:
        await service.delete_conversation(conversation_id)
        
        return ConversationDeletedResponse(
            success=True,
            conversation_id=conversation_id,
            deleted=True,
            message="Conversation deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Delete conversation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    service: ChatService = Depends(get_chat_service)
) -> MessageListResponse:
    """
    Get conversation message history
    
    Args:
        conversation_id: Conversation ID
        service: Chat service
        
    Returns:
        List of messages in chronological order
    """
    try:
        messages = await service.get_conversation_history(conversation_id)
        
        # Convert domain Message objects to dictionaries for Pydantic serialization
        messages_dict = []
        for message in messages:
            # Convert sources
            sources_dict = []
            for source in message.sources:
                sources_dict.append({
                    "document_id": source.document_id,
                    "document_name": source.document_name,
                    "page_number": source.page_number,
                    "confidence": source.confidence,
                    "excerpt": source.excerpt
                })
            
            messages_dict.append({
                "id": message.id,
                "role": message.role.value,
                "content": message.content,
                "sources": sources_dict,
                "timestamp": message.timestamp.isoformat()
            })
        
        return MessageListResponse(
            success=True,
            messages=messages_dict,
            total_count=len(messages),
            message="Messages retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get conversation messages failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
