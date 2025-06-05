from __future__ import annotations

import hashlib
import io
import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from imap_tools.message import MailMessage 
from config import OPENAI_CLIENT

__all__ = [
    "EmailVectorStoreManager",
    "BaseVectorBackend",
    "OpenAIVectorBackend",
]

###############################################################################
# Backend protocol
###############################################################################

class BaseVectorBackend(ABC):
    """Abstract interface any vector‑store backend must implement."""

    @abstractmethod
    def add_file(
        self,
        *,
        file_bytes: bytes,
        file_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store *one* document and return its **file/vector ID**."""

    @abstractmethod
    def delete_file(self, *, file_id: str) -> None:
        """Remove a document (identified by *file_id*) from the store."""

    @abstractmethod
    def get_vector_store_id(self) -> str:
        """Return the backend‑specific *vector store ID* (stable identifier)."""

###############################################################################
# OpenAI backend
###############################################################################

class OpenAIVectorBackend(BaseVectorBackend):
    """Implementation backed by **OpenAI Vector Store**."""

    def __init__(self, *, store_name: str) -> None:
        self.client = OPENAI_CLIENT
        # Re‑use existing store or create a new one with the given *name*.
        vs = self._get_or_create_store(store_name)
        self._vector_store_id: str = vs.id

    # ------------------------------------------------------------------
    # Public API – implementation of BaseVectorBackend
    # ------------------------------------------------------------------

    def add_file(
        self,
        *,
        file_bytes: bytes,
        file_name: str,
        metadata: Optional[Dict[str, Any]] | None = None,
    ) -> str:
        buffer = io.BytesIO(file_bytes)
        buffer.name = file_name 
        file_obj = self.client.files.create(
            file=buffer,
            purpose="assistants",
        )
        # # 2️⃣  Attach custom metadata, if provided.
        # if metadata:
        #     self.client.files.update(file_obj.id, metadata=metadata)

        # 3️⃣  Attach to the vector store (blocking until processed).
        self.client.vector_stores.file_batches.create(
            vector_store_id=self._vector_store_id,
            file_ids=[file_obj.id],
        )
        return file_obj.id

    def delete_file(self, *, file_id: str) -> None:
        self.client.vector_stores.files.delete(
            vector_store_id=self._vector_store_id,
            file_id=file_id,
        )

    def get_vector_store_id(self) -> str: 
        return self._vector_store_id

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_or_create_store(self, name: str):
        page = self.client.vector_stores.list(limit=100)
        for vs in page.data:
            if vs.name == name:
                return vs
        # Not found – create a fresh one.
        return self.client.vector_stores.create(name=name)

###############################################################################
# Manager with local SQLite index (deduplication)
###############################################################################

class EmailVectorStoreManager:
    """High‑level convenience wrapper around a :class:BaseVectorBackend."""

    def __init__(
        self,
        *,
        store_name: str = "emails",
        db_path: str | os.PathLike[str] = "vector_store_index.db",
        backend: Optional[BaseVectorBackend] = None,
    ) -> None:
        self.backend = backend or OpenAIVectorBackend(store_name=store_name)
        self._conn = sqlite3.connect(Path(db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                hash       TEXT PRIMARY KEY,
                file_id    TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Public helpers – new MailMessage‑centric API
    # ------------------------------------------------------------------

    def add_message(self, msg: MailMessage, *, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add one *MailMessage*; returns the **file/vector ID**.

        Duplicate detection uses a stable SHA‑256 hash of
        msg.message_id (fallback to uid) + body.
        """
        body = self._get_message_body(msg)
        message_id = self._get_message_id(msg)
        subject = msg.subject or "(no subject)"

        digest = self._digest(message_id, body)
        cur = self._conn.execute("SELECT file_id FROM emails WHERE hash = ?", (digest,))
        row = cur.fetchone()
        if row:
            return row[0]  # Already ingested.

        payload = f"Subject: {subject}\n\n{body}"
        file_id = self.backend.add_file(
            file_bytes=payload.encode(),
            file_name=f"{message_id}.txt",
            metadata=metadata,
        )
        self._conn.execute(
            "INSERT INTO emails(hash, file_id) VALUES (?, ?)", (digest, file_id)
        )
        self._conn.commit()
        return file_id

    def delete_message(self, msg: MailMessage) -> bool:
        """Remove a MailMessage. Returns **True** if deletion occurred."""
        body = self._get_message_body(msg)
        message_id = self._get_message_id(msg)
        digest = self._digest(message_id, body)

        cur = self._conn.execute("SELECT file_id FROM emails WHERE hash = ?", (digest,))
        row = cur.fetchone()
        if not row:
            return False  # Nothing to do.

        file_id: str = row[0]
        self.backend.delete_file(file_id=file_id)
        self._conn.execute("DELETE FROM emails WHERE hash = ?", (digest,))
        self._conn.commit()
        return True

    def get_vector_store_id(self) -> str:
        return self.backend.get_vector_store_id()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_message_body(msg: MailMessage) -> str:
        return (msg.text or "") or (msg.html or "")
    
    @staticmethod
    def _get_message_id(msg: MailMessage) -> str:
        return str(msg.uid)

    @staticmethod
    def _digest(message_id: str, body: str) -> str:  # pragma: no cover
        return hashlib.sha256(f"{message_id}\x00{body}".encode()).hexdigest()