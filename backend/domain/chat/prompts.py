"""
Centralized System Prompts Configuration
Defines AI assistant personality and behavior as legal counsel for property owners
"""


class SystemPrompts:
    """
    Centralized system prompts for the AI assistant.
    The assistant acts as legal counsel for private real estate property owners.
    """
    
    # Core personality base
    BASE_PERSONALITY = """You are a professional legal counsel assistant specializing in real estate property management. 
You serve private property owners in managing their contract portfolios and legal matters.

Your core principles:
- Act in the best interest of property owners
- Maintain professional, trustworthy, and detail-oriented communication
- Understand that users may ask questions from different perspectives (as property owner or as renter)
- Always determine the user's perspective and provide relevant advice accordingly"""

    # Context-specific prompts
    DOCUMENT_QUERY_CONTEXT = """
I will analyze your uploaded documents to provide accurate, document-based answers:
- All my answers are based on the documents you've provided
- I will cite specific sources when relevant
- If information is not in your documents, I will clearly state this
- I will not make assumptions or guess information that isn't explicitly in your documents"""

    NO_DOCUMENT_INFO_CONTEXT = """
I thoroughly searched your documents but could not find the requested information.
The information you're asking about is not available in your uploaded documents.
Would you like my general legal perspective on this matter based on standard legal practices?"""

    GENERAL_QUERY_CONTEXT = """
I will provide general legal advice based on best practices and standard legal approaches.
Please note: This is general guidance, not based on your specific documents.
For document-specific advice, please upload relevant contracts or documents."""

    @classmethod
    def get_system_prompt(
        cls,
        context_type: str = "document_query",
        language_instruction: str = ""
    ) -> str:
        """
        Generate complete system prompt based on context type.
        
        Args:
            context_type: Type of query context
                - "document_query": Query with document context
                - "general_query": Query without document context
                - "no_info_found": Info not found in documents
            language_instruction: Language-specific instruction to append
            
        Returns:
            Complete system prompt string
        """
        # Start with base personality
        prompt_parts = [cls.BASE_PERSONALITY]
        
        # Add context-specific instructions
        if context_type == "document_query":
            prompt_parts.append(cls.DOCUMENT_QUERY_CONTEXT)
        elif context_type == "general_query":
            prompt_parts.append(cls.GENERAL_QUERY_CONTEXT)
        elif context_type == "no_info_found":
            prompt_parts.append(cls.NO_DOCUMENT_INFO_CONTEXT)
        
        # Combine all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        # Add language instruction if provided
        if language_instruction:
            # Only add if not already present
            if "Respond in the same language" not in full_prompt:
                full_prompt += f"\n\n{language_instruction}"
        
        return full_prompt
    
    @classmethod
    def get_streaming_prompt(
        cls,
        context_type: str = "document_query",
        language_instruction: str = ""
    ) -> str:
        """
        Generate system prompt for streaming responses.
        Currently identical to get_system_prompt, but separated for future customization.
        
        Args:
            context_type: Type of query context
            language_instruction: Language-specific instruction to append
            
        Returns:
            Complete system prompt string for streaming
        """
        # For now, streaming uses the same prompts as non-streaming
        return cls.get_system_prompt(context_type, language_instruction)

