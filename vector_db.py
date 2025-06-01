from __future__ import annotations
import json, os, tempfile, logging
from typing import Optional, Iterable, Dict
from imap_tools import MailMessage
from openai import OpenAI, NotFoundError

log = logging.getLogger(__name__)
client = OpenAI()

class EmailVectorDB:
    """
    Thin helper around an OpenAI Vector Store for email messages.
    Holds **only** the store‑ID; all message‑level data lives inside the store.
    """
    def __init__(self, name: str = "email_db"):
        self._name = name
        self._vector_store_id: Optional[str] = None  

    # --------------- helpers -----------------
    @staticmethod
    def _body(msg: MailMessage) -> str:
        return msg.text.strip() if msg.text else msg.html.strip()

    def _require_store(self) -> str:
        if self._vector_store_id is None:
            vs = client.vector_stores.create(name=self._name)
            self._vector_store_id = vs.id
            log.info("Created vector store %s (%s)", self._name, vs.id)
        return self._vector_store_id

    # --------------- public API ---------------
    def addEmails(self, emails: [MailMessage]) -> list[str]:
        """
        Upload one or more MailMessage objects.
        Returns the list of file_ids created (and stores each id back
        into that file’s own `attributes` for future self‑reference).
        """
        if not emails:
            return []

        vs_id = self._require_store()

        # 1) serialise each email to a temp JSON file
        tmp_paths, rec_attributes = [], []
        for m in emails:
            attrs = {
                "subject": m.subject,
                "from":    m.from_,
                "date":    m.date.isoformat(),
            }
            rec = {
                "text": (
                    f"Subject: {m.subject}\n"
                    f"From: {m.from_}\n"
                    f"Date: {m.date}\n\n{self._body(m)}"
                ),
                "metadata": attrs,   # user‑visible meta for retrieval
            }
            f = tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False)
            json.dump(rec, f)
            f.close()
            tmp_paths.append(f.name)
            rec_attributes.append(attrs)

        # 2) upload & poll
        streams = [open(p, "rb") for p in tmp_paths]
        try:
            batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs_id,
                files=streams,
            )
        finally:
            for s in streams: s.close()
            for p in tmp_paths: os.remove(p)

        file_ids = [f.id for f in batch.file_batch.files]

        # 3) write the file‑id back into each file’s attributes
        for fid, attrs in zip(file_ids, rec_attributes):
            attrs["file_id"] = fid
            client.vector_stores.files.update(           # ← single PATCH call
                vector_store_id=vs_id,
                file_id=fid,
                attributes=attrs,
            )

        return file_ids

    def removeEmail(self, file_id: str) -> bool:
        """Delete a single message by file‑id (True if existed)."""
        if self._vector_store_id is None:
            return False
        try:
            client.vector_stores.files.delete(
                vector_store_id=self._vector_store_id, file_id=file_id)
            client.files.delete(file_id)
            return True
        except NotFoundError:
            return False

    def getDatabase(self) -> Optional[str]:
        return self._vector_store_id

    def deleteDatabase(self) -> None:
        """Nuke every file in the store, then the store itself."""
        if self._vector_store_id is None:
            return

        # list *current* files → delete all
        files = client.vector_stores.files.list(
            vector_store_id=self._vector_store_id).data
        for f in files:
            try:
                client.vector_stores.files.delete(
                    vector_store_id=self._vector_store_id,
                    file_id=f.id)
                client.files.delete(f.id)
            except Exception as e:
                log.debug("Skip file %s: %s", f.id, e)

        # finally remove the store
        try:
            client.vector_stores.delete(self._vector_store_id)
            log.info("Deleted vector store %s", self._vector_store_id)
        except Exception as e:
            log.warning("Could not delete vector store: %s", e)
        finally:
            self._vector_store_id = None
