"""
Summary Storage
Manages persistent storage for document summaries and translations
"""
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from domain.documents.models import DocumentSummary, SummaryMetadata
from core.config import get_settings

logger = logging.getLogger(__name__)


class SummaryStorage:
    """
    Storage manager for document summaries
    
    Storage structure:
    ~/.covenantrix/summaries/
    ├── {doc-id-1}/
    │   ├── summary_he.json          # Original summary in Hebrew
    │   ├── summary_en.json          # English translation
    │   └── summary_ar.json          # Arabic translation
    ├── {doc-id-2}/
    │   └── summary_en.json          # Original summary in English
    └── ...
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize summary storage
        
        Args:
            storage_dir: Base storage directory (defaults to ~/.covenantrix/summaries)
        """
        if storage_dir is None:
            settings = get_settings()
            storage_dir = Path(settings.storage.working_dir) / "summaries"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Summary storage initialized: {self.storage_dir}")
    
    def _get_document_dir(self, document_id: str) -> Path:
        """Get directory for a document's summaries"""
        return self.storage_dir / document_id
    
    def _get_summary_file(self, document_id: str, language: str) -> Path:
        """Get file path for a summary in a specific language"""
        return self._get_document_dir(document_id) / f"summary_{language}.json"
    
    async def save_summary(self, summary: DocumentSummary) -> None:
        """
        Save a document summary
        
        Args:
            summary: DocumentSummary to save
        """
        try:
            # Create document directory
            doc_dir = self._get_document_dir(summary.document_id)
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Save original summary
            summary_file = self._get_summary_file(
                summary.document_id, 
                summary.original_language
            )
            
            summary_data = {
                "summary_id": summary.summary_id,
                "document_id": summary.document_id,
                "original_language": summary.original_language,
                "original_summary": summary.original_summary,
                "metadata": {
                    "document_id": summary.metadata.document_id,
                    "document_name": summary.metadata.document_name,
                    "total_chunks": summary.metadata.total_chunks,
                    "batches_processed": summary.metadata.batches_processed,
                    "generation_time_seconds": summary.metadata.generation_time_seconds,
                    "structure_detected": summary.metadata.structure_detected,
                    "language": summary.metadata.language,
                    "created_at": summary.metadata.created_at.isoformat(),
                    "model_used": summary.metadata.model_used
                },
                "translations": summary.translations,
                "created_at": summary.created_at.isoformat(),
                "updated_at": summary.updated_at.isoformat()
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Summary saved: {summary.document_id} (language: {summary.original_language})")
            
        except Exception as e:
            logger.error(f"Failed to save summary for document {summary.document_id}: {e}")
            raise
    
    async def get_summary(
        self, 
        document_id: str, 
        language: Optional[str] = None
    ) -> Optional[DocumentSummary]:
        """
        Get a document summary
        
        Args:
            document_id: Document ID
            language: Optional language code (if None, returns original summary)
            
        Returns:
            DocumentSummary or None if not found
        """
        try:
            doc_dir = self._get_document_dir(document_id)
            if not doc_dir.exists():
                return None
            
            # Find original summary file (any language)
            summary_files = list(doc_dir.glob("summary_*.json"))
            if not summary_files:
                return None
            
            # Load original summary
            original_file = summary_files[0]
            with open(original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct summary
            summary = DocumentSummary(
                summary_id=data["summary_id"],
                document_id=data["document_id"],
                original_language=data["original_language"],
                original_summary=data["original_summary"],
                metadata=SummaryMetadata(
                    document_id=data["metadata"]["document_id"],
                    document_name=data["metadata"]["document_name"],
                    total_chunks=data["metadata"]["total_chunks"],
                    batches_processed=data["metadata"]["batches_processed"],
                    generation_time_seconds=data["metadata"]["generation_time_seconds"],
                    structure_detected=data["metadata"]["structure_detected"],
                    language=data["metadata"]["language"],
                    created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
                    model_used=data["metadata"]["model_used"]
                ),
                translations=data.get("translations", {}),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get summary for document {document_id}: {e}")
            return None
    
    async def summary_exists(self, document_id: str) -> bool:
        """
        Check if a summary exists for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            True if summary exists
        """
        doc_dir = self._get_document_dir(document_id)
        if not doc_dir.exists():
            return False
        
        summary_files = list(doc_dir.glob("summary_*.json"))
        return len(summary_files) > 0
    
    async def delete_summary(self, document_id: str) -> bool:
        """
        Delete all summaries and translations for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        try:
            doc_dir = self._get_document_dir(document_id)
            if not doc_dir.exists():
                return False
            
            # Delete all summary files
            for summary_file in doc_dir.glob("summary_*.json"):
                summary_file.unlink()
            
            # Remove directory if empty
            try:
                doc_dir.rmdir()
            except OSError:
                pass  # Directory not empty, that's okay
            
            logger.info(f"Summary deleted: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete summary for document {document_id}: {e}")
            return False
    
    async def save_translation(
        self, 
        document_id: str, 
        language: str, 
        translated_text: str
    ) -> None:
        """
        Save a translation for a document summary
        
        Args:
            document_id: Document ID
            language: Target language code
            translated_text: Translated summary text
        """
        try:
            # Load original summary
            summary = await self.get_summary(document_id)
            if not summary:
                raise ValueError(f"No summary found for document {document_id}")
            
            # Update translations
            summary.translations[language] = translated_text
            summary.updated_at = datetime.utcnow()
            
            # Save updated summary
            await self.save_summary(summary)
            
            logger.info(f"Translation saved: {document_id} -> {language}")
            
        except Exception as e:
            logger.error(f"Failed to save translation for document {document_id}: {e}")
            raise
    
    async def get_translation(
        self, 
        document_id: str, 
        language: str
    ) -> Optional[str]:
        """
        Get a translation of a document summary
        
        Args:
            document_id: Document ID
            language: Target language code
            
        Returns:
            Translated text or None if not found
        """
        summary = await self.get_summary(document_id)
        if not summary:
            return None
        
        return summary.translations.get(language)
    
    async def list_available_translations(self, document_id: str) -> List[str]:
        """
        List all available translations for a document summary
        
        Args:
            document_id: Document ID
            
        Returns:
            List of language codes
        """
        summary = await self.get_summary(document_id)
        if not summary:
            return []
        
        # Include original language and all translations
        translations = [summary.original_language]
        translations.extend(summary.translations.keys())
        
        return list(set(translations))  # Remove duplicates

