"""
Document Summarization Service
Implements hierarchical map-reduce summarization for legal documents
"""
import logging
import re
import time
import uuid
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from domain.documents.models import DocumentSummary, SummaryMetadata
from infrastructure.storage.summary_storage import SummaryStorage

logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Service for generating hierarchical document summaries
    
    Uses map-reduce strategy:
    1. Split chunks into batches of 15
    2. Generate batch summaries
    3. If >3 batches, create section summaries
    4. Generate final summary with structure detection
    """
    
    # Batch size for processing chunks
    BATCH_SIZE = 15
    
    # Section threshold (if >3 batches, create sections)
    SECTION_THRESHOLD = 3
    
    # Target word counts
    TARGET_WORDS = 800
    MAX_WORDS = 1600
    
    def __init__(
        self,
        llm_func: Callable[[str], Awaitable[str]],
        rag_engine: 'RAGEngine',
        summary_storage: SummaryStorage
    ):
        """
        Initialize summarization service
        
        Args:
            llm_func: Async function to call LLM with prompt
            rag_engine: RAG engine for accessing document chunks
            summary_storage: Storage for summaries
        """
        self.llm_func = llm_func
        self.rag_engine = rag_engine
        self.summary_storage = summary_storage
    
    async def generate_summary(
        self,
        document_id: str,
        progress_callback: Optional[Callable[[Dict], Awaitable[None]]] = None
    ) -> DocumentSummary:
        """
        Generate or retrieve cached summary for a document
        
        Args:
            document_id: Document to summarize
            progress_callback: Optional callback for progress updates
            
        Returns:
            DocumentSummary
        """
        # Check if summary already exists
        existing_summary = await self.summary_storage.get_summary(document_id)
        if existing_summary:
            logger.info(f"Returning cached summary for document {document_id}")
            return existing_summary
        
        start_time = time.time()
        
        try:
            # Stage 1: Initializing
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "initializing",
                    "progress_percent": 5,
                    "message": "Preparing document for summarization..."
                })
            
            # Get document chunks from RAG engine
            chunks = await self._get_document_chunks(document_id)
            if not chunks:
                raise ValueError(f"No chunks found for document {document_id}")
            
            # Get document name
            document_name = await self._get_document_name(document_id)
            
            total_chunks = len(chunks)
            logger.info(f"Starting summarization for document {document_id} ({total_chunks} chunks)")
            
            # Detect structure early
            structure = await self._detect_structure(chunks)
            
            # Calculate batches
            batches = self._create_batches(chunks, self.BATCH_SIZE)
            total_batches = len(batches)
            
            logger.info(f"Created {total_batches} batches of {self.BATCH_SIZE} chunks each")
            
            # Stage 2: Batch Processing
            batch_summaries = []
            for batch_num, batch in enumerate(batches, 1):
                if progress_callback:
                    progress_percent = 10 + int((batch_num / total_batches) * 60)
                    await progress_callback({
                        "document_id": document_id,
                        "stage": "batch_processing",
                        "progress_percent": progress_percent,
                        "current_batch": batch_num,
                        "total_batches": total_batches,
                        "message": f"Processing batch {batch_num} of {total_batches}..."
                    })
                
                batch_summary = await self._process_batch(
                    batch, batch_num, total_batches, document_name
                )
                batch_summaries.append(batch_summary)
                
                logger.debug(f"Batch {batch_num}/{total_batches} summarized")
            
            # Stage 3: Section Merging (if needed)
            if total_batches > self.SECTION_THRESHOLD:
                if progress_callback:
                    await progress_callback({
                        "document_id": document_id,
                        "stage": "section_merging",
                        "progress_percent": 75,
                        "message": "Organizing sections..."
                    })
                
                section_summaries = await self._create_section_summaries(
                    batch_summaries, document_name
                )
                summaries_to_merge = section_summaries
            else:
                summaries_to_merge = batch_summaries
            
            # Stage 4: Finalizing
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "finalizing",
                    "progress_percent": 85,
                    "message": "Creating final summary..."
                })
            
            # Merge all summaries
            merged_summary = await self._merge_summaries(
                summaries_to_merge, document_name
            )
            
            # Format final summary with structure
            final_summary = await self._format_final_summary(
                merged_summary, structure, document_name
            )
            
            # Detect language
            language = await self._detect_language(final_summary)
            
            generation_time = time.time() - start_time
            
            # Create DocumentSummary object
            summary = DocumentSummary(
                summary_id=str(uuid.uuid4()),
                document_id=document_id,
                original_language=language,
                original_summary=final_summary,
                metadata=SummaryMetadata(
                    document_id=document_id,
                    document_name=document_name,
                    total_chunks=total_chunks,
                    batches_processed=total_batches,
                    generation_time_seconds=generation_time,
                    structure_detected=structure.get("detected", False),
                    language=language,
                    created_at=datetime.utcnow(),
                    model_used=self._get_model_name()
                ),
                translations={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save summary
            await self.summary_storage.save_summary(summary)
            
            # Stage 5: Completed
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "completed",
                    "progress_percent": 100,
                    "message": "Summary generation complete!",
                    "summary_id": summary.summary_id
                })
            
            logger.info(f"Summary generated for document {document_id} in {generation_time:.2f}s")
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed for document {document_id}: {e}")
            
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "failed",
                    "progress_percent": 0,
                    "message": f"Summary generation failed: {str(e)}"
                })
            
            raise
    
    async def translate_summary(
        self,
        document_id: str,
        user_language_input: str,
        progress_callback: Optional[Callable[[Dict], Awaitable[None]]] = None
    ) -> str:
        """
        Translate summary to target language
        
        Args:
            document_id: Document ID
            user_language_input: User's free-text language input
            progress_callback: Optional progress callback
            
        Returns:
            Translated summary text
        """
        try:
            # Detect target language
            target_language = await self._detect_target_language(user_language_input)
            
            logger.info(f"Translating summary for document {document_id} to {target_language}")
            
            # Load original summary
            summary = await self.summary_storage.get_summary(document_id)
            if not summary:
                raise ValueError(f"No summary found for document {document_id}")
            
            # Check if translation exists
            existing_translation = summary.translations.get(target_language)
            if existing_translation:
                logger.info(f"Returning cached translation for {document_id} -> {target_language}")
                return existing_translation
            
            # Check if original is already in target language
            if summary.original_language == target_language:
                logger.info(f"Original summary is already in {target_language}")
                return summary.original_summary
            
            # Generate translation
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "translating",
                    "progress_percent": 50,
                    "message": f"Translating to {target_language}..."
                })
            
            translated_text = await self._generate_translation(
                summary.original_summary,
                target_language
            )
            
            # Cache translation
            await self.summary_storage.save_translation(
                document_id, target_language, translated_text
            )
            
            if progress_callback:
                await progress_callback({
                    "document_id": document_id,
                    "stage": "completed",
                    "progress_percent": 100,
                    "message": "Translation complete!"
                })
            
            logger.info(f"Translation completed for {document_id} -> {target_language}")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed for document {document_id}: {e}")
            raise
    
    async def _get_document_chunks(self, document_id: str) -> List[str]:
        """Get all chunks for a document from RAG storage"""
        try:
            # Access LightRAG's chunk storage
            chunks = await self.rag_engine.get_document_chunks(document_id)
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for document {document_id}: {e}")
            raise
    
    async def _get_document_name(self, document_id: str) -> str:
        """Get document name from registry"""
        try:
            # Import here to avoid circular dependency
            from core.dependencies import get_document_registry
            registry = get_document_registry()
            
            doc_data = await registry.get_document(document_id)
            if doc_data:
                return doc_data.get("filename", "Unknown Document")
            
            return "Unknown Document"
        except Exception as e:
            logger.warning(f"Could not get document name for {document_id}: {e}")
            return "Unknown Document"
    
    def _create_batches(self, chunks: List[str], batch_size: int) -> List[List[str]]:
        """Split chunks into batches"""
        batches = []
        for i in range(0, len(chunks), batch_size):
            batches.append(chunks[i:i + batch_size])
        return batches
    
    async def _process_batch(
        self,
        chunks: List[str],
        batch_num: int,
        total_batches: int,
        document_name: str
    ) -> str:
        """
        Process a batch of chunks and generate summary
        
        Args:
            chunks: List of chunk texts
            batch_num: Current batch number
            total_batches: Total number of batches
            document_name: Document name
            
        Returns:
            Batch summary text
        """
        batch_content = "\n\n".join(chunks)
        
        prompt = f"""You are a legal document summarization expert. Summarize the following section from a legal document.

