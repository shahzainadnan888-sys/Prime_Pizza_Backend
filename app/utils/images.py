"""Image helper utilities (Cloudinary-ready)."""

from __future__ import annotations

from typing import BinaryIO

ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp", "gif"})

_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"RIFF", "webp"),  # WebP: RIFF....WEBP
)


def is_allowed_image(filename: str) -> bool:
    """Return True when filename has an allowed image extension."""
    extension = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    return extension in ALLOWED_IMAGE_EXTENSIONS


def sniff_image_type(file_obj: BinaryIO) -> str | None:
    """
    Detect image type from magic bytes.

    Returns a normalized type name (jpeg/png/gif/webp) or None.
    Resets the stream position after reading.
    """
    position = file_obj.tell()
    try:
        header = file_obj.read(16)
    finally:
        file_obj.seek(position)

    if not header:
        return None

    for signature, image_type in _IMAGE_SIGNATURES:
        if header.startswith(signature):
            if image_type == "webp":
                if len(header) >= 12 and header[8:12] == b"WEBP":
                    return "webp"
                return None
            return image_type
    return None


def is_valid_image_content(file_obj: BinaryIO) -> bool:
    """Return True when the file content looks like an allowed image."""
    return sniff_image_type(file_obj) is not None
