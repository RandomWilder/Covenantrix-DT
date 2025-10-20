"""
Document Chunk Mapper
Maps user document IDs (UUIDs) to LightRAG chunk IDs for document-scoped queries.

Reads from:
- document_registry.json (user document ID -> content_hash)
- kv_store_doc_status.json (LightRAG doc ID -> chunks_list)

If LightRAG doc ID format differs, attempts multiple deterministic mappings
from content_hash and falls back to best-effort matching.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DocumentChunkMapper:
    """
    Utility for mapping user document IDs to LightRAG chunk IDs.
    """

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = Path(storage_path)
        self.registry_file = self.storage_path / "document_registry.json"
        self.doc_status_file = self.storage_path / "kv_store_doc_status.json"

    def _load_json(self, path: Path) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Required storage file not found: {path}")
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON at {path}: {e}")
            raise

    def _get_content_hashes(self, document_ids: Iterable[str]) -> Dict[str, str]:
        """
        Simplified: just return doc_ids as-is since we now use direct mapping.
        Kept for backward compatibility.
        """
        return {doc_id: doc_id for doc_id in document_ids}

    @staticmethod
    def _candidate_lightrag_doc_ids(content_hash: str) -> List[str]:
        """
        Generate candidate LightRAG doc IDs from a content hash.

        LightRAG commonly uses stable identifiers; we try a few conventions:
        - Exact hash
        - "doc-" + exact hash
        - Prefix variants (first 16/24/32 chars) with and without "doc-"
        """
        prefixes = [content_hash, content_hash[:32], content_hash[:24], content_hash[:16]]
        candidates = []
        for p in prefixes:
            if not p:
                continue
            candidates.append(p)
            candidates.append(f"doc-{p}")
        # Deduplicate, preserve order
        seen = set()
        dedup: List[str] = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                dedup.append(c)
        return dedup

    def _match_doc_id(self, user_doc_id: str, doc_status: Dict) -> Optional[str]:
        """
        Get LightRAG doc ID from stored mapping in registry.
        Falls back to hash-based matching for legacy documents.
        
        Args:
            user_doc_id: User document UUID
            doc_status: Loaded kv_store_doc_status.json data
            
        Returns:
            LightRAG doc ID if found, None otherwise
        """
        try:
            # Load registry to get stored LightRAG doc ID
            registry_data = self._load_json(self.registry_file)
            doc_entry = registry_data.get("documents", {}).get(user_doc_id)
            
            if not doc_entry:
                logger.warning(f"Document {user_doc_id} not found in registry")
                return None
            
            # First, try to use stored LightRAG doc ID (new documents)
            lightrag_doc_id = doc_entry.get("lightrag_doc_id")
            if lightrag_doc_id:
                if lightrag_doc_id in doc_status:
                    logger.debug(f"Found stored LightRAG doc ID: {lightrag_doc_id}")
                    return lightrag_doc_id
                else:
                    logger.warning(f"Stored LightRAG doc ID not found in kv_store: {lightrag_doc_id}")
            
            # Fallback: hash-based matching for legacy documents (uploaded before this change)
            content_hash = doc_entry.get("content_hash")
            if content_hash:
                logger.debug(f"Attempting hash-based fallback for legacy document {user_doc_id}")
                for candidate in self._candidate_lightrag_doc_ids(content_hash):
                    if candidate in doc_status:
                        logger.info(f"Legacy document matched via hash: {candidate}")
                        return candidate
            
            return None
            
        except Exception as e:
            logger.error(f"Error matching doc ID for {user_doc_id}: {e}")
            return None

    def _extract_chunks_from_doc_entry(self, entry: Dict) -> List[str]:
        # Preferred: explicit chunks_list if present
        chunks = entry.get("chunks_list") or entry.get("chunks")
        if isinstance(chunks, list) and all(isinstance(x, str) for x in chunks):
            return chunks

        # Fallbacks: some LightRAG stores may track chunk IDs under different fields
        # Try to infer from mapping structures
        if isinstance(entry, dict):
            # If entry has mapping of chunk_id -> metadata
            possible_map = entry.get("chunk_map") or entry.get("chunks_map")
            if isinstance(possible_map, dict):
                return [str(k) for k in possible_map.keys()]

        return []

    def map_documents_to_chunk_ids(self, document_ids: Iterable[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Map user document IDs to LightRAG chunk IDs.

        Returns tuple of (all_chunk_ids, per_document_chunk_ids)
        """
        document_ids = list(document_ids)
        logger.info(f"Mapping {len(document_ids)} document IDs to chunk IDs")

        content_hashes = self._get_content_hashes(document_ids)
        doc_status = self._load_json(self.doc_status_file)

        all_chunk_ids: List[str] = []
        per_doc: Dict[str, List[str]] = {}

        for doc_id in document_ids:
            # Use doc_id directly (not content_hash) for matching
            lightrag_doc_id = self._match_doc_id(doc_id, doc_status)
            if not lightrag_doc_id:
                logger.warning(f"LightRAG doc ID not found for {doc_id}")
                per_doc[doc_id] = []
                continue

            entry = doc_status.get(lightrag_doc_id, {})
            chunk_ids = self._extract_chunks_from_doc_entry(entry)

            # As an additional fallback, some deployments store per-chunk records under keys
            # that include the doc id; scan once if list is empty and doc_status looks like
            # chunk_id->metadata mapping.
            if not chunk_ids and all(isinstance(v, dict) for v in doc_status.values()):
                inferred: List[str] = []
                for maybe_chunk_id, meta in doc_status.items():
                    if isinstance(maybe_chunk_id, str) and isinstance(meta, dict):
                        file_paths = meta.get("file_paths") or meta.get("files") or []
                        if isinstance(file_paths, list) and doc_id in file_paths:
                            inferred.append(maybe_chunk_id)
                if inferred:
                    chunk_ids = inferred

            per_doc[doc_id] = chunk_ids
            all_chunk_ids.extend(chunk_ids)

        # Deduplicate preserving order
        seen: set[str] = set()
        dedup_all: List[str] = []
        for cid in all_chunk_ids:
            if cid not in seen:
                seen.add(cid)
                dedup_all.append(cid)

        logger.info(
            f"Mapped {len(document_ids)} docs to {len(dedup_all)} chunks; "
            f"non-empty docs: {sum(1 for v in per_doc.values() if v)}"
        )
        return dedup_all, per_doc


