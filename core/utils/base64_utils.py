import base64
import re
import uuid
from io import BytesIO
from typing import Tuple, Optional, Set
from zipfile import ZipFile

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from PIL import Image, ImageFile
from PIL.Image import DecompressionBombError

# =========================
# Configuration globale
# =========================
Image.MAX_IMAGE_PIXELS = 20_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False

MAX_BASE64_LENGTH = 15 * 1024 * 1024  # 15 Mo (texte base64)
MAX_FILE_SIZE = 15 * 1024 * 1024       # 15 Mo pour les fichiers décodés

# Allowlist des types MIME autorisés
ALLOWED_MIME_TYPES: Set[str] = {
    # Images
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    # Documents
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",        # .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation", # .pptx
    "text/plain",
    # Archives (à scanner)
    "application/zip",
}

# =========================
# Détection MIME avec python-magic (fallback manuel)
# =========================
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    import warnings
    warnings.warn("python-magic non installé, utilisation de la détection manuelle limitée.")


def detect_mime_from_magic(binary: bytes) -> Tuple[str, str]:
    """
    Détecte le type MIME et l'extension réelle du fichier.
    Utilise python-magic si disponible, sinon signatures manuelles.
    """
    if HAS_MAGIC:
        try:
            mime = magic.from_buffer(binary, mime=True)
            # Deviner l'extension à partir du mime (simple)
            ext = _guess_extension_from_mime(mime)
            return mime, ext
        except Exception:
            # Fallback silencieux vers la méthode manuelle
            pass

    # --- Méthode manuelle (signatures) ---
    if binary.startswith(b"%PDF"):
        return "application/pdf", "pdf"
    if binary.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg", "jpg"
    if binary.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if binary.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", "gif"
    if binary[:4] == b"RIFF" and binary[8:12] == b"WEBP":
        return "image/webp", "webp"
    if binary.startswith(b"PK\x03\x04"):
        return "application/zip", "zip"
    # Détection basique de texte
    try:
        binary[:512].decode('utf-8')
        if b'\x00' not in binary[:512]:
            return "text/plain", "txt"
    except UnicodeDecodeError:
        pass
    raise ValidationError("Type de fichier inconnu ou non supporté")


def _guess_extension_from_mime(mime: str) -> str:
    """Convertit un type MIME en extension de fichier (simple)."""
    mapping = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "application/zip": "zip",
        "text/plain": "txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    }
    return mapping.get(mime, "bin")


# =========================
# Parsing base64
# =========================
DATA_URI_RE = re.compile(
    r'^data:(?P<mime>[-\w.+/]+)(?:;charset=[^;]+)?;base64,(?P<data>[A-Za-z0-9+/=\s]+)$'
)


def decode_base64_strict(base64_string: str) -> Tuple[bytes, Optional[str]]:
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
# Validation de la taille
# =========================
def validate_file_size(binary: bytes, max_size: int = MAX_FILE_SIZE):
    if len(binary) > max_size:
        raise ValidationError(f"Fichier trop volumineux (max {max_size//1024//1024} Mo)")


# =========================
# Scan optionnel des ZIP
# =========================
def scan_zip(binary: bytes):
    """Vérifie qu'un ZIP ne contient pas de fichiers exécutables."""
    dangerous_extensions = {'.exe', '.bat', '.sh', '.php', '.js', '.jar', '.vbs', '.msi'}
    with ZipFile(BytesIO(binary)) as zf:
        for name in zf.namelist():
            ext = name.lower().split('.')[-1] if '.' in name else ''
            if f'.{ext}' in dangerous_extensions:
                raise ValidationError(f"Le ZIP contient un fichier interdit : {name}")


# =========================
# Handler pour les images (avec redimensionnement)
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
        max_dimensions: Optional[Tuple[int, int]] = (1920, 1080),
        quality: int = 85,
    ) -> ContentFile:
        validate_file_size(binary, self.max_size_bytes)

        try:
            img = Image.open(BytesIO(binary))
            img.load()
        except DecompressionBombError:
            raise ValidationError("Image trop grande (decompression bomb)")
        except Exception:
            raise ValidationError("Image invalide ou corrompue")

        if img.format not in self.ALLOWED_FORMATS:
            raise ValidationError(f"Format image non autorisé: {img.format}")

        if img.format == "GIF" and getattr(img, "is_animated", False):
            raise ValidationError("GIF animés non supportés")

        if max_dimensions:
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

        if img.format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        output = BytesIO()
        save_kwargs = {"optimize": True}
        if img.format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality

        img.save(output, format=img.format, **save_kwargs)

        ext = img.format.lower().replace("jpeg", "jpg")
        filename_prefix = re.sub(r"[^a-zA-Z0-9_-]", "", filename_prefix) or "image"
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{ext}"

        return ContentFile(output.getvalue(), name=filename)


# =========================
# Handler pour les documents (autres types autorisés)
# =========================
class Base64DocumentHandler:
    MAX_SIZE_MB = 15

    def __init__(self, max_size_mb: int = MAX_SIZE_MB):
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def handle(self, binary: bytes, filename_prefix: str = "doc", original_mime: str = None) -> ContentFile:
        validate_file_size(binary, self.max_size_bytes)

        # Le type MIME a déjà été validé par le handler principal
        # On peut éventuellement ajouter des traitements spécifiques selon le type
        if original_mime == "application/zip":
            # Option : scanner le ZIP
            scan_zip(binary)  # décommentez si vous voulez activer le scan

        # Générer un nom de fichier sécurisé
        ext = _guess_extension_from_mime(original_mime) if original_mime else "bin"
        filename_prefix = re.sub(r"[^a-zA-Z0-9_-]", "", filename_prefix) or "file"
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{ext}"

        return ContentFile(binary, name=filename)


# =========================
# Handler principal unifié
# =========================
class Base64FileHandler:
    def __init__(self):
        self.image_handler = Base64ImageHandler()
        self.document_handler = Base64DocumentHandler()

    def handle(self, base64_string: str, filename_prefix: str = "file", **kwargs) -> ContentFile:
        # 1. Décoder et récupérer le type déclaré
        binary, declared_mime = decode_base64_strict(base64_string)

        # 2. Détection réelle du type
        detected_mime, ext = detect_mime_from_magic(binary)

        # 3. Vérifier que le type détecté est autorisé
        if detected_mime not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"Type de fichier non autorisé : {detected_mime}")

        # 4. Optionnel : vérifier la cohérence avec le type déclaré (si fourni)
        if declared_mime and declared_mime != detected_mime:
            # On peut être strict ou seulement logger, ici on refuse par sécurité
            raise ValidationError(
                f"Le type déclaré ({declared_mime}) ne correspond pas au type réel ({detected_mime})"
            )

        # 5. Aiguiller vers le handler approprié
        if detected_mime.startswith("image/"):
            # Les kwargs (max_dimensions, quality) ne sont passés qu'au handler image
            return self.image_handler.handle(binary, filename_prefix, **kwargs)
        else:
            # Pour les documents, on passe aussi le type détecté (utile pour l'extension et le scan ZIP)
            return self.document_handler.handle(binary, filename_prefix, original_mime=detected_mime)