Document: {document_name}
Section {batch_num}/{total_batches}

Maintain all critical legal information including:
- Parties involved
- Key obligations and rights
- Important dates and terms
- Financial amounts and conditions
- Legal clauses and provisions

Preserve the original document structure when present (numbered sections, clauses, etc.).

Content to summarize:
{batch_content}

Provide a clear, comprehensive summary in the same language as the source document."""
        
        summary = await self.llm_func(prompt)
        return summary
    
    async def _create_section_summaries(
        self,
        batch_summaries: List[str],
        document_name: str
    ) -> List[str]:
        """
        Create section summaries from batch summaries
        
        Args:
            batch_summaries: List of batch summary texts
            document_name: Document name
            
        Returns:
            List of section summary texts
        """
        # Group batches into sections (3-4 batches per section)
        section_size = 3
        sections = []
        
        for i in range(0, len(batch_summaries), section_size):
            section_batches = batch_summaries[i:i + section_size]
            section_content = "\n\n".join(section_batches)
            
            prompt = f"""You are a legal document summarization expert. Merge the following batch summaries into a cohesive section summary.

Document: {document_name}
Section {i//section_size + 1}

Batch summaries to merge:
{section_content}

Create a unified section summary that maintains all critical information and document structure. Use the same language as the source summaries."""
            
            section_summary = await self.llm_func(prompt)
            sections.append(section_summary)
        
        logger.info(f"Created {len(sections)} section summaries from {len(batch_summaries)} batches")
        
        return sections
    
    async def _merge_summaries(
        self,
        summaries: List[str],
        document_name: str
    ) -> str:
        """
        Merge section or batch summaries into final summary
        
        Args:
            summaries: List of summary texts to merge
            document_name: Document name
            
        Returns:
            Merged summary text
        """
        summaries_content = "\n\n".join(summaries)
        
        prompt = f"""You are a legal document summarization expert. Create a comprehensive summary by merging these section summaries.

Document: {document_name}
Total sections: {len(summaries)}

Requirements:
- Generate a 1-2 page summary (target {self.TARGET_WORDS} words, max {self.MAX_WORDS} words)
- Maintain document structure (sections, clauses, addendums)
- Preserve all critical legal information
- Use clear, professional language
- Output in the same language as the source document

Section summaries to merge:
{summaries_content}

Provide the final comprehensive summary."""
        
        merged = await self.llm_func(prompt)
        return merged
    
    async def _detect_structure(self, chunks: List[str]) -> Dict[str, Any]:
        """
        Detect document structure from chunks
        
        Args:
            chunks: List of chunk texts
            
        Returns:
            Structure information dict
        """
        # Scan first 5 chunks for patterns
        sample_chunks = chunks[:min(5, len(chunks))]
        sample_text = " ".join(sample_chunks)
        
        structure = {
            "detected": False,
            "section_markers": [],
            "hierarchy_levels": [],
            "has_clauses": False
        }
        
        # Detect numbered sections (1., 1.1, Article I, etc.)
        numbered_pattern = r'\b(?:\d+\.)+\d*\s|\b[A-Z]+\.\s|\bArticle\s+[IVX]+\b|\bSection\s+\d+\b'
        numbered_matches = re.findall(numbered_pattern, sample_text)
        
        if numbered_matches:
            structure["detected"] = True
            structure["section_markers"] = list(set(numbered_matches))
        
        # Detect legal clauses
        clause_pattern = r'\b(?:WHEREAS|NOW THEREFORE|PROVIDED THAT|WITNESSETH)\b'
        if re.search(clause_pattern, sample_text):
            structure["detected"] = True
            structure["has_clauses"] = True
        
        # Detect hierarchy levels
        if re.search(r'\b(?:Article|Chapter|Part|Section|Subsection)\b', sample_text, re.IGNORECASE):
            structure["hierarchy_levels"] = ["article", "section", "subsection"]
        
        logger.info(f"Structure detection: {structure}")
        
        return structure
    
    async def _format_final_summary(
        self,
        merged_summary: str,
        structure: Dict[str, Any],
        document_name: str
    ) -> str:
        """
        Format final summary with structure enhancement
        
        Args:
            merged_summary: Merged summary text
            structure: Detected structure information
            document_name: Document name
            
        Returns:
            Formatted final summary
        """
        if not structure.get("detected"):
            # No structure detected, return as-is
            return merged_summary
        
        # Enhance structure if detected
        prompt = f"""You are a legal document summarization expert. Format and enhance this summary to better reflect the document's structure.

Document: {document_name}

Detected structure:
- Section markers: {structure.get('section_markers', [])}
- Hierarchy levels: {structure.get('hierarchy_levels', [])}
- Has legal clauses: {structure.get('has_clauses', False)}

Current summary:
{merged_summary}

Requirements:
- Maintain section numbering from original document
- Use markdown formatting (##, ###) for hierarchy
- Keep all critical legal information
- Target length: {self.TARGET_WORDS}-{self.MAX_WORDS} words
- Use the same language as the source summary

Provide the enhanced, well-structured final summary."""
        
        formatted = await self.llm_func(prompt)
        return formatted
    
    async def _detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO 639-1 language code
        """
        # Use LLM for accurate language detection
        prompt = f"""Identify the primary language of the following text and respond ONLY with the ISO 639-1 two-letter language code (e.g., 'en' for English, 'he' for Hebrew, 'ar' for Arabic, 'es' for Spanish).

Text:
{text[:500]}

Respond with ONLY the two-letter language code:"""
        
        response = await self.llm_func(prompt)
        language_code = response.strip().lower()[:2]
        
        # Validate code (basic check)
        if len(language_code) == 2 and language_code.isalpha():
            return language_code
        
        # Default to English if detection fails
        logger.warning(f"Language detection failed, defaulting to 'en': {response}")
        return "en"
    
    async def _detect_target_language(self, user_input: str) -> str:
        """
        Detect target language from user's natural language input
        
        Args:
            user_input: User's language input (e.g., "אנגלית", "English", "Español")
            
        Returns:
            ISO 639-1 language code
        """
        prompt = f"""Identify the language that the user wants to translate to, based on their input. Respond ONLY with the ISO 639-1 two-letter language code.

User input: {user_input}

Examples:
- "אנגלית" -> "en"
- "English" -> "en"
- "Español" -> "es"
- "Hebrew" -> "he"
- "عربي" -> "ar"

Respond with ONLY the two-letter language code:"""
        
        response = await self.llm_func(prompt)
        language_code = response.strip().lower()[:2]
        
        # Validate code
        if len(language_code) == 2 and language_code.isalpha():
            return language_code
        
        # Default to English if detection fails
        logger.warning(f"Target language detection failed, defaulting to 'en': {response}")
        return "en"
    
    async def _generate_translation(
        self,
        original_summary: str,
        target_language: str
    ) -> str:
        """
        Generate translation of summary
        
        Args:
            original_summary: Original summary text
            target_language: Target language ISO code
            
        Returns:
            Translated summary text
        """
        # Map language codes to full names for better LLM understanding
        language_names = {
            "en": "English",
            "he": "Hebrew",
            "ar": "Arabic",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian",
            "zh": "Chinese"
        }
        
        target_language_name = language_names.get(target_language, target_language)
        
        prompt = f"""Translate the following legal document summary to {target_language_name}.

Requirements:
- Maintain all legal terminology accurately
- Preserve markdown formatting exactly
- Keep section structure intact
- Use professional legal language

Original summary:
{original_summary}

Provide the translated summary in {target_language_name}:"""
        
        translation = await self.llm_func(prompt)
        return translation
    
    def _get_model_name(self) -> str:
        """Get the LLM model name being used"""
        try:
            # Try to get model from RAG engine settings
            if hasattr(self.rag_engine, 'llm_model'):
                return self.rag_engine.llm_model
            return "gpt-4o-mini"  # Default
        except:
            return "gpt-4o-mini"

