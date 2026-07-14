"""Safe multipart upload helpers with early size gating."""

from __future__ import annotations

from fastapi import UploadFile

from app.core.exceptions import ValidationException
from app.utils.files import sanitize_filename


async def read_upload_limited(file: UploadFile, *, max_bytes: int) -> bytes:
    """
    Read an uploaded file without buffering more than ``max_bytes``.

    Prefer Content-Length rejection when the client advertised a larger body.
    """
    if max_bytes <= 0:
        raise ValidationException("Invalid upload size limit")

    content_length = file.size
    if content_length is not None and content_length > max_bytes:
        raise ValidationException(
            f"Image exceeds maximum size of {max_bytes} bytes",
            details={"max_bytes": max_bytes, "content_length": content_length},
        )

    chunks: list[bytes] = []
    total = 0
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValidationException(
                f"Image exceeds maximum size of {max_bytes} bytes",
                details={"max_bytes": max_bytes},
            )
        chunks.append(chunk)

    if total <= 0:
        raise ValidationException("Empty image upload is not allowed")
    return b"".join(chunks)


def safe_upload_filename(filename: str | None, *, default: str = "upload.bin") -> str:
    """Sanitize client-supplied filenames for logging and extension checks."""
    return sanitize_filename(filename or default)
