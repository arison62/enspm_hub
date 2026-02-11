from .base import BaseEvent
from .event_bus import event_bus, EventBus
from .groupe_events import GroupeEvents
from .chat_events import ChatEvents

# For backward compatibility if needed, though we are refactoring everything
# We can define EventTypes class here if wanted, or just use the event_type string directly.

class EventTypes:
    # Messages
    MESSAGE_ENVOYE = 'MessageEnvoye'
    MESSAGE_LU = 'MessageLu'
    MESSAGE_MODIFIE = 'MessageModifie'
    MESSAGE_SUPPRIME = 'MessageSupprime'
    UTILISATEUR_TAPE = 'UtilisateurTape'
    
    # Groupes
    UTILISATEUR_AJOUTE = 'UtilisateurAjouteAuGroupe'
    UTILISATEUR_RETIRE = 'UtilisateurRetireDuGroupe'
    UTILISATEUR_A_REJOINT = 'UtilisateurARejointLeGroupe'
    UTILISATEUR_A_QUITTE = 'UtilisateurAQuitteLeGroupe'
    GROUPE_CREE = 'GroupeCree'
    GROUPE_MODIFIE = 'GroupeModifie'
    GROUPE_FERME = 'GroupeFerme'
    GROUPE_DESACTIVE = 'GroupeDesactive'
    GROUPE_REACTIVE = 'GroupeReactive'
    ROLE_MODIFIE = 'RoleUtilisateurModifie'
