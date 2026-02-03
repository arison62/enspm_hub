from typing import Optional
from nanoid import generate
from django.utils.text import slugify

EXCLUDED_SLUGS = [
    'admin',
    'django-admin',
]

def generate_unique_slug(base_slug: str, model_class, max_attempts=5) -> Optional[str]:
    """
    Génère un slug unique avec un nombre max de tentatives.
    """
    base_slug = slugify(base_slug)
    if base_slug in EXCLUDED_SLUGS:
        raise ValueError("Le slug de base est exclu de la liste des slugs exclus.")
    
    
    # D'abord verifier si le slug de base est disponible
    if not model_class.objects.filter(slug=base_slug).exists():
        return base_slug
    
    # Sinon ajouter un suffixe unique
    for attempt in range(max_attempts):
        suffix = generate(size=6, alphabet='0123456789abcdefghijklmnopqrst')
        slug = slugify(f"{base_slug}-{suffix}")
        
        if not model_class.objects.filter(slug=slug).exists():
            return slug
        
    return None