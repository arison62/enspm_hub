# opportunities/utils/get_similar_opportunities.py
from uuid import UUID
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

def get_similar_opportunities(
    model_class: type[models.Model],
    opportunity_id: UUID,
    limit: int = 5
    ):
    """
    Recherche des entités similaires en utilisant le titre et la description.
    """
    try:
        # 1. Récupération de l'entité source
        # On récupère spécifiquement titre et description_text
        source = model_class.objects.get(pk=opportunity_id, deleted=False)
        
        # 2. Construction de la requête de recherche globale
        # On concatène les deux pour que PostgreSQL cherche des correspondances sur les deux
        # On utilise 'french' pour gérer le stemming (racines des mots)
        search_terms = f"{source.titre} {source.description_text or ''}" # type: ignore
        query = SearchQuery(search_terms, config='simple')

        # 3. Exécution de la recherche sur le vecteur pondéré
        similar_items = (
            model_class.objects
            .filter(deleted=False, statut='active') # Uniquement les offres visibles
            .exclude(pk=opportunity_id)                   # Exclure l'offre actuelle
            .annotate(
                
                rank=SearchRank(F('search_vector'), query)
            )
            .filter(rank__gt=0.01)                   # Seuil de pertinence
            .order_by('-rank', '-date_publication')  # Plus pertinent, puis plus récent
        )[:limit]

        logger.info(
            f"Similarity search successful for {model_class.__name__} {opportunity_id}",
            extra={'count': len(similar_items)}
        )
        
        return similar_items

    except model_class.DoesNotExist:
        logger.warning(f"Similarity search: {model_class.__name__} {opportunity_id} not found.")
        return []
    except Exception as e:
        logger.error(f"DiscoveryService Error: {str(e)}", exc_info=True)
        return []