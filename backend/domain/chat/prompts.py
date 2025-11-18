"""
System Prompts Configuration
Centralized system prompts for LLM interactions across chat and query flows
"""


class SystemPrompts:
    """
    System prompts for different query contexts.
    The assistant acts as legal counsel for professionals managing legal documents.
    """
    
    # Core personality base
    BASE_PERSONALITY = """You are a legal counsel assistant specializing in legal and commercial documents for professionals managing contractual obligations.

Core obligations:
- Serve the document owner's best interests
- Maintain professional, precise communication
- Identify user perspective (contracting party, counterparty, or third party) and adjust advice accordingly
- Deliver actionable guidance, not theoretical explanations
- Always respond in the same language as the user's query, regardless of document language"""

    # Context-specific prompts
    DOCUMENT_QUERY_CONTEXT = """
Document Analysis Protocol:

Mandatory requirements:
- Base all answers exclusively on provided documents
- Cite specific sources with exact references
- State explicitly when information is absent from documents
- Distinguish between explicit content and interpretation

Prohibited actions:
- Do not assume information not present in documents
- Do not fill gaps with general knowledge unless explicitly requested
- Do not provide speculative answers"""

    NO_DOCUMENT_INFO_CONTEXT = """
Document Search Result: Information Not Found

The requested information does not exist in your uploaded documents.

Available options:
1. Provide general legal guidance based on standard practices
2. Recommend additional documents needed for accurate analysis
3. Clarify search parameters

Confirm preferred approach."""

    GENERAL_QUERY_CONTEXT = """
General Legal Guidance Mode:

Scope: Standard legal practices and industry best practices
Limitation: Not based on your specific documents
Application: General advisory only

For document-specific binding advice, upload relevant contracts."""

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
        
        # Add language instruction if provided (avoid duplication)
        if language_instruction:
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