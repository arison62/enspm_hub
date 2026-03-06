# core/mixins.py
from abc import abstractmethod
from datetime import datetime
from typing import Optional

from ninja import Schema

class ChatReferenceable:
    """
    Mixin a implementer sur tout les modele pouvant etre reference
    dans un message de chat
    """
    REFERENCE_TYPE : str # ex: "post", "comment", "message"
    
    @abstractmethod
    def get_chat_preview(self) -> dict:
        """
        Retourne un apercu standardise pour l'affichage dans le chat
        Toutes les cles sont optionnelles sauf l`id` et le `type`
        """
        raise NotImplementedError
    
    # Exemple de structure attendue:
    # {
    #     "id": str(self.pk),
    #     "type": self.REFERENCE_TYPE,
    #     "titre": "...",
    #     "sous_titre": "...",
    #     "apercu": "...",                  # extrait du contenu
    #     "url": "...",                     # lien de navigation
    #     "media_url": "...",
    #     "media_type": "...",
    #     "media_name": "...",
    #     "created_at": "...",
    #     "updated_at": "..."
    # }
    
class ReferencePreviewOut(Schema):
    id: str
    type: str
    titre: Optional[str]=None
    sous_titre: Optional[str]=None
    apercu: Optional[str]=None
    url: Optional[str]=None
    media_url: Optional[str]=None
    media_type: Optional[str]=None
    media_name: Optional[str]=None
    created_at: Optional[datetime]=None
    updated_at: Optional[datetime]=None
