import base64
import re
import uuid
from io import BytesIO
from typing import Tuple

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from PIL import Image, ImageFile
from PIL.Image import DecompressionBombError


# =========================
# Sécurité Pillow globale
# =========================
Image.MAX_IMAGE_PIXELS = 20_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False


# =========================
# Base64 parsing
# =========================
MAX_BASE64_LENGTH = 15 * 1024 * 1024  # ~15MB texte

DATA_URI_RE = re.compile(
    r'^data:(?P<mime>[-\w.+/]+)(?:;charset=[^;]+)?;base64,(?P<data>[A-Za-z0-9+/=\s]+)$'
)


def decode_base64_strict(base64_string: str) -> Tuple[bytes, str | None]:
    if not base64_string:
        raise ValidationError("Base64 vide")

    if len(base64_string) > MAX_BASE64_LENGTH:
        raise ValidationError("Payload Base64 trop volumineux")

    match = DATA_URI_RE.match(base64_string.strip())
    if match:
        declared_mime = match.group("mime")
        data = match.group("data")
    else:
        declared_mime = None
        data = base64_string.strip()

    try:
        binary = base64.b64decode(data, validate=True)
    except Exception:
        raise ValidationError("Base64 invalide")

    return binary, declared_mime


# =========================
# Magic bytes (réels)
# =========================
def detect_mime_from_magic(binary: bytes) -> Tuple[str, str]:
    if binary.startswith(b"%PDF"):
        return "application/pdf", "pdf"

    if binary.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg", "jpg"

    if binary.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"

    if binary.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", "gif"

    # WEBP : RIFF....WEBP
    if binary[:4] == b"RIFF" and binary[8:12] == b"WEBP":
        return "image/webp", "webp"

    # ZIP (docx, xlsx, etc.)
    if binary.startswith(b"PK\x03\x04"):
        return "application/zip", "zip"

    raise ValidationError("Type de fichier inconnu ou non supporté")


# =========================
# Image handler sécurisé
# =========================
class Base64ImageHandler:
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
    MAX_SIZE_MB = 10

    def __init__(self, max_size_mb: int = MAX_SIZE_MB):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def handle(
        self,
        binary: bytes,
        filename_prefix: str = "image",
        max_dimensions: tuple[int, int] | None = (1920, 1080),
        quality: int = 85,
    ) -> ContentFile:

        if len(binary) > self.max_size_bytes:
            raise ValidationError("Image trop volumineuse")

        try:
            img = Image.open(BytesIO(binary))
            img.load()
        except DecompressionBombError:
            raise ValidationError("Image trop grande (decompression bomb)")
        except Exception:
            raise ValidationError("Image invalide ou corrompue")

        if img.format not in self.ALLOWED_FORMATS:
            raise ValidationError(f"Format image non autorisé: {img.format}")

        # Refuser explicitement les GIF animés
        if img.format == "GIF" and getattr(img, "is_animated", False):
            raise ValidationError("GIF animés non supportés")

        # Redimensionnement
        if max_dimensions:
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

        # Conversion alpha uniquement pour JPEG
        if img.format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        output = BytesIO()
        save_kwargs = {"optimize": True}

        if img.format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality

        img.save(output, format=img.format, **save_kwargs)

        ext = img.format.lower().replace("jpeg", "jpg")
        filename_prefix = re.sub(r"[^a-zA-Z0-9_-]", "", filename_prefix)

        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{ext}"
        return ContentFile(output.getvalue(), name=filename)


# =========================
# Document handler sécurisé
# =========================
class Base64DocumentHandler:
    ALLOWED_MIME = {"application/pdf"}
    MAX_SIZE_MB = 15

    def __init__(self, max_size_mb: int = MAX_SIZE_MB):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def handle(self, binary: bytes, filename_prefix: str = "doc") -> ContentFile:
        if len(binary) > self.max_size_bytes:
            raise ValidationError("Document trop volumineux")

        mime, ext = detect_mime_from_magic(binary)

        if mime not in self.ALLOWED_MIME:
            raise ValidationError(f"Type document non autorisé: {mime}")

        filename_prefix = re.sub(r"[^a-zA-Z0-9_-]", "", filename_prefix)
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{ext}"

        return ContentFile(binary, name=filename)


# =========================
# Handler global unifié
# =========================
class Base64FileHandler:
    def __init__(self):
        self.image_handler = Base64ImageHandler()
        self.document_handler = Base64DocumentHandler()

    def handle(self, base64_string: str, filename_prefix: str = "file", **kwargs) -> ContentFile:
        binary, declared_mime = decode_base64_strict(base64_string)

        detected_mime, _ = detect_mime_from_magic(binary)

        if detected_mime.startswith("image/"):
            return self.image_handler.handle(binary, filename_prefix, **kwargs)
        else:
            return self.document_handler.handle(binary, filename_prefix)
