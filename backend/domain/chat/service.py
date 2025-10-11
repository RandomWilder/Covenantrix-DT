"""
Chat Service
Business logic for chat and conversation management
"""
import logging
from typing import List, Optional, TYPE_CHECKING, AsyncGenerator
from datetime import datetime

from domain.chat.models import (
    Conversation, Message, ChatResponse, ConversationSummary, Source, MessageRole
)
from domain.chat.exceptions import (
    ConversationNotFoundError,
    MessageProcessingError,
    InvalidMessageError
)

# Avoid circular imports
if TYPE_CHECKING:
    from infrastructure.ai.rag_engine import RAGEngine
    from domain.agents.orchestrator import AgentOrchestrator
    from domain.documents.service import DocumentService
    from infrastructure.storage.chat_storage import ChatStorage

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat domain service
    Orchestrates message routing between RAG engine and agent system
    """
    
    def __init__(
        self,
        chat_storage: 'ChatStorage',
        rag_engine: Optional['RAGEngine'] = None,
        agent_orchestrator: Optional['AgentOrchestrator'] = None,
        document_service: Optional['DocumentService'] = None
    ):
        """
        Initialize chat service
        
        Args:
            rag_engine: RAG engine for document queries (optional)
            agent_orchestrator: Agent orchestrator for agent tasks (optional)
            document_service: Document service for document access (optional)
            chat_storage: Chat storage for conversation persistence
        """
        self.rag_engine = rag_engine
        self.agent_orchestrator = agent_orchestrator
        self.document_service = document_service
        self.chat_storage = chat_storage
    
    async def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> ChatResponse:
        """
        Send a message and get response
        
        Args:
            message: User message content
            conversation_id: Existing conversation ID (None for new conversation)
            agent_id: Selected agent ID (None for RAG query)
            document_ids: Document IDs to include in context
            
        Returns:
            Chat response with assistant message and sources
            
        Raises:
            InvalidMessageError: Invalid message content
            MessageProcessingError: Message processing failed
        """
        logger.info(f"Processing message: '{message[:50]}...' (agent: {agent_id})")
        
        # Validate message
        if not message or not message.strip():
            raise InvalidMessageError("Message cannot be empty")
        
        if len(message.strip()) < 2:
            raise InvalidMessageError("Message too short")
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self.chat_storage.load_conversation(conversation_id)
                if not conversation:
                    raise ConversationNotFoundError(conversation_id)
            else:
                # Create new conversation with auto-generated title
                title = self._generate_conversation_title(message)
                conversation = Conversation.create_new(title)
            
            # Add user message to conversation
            user_message = Message.create_user_message(message)
            conversation.add_message(user_message)
            
            # Process message based on agent selection
            if agent_id:
                # Route to agent orchestrator
                if not self.agent_orchestrator:
                    raise MessageProcessingError("Agent orchestrator not available. Please configure the system properly.")
                response_content, sources = await self._process_with_agent(
                    message=message,
                    agent_id=agent_id,
                    conversation=conversation,
                    document_ids=document_ids
                )
            else:
                # Route to RAG engine
                if not self.rag_engine:
                    raise MessageProcessingError("RAG engine not available. Please ensure the system is properly initialized and OpenAI API key is configured.")
                response_content, sources = await self._process_with_rag(
                    message=message,
                    conversation=conversation,
                    document_ids=document_ids
                )
            
            # Create assistant message
            assistant_message = Message.create_assistant_message(
                content=response_content,
                sources=sources
            )
            conversation.add_message(assistant_message)
            
            # Save conversation
            await self.chat_storage.save_conversation(conversation)
            
            # Create response
            response = ChatResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                response=response_content,
                sources=sources,
                agent_used=agent_id
            )
            
            logger.info(f"Message processed successfully: {conversation.id}")
            return response
            
        except (ConversationNotFoundError, InvalidMessageError):
            raise
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            raise MessageProcessingError(f"Failed to process message: {str(e)}")
    
    async def send_message_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Send a message and stream response
        
        Args:
            message: User message content
            conversation_id: Existing conversation ID (None for new conversation)
            agent_id: Selected agent ID (None for RAG query)
            document_ids: Document IDs to include in context
            
        Yields:
            Token dictionaries with streaming response
            
        Raises:
            InvalidMessageError: Invalid message content
            MessageProcessingError: Message processing failed
        """
        logger.info(f"Processing streaming message: '{message[:50]}...' (agent: {agent_id})")
        
        # Validate message
        if not message or not message.strip():
            raise InvalidMessageError("Message cannot be empty")
        
        if len(message.strip()) < 2:
            raise InvalidMessageError("Message too short")
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self.chat_storage.load_conversation(conversation_id)
                if not conversation:
                    raise ConversationNotFoundError(conversation_id)
            else:
                # Create new conversation with auto-generated title
                title = self._generate_conversation_title(message)
                conversation = Conversation.create_new(title)
            
            # Add user message to conversation
            user_message = Message.create_user_message(message)
            conversation.add_message(user_message)
            
            # Save conversation with user message immediately
            await self.chat_storage.save_conversation(conversation)
            
            # Create assistant message placeholder
            assistant_message = Message.create_assistant_message(
                content="",  # Will be filled as stream progresses
                sources=[]
            )
            
            # Accumulate streamed content
            accumulated_content = ""
            
            # Process message based on agent selection
            if agent_id:
                # Route to agent orchestrator
                if not self.agent_orchestrator:
                    raise MessageProcessingError("Agent orchestrator not available. Please configure the system properly.")
                
                # Note: Agent streaming not implemented yet, fall back to non-streaming
                response_content, sources = await self._process_with_agent(
                    message=message,
                    agent_id=agent_id,
                    conversation=conversation,
                    document_ids=document_ids
                )
                
                # Yield as single token (simulated streaming)
                yield {"token": response_content, "done": False}
                accumulated_content = response_content
                
            else:
                # Route to RAG engine with streaming
                if not self.rag_engine:
                    raise MessageProcessingError("RAG engine not available. Please ensure the system is properly initialized and OpenAI API key is configured.")
                
                # Build context from conversation history
                context_messages = conversation.get_last_messages(10)
                context_text = self._build_conversation_context(context_messages)
                
                # Combine with current message
                full_query = f"{context_text}\n\nUser: {message}"
                
                # Stream tokens from RAG engine
                async for token in self.rag_engine.query_stream(
                    query=full_query,
                    mode="hybrid"
                ):
                    accumulated_content += token
                    yield {"token": token, "done": False}
                
                # Extract sources (RAG doesn't provide during streaming)
                sources = self._extract_rag_sources({}, document_ids)
            
            # Update assistant message with complete content
            assistant_message.content = accumulated_content
            assistant_message.sources = sources
            conversation.add_message(assistant_message)
            
            # Save conversation with complete assistant message
            await self.chat_storage.save_conversation(conversation)
            
            # Send final message with metadata
            sources_dict = []
            for source in sources:
                sources_dict.append({
                    "document_id": source.document_id,
                    "document_name": source.document_name,
                    "page_number": source.page_number,
                    "confidence": source.confidence,
                    "excerpt": source.excerpt
                })
            
            yield {
                "token": None,
                "done": True,
                "message_id": assistant_message.id,
                "conversation_id": conversation.id,
                "sources": sources_dict
            }
            
            logger.info(f"Streaming message processed successfully: {conversation.id}")
            
        except (ConversationNotFoundError, InvalidMessageError):
            raise
        except Exception as e:
            logger.error(f"Streaming message processing failed: {e}")
            raise MessageProcessingError(f"Failed to process streaming message: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str) -> List[Message]:
        """
        Get conversation message history
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages in chronological order
            
        Raises:
            ConversationNotFoundError: Conversation not found
        """
        conversation = await self.chat_storage.load_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)
        
        return conversation.messages
    
    async def create_conversation(self, title: str) -> Conversation:
        """
        Create a new conversation
        
        Args:
            title: Conversation title
            
        Returns:
            Created conversation
        """
        conversation = Conversation.create_new(title)
        await self.chat_storage.save_conversation(conversation)
        
        logger.info(f"Created conversation: {conversation.id}")
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            ConversationNotFoundError: Conversation not found
        """
        success = await self.chat_storage.delete_conversation(conversation_id)
        if not success:
            raise ConversationNotFoundError(conversation_id)
        
        logger.info(f"Deleted conversation: {conversation_id}")
        return True
    
    async def list_conversations(self) -> List[ConversationSummary]:
        """
        List all conversations
        
        Returns:
            List of conversation summaries
        """
        return await self.chat_storage.list_conversations()
    
    async def _process_with_rag(
        self,
        message: str,
        conversation: Conversation,
        document_ids: Optional[List[str]] = None
    ) -> tuple[str, List[Source]]:
        """
        Process message using RAG engine
        
        Args:
            message: User message
            conversation: Current conversation
            document_ids: Optional document scope
            
        Returns:
            Tuple of (response_content, sources)
        """
        try:
            # Build context from conversation history
            context_messages = conversation.get_last_messages(10)
            context_text = self._build_conversation_context(context_messages)
            
            # Combine with current message
            full_query = f"{context_text}\n\nUser: {message}"
            
            # Execute RAG query
            result = await self.rag_engine.query(
                query=full_query,
                mode="hybrid"  # Use hybrid mode for best results
            )
            
            response_content = result.get("response", "I couldn't process your request.")
            
            # Extract sources from RAG result
            sources = self._extract_rag_sources(result, document_ids)
            
            logger.debug(f"RAG query completed: {len(response_content)} chars, {len(sources)} sources")
            return response_content, sources
            
        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
            return "I'm sorry, I couldn't process your request at the moment.", []
    
    async def _process_with_agent(
        self,
        message: str,
        agent_id: str,
        conversation: Conversation,
        document_ids: Optional[List[str]] = None
    ) -> tuple[str, List[Source]]:
        """
        Process message using agent orchestrator
        
        Args:
            message: User message
            agent_id: Selected agent ID
            conversation: Current conversation
            document_ids: Optional document scope
            
        Returns:
            Tuple of (response_content, sources)
        """
        try:
            # Build context from conversation history
            context_messages = conversation.get_last_messages(10)
            context_text = self._build_conversation_context(context_messages)
            
            # Determine task type based on agent and message content
            task_type = self._determine_task_type(agent_id, message)
            
            # Prepare task parameters
            task_parameters = {
                "message": message,
                "context": context_text,
                "document_ids": document_ids or []
            }
            
            # Create task request
            from domain.agents.models import TaskRequest
            task_request = TaskRequest(
                agent_id=agent_id,
                task_type=task_type,
                parameters=task_parameters
            )
            
            # Submit task to agent orchestrator
            task = await self.agent_orchestrator.submit_task(task_request)
            
            # Wait for task completion (with timeout)
            import asyncio
            max_wait_time = 30  # 30 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while task.status.value in ["pending", "running"]:
                if asyncio.get_event_loop().time() - start_time > max_wait_time:
                    raise Exception("Agent task timeout")
                
                await asyncio.sleep(0.5)
                task = await self.agent_orchestrator.get_task_status(task.id)
            
            if task.status.value == "failed":
                raise Exception(f"Agent task failed: {task.error}")
            
            # Get task result
            task_result = await self.agent_orchestrator.get_task_result(task.id)
            
            # Extract response content and sources
            response_content = self._format_agent_response(task_result, agent_id)
            sources = self._extract_agent_sources(task_result, document_ids)
            
            logger.debug(f"Agent processing completed: {len(response_content)} chars")
            return response_content, sources
            
        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return "I'm sorry, I couldn't process your request with the selected agent.", []
    
    def _build_conversation_context(self, messages: List[Message]) -> str:
        """Build conversation context from message history"""
        if not messages:
            return ""
        
        context_parts = []
        for msg in messages[-10:]:  # Last 10 messages
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _extract_rag_sources(self, rag_result: dict, document_ids: Optional[List[str]]) -> List[Source]:
        """Extract sources from RAG result"""
        sources = []
        
        # RAG engine doesn't provide detailed source information
        # We'll create generic sources based on available documents
        if document_ids:
            for doc_id in document_ids:
                sources.append(Source(
                    document_id=doc_id,
                    document_name=f"Document {doc_id[:8]}",
                    confidence=0.8
                ))
        
        return sources
    
    def _extract_agent_sources(self, agent_result: dict, document_ids: Optional[List[str]]) -> List[Source]:
        """Extract sources from agent result"""
        sources = []
        
        # Agent results may include source information
        if "sources" in agent_result:
            for src_data in agent_result["sources"]:
                sources.append(Source(
                    document_id=src_data.get("document_id", ""),
                    document_name=src_data.get("document_name", "Unknown"),
                    page_number=src_data.get("page_number"),
                    confidence=src_data.get("confidence"),
                    excerpt=src_data.get("excerpt")
                ))
        elif document_ids:
            # Fallback to document IDs
            for doc_id in document_ids:
                sources.append(Source(
                    document_id=doc_id,
                    document_name=f"Document {doc_id[:8]}",
                    confidence=0.8
                ))
        
        return sources
    
    def _determine_task_type(self, agent_id: str, message: str) -> str:
        """
        Determine task type based on agent and message content
        
        Args:
            agent_id: Agent identifier
            message: User message
            
        Returns:
            Task type string
        """
        # For market research agent, determine if it's a rent analysis request
        if "market_research" in agent_id.lower():
            message_lower = message.lower()
            if any(keyword in message_lower for keyword in ["rent", "rental", "lease", "price", "cost", "analysis"]):
                return "rent_analysis"
        
        # Default task type
        return "general_query"
    
    def _format_agent_response(self, task_result: dict, agent_id: str) -> str:
        """
        Format agent response for display
        
        Args:
            task_result: Agent task result
            agent_id: Agent identifier
            
        Returns:
            Formatted response string
        """
        # For market research agent, format the analysis result
        if "market_research" in agent_id.lower() and "rent_analysis" in task_result.get("task_type", ""):
            return self._format_market_analysis_response(task_result)
        
        # Default formatting
        if "reasoning" in task_result:
            return task_result["reasoning"]
        elif "response" in task_result:
            return task_result["response"]
        else:
            return str(task_result)
    
    def _format_market_analysis_response(self, task_result: dict) -> str:
        """
        Format market analysis response
        
        Args:
            task_result: Market analysis result
            
        Returns:
            Formatted analysis response
        """
        lines = []
        
        # Add header
        lines.append("🏠 **Market Analysis Report**")
        lines.append("")
        
        # Current rent
        current_rent = task_result.get("current_rent")
        if current_rent:
            lines.append(f"**Current Rent:** ${current_rent:,.2f}/month")
        else:
            lines.append("**Current Rent:** Not available in documents")
        
        # Recommendation
        recommended_rent = task_result.get("recommended_rent")
        market_average = task_result.get("market_average")
        
        if recommended_rent:
            lines.append(f"**Recommended Rent:** ${recommended_rent:,.2f}/month")
        if market_average:
            lines.append(f"**Market Average:** ${market_average:,.2f}/month")
        
        # Confidence
        confidence = task_result.get("confidence", 0)
        confidence_pct = confidence * 100
        lines.append(f"**Confidence:** {confidence_pct:.0f}%")
        lines.append("")
        
        # Reasoning
        reasoning = task_result.get("reasoning", "")
        if reasoning:
            lines.append("**Analysis Details:**")
            lines.append(reasoning)
        
        # Market factors
        market_factors = task_result.get("market_factors", {})
        if market_factors:
            lines.append("")
            lines.append("**Market Factors:**")
            for key, value in market_factors.items():
                if value is not None and key != "note":
                    lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(lines)
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """Generate conversation title from first message"""
        # Simple title generation - take first 50 chars
        title = first_message.strip()[:50]
        if len(first_message.strip()) > 50:
            title += "..."
        
        return title or "New Conversation"
