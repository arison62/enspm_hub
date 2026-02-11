"""
Système EventBus pour la gestion centralisée des événements
"""
import logging
from typing import Dict, List, Callable, Any, Optional
from threading import Lock
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Classe de base pour tous les événements"""
    # timestamp: Optional[datetime] = field(default_factory=lambda: None)
    
    def __post_init__(self):
        if self.timestamp is None:
            from django.utils import timezone
            self.timestamp = timezone.now()


class EventBus:
    """
    Singleton EventBus pour publier et souscrire aux événements.
    Pattern Publisher-Subscriber pour découpler les composants.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers: Dict[str, List[Callable]] = {}
                    cls._instance._initialized = True
        return cls._instance
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Souscrit à un type d'événement.
        
        Args:
            event_type: Type d'événement (ex: 'message.groupe.created')
            callback: Fonction à appeler quand l'événement est publié
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscriber registered for event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Désinscrit un callback d'un type d'événement.
        
        Args:
            event_type: Type d'événement
            callback: Fonction à désinscrire
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Subscriber unregistered for event: {event_type}")
    
    def publish(self, event_type: str, event: Event) -> None:
        """
        Publie un événement à tous les souscripteurs.
        
        Args:
            event_type: Type d'événement (ex: 'message.groupe.created')
            event: Instance de l'événement
        """
        logger.info(f"Publishing event: {event_type}")
        
        if event_type not in self._subscribers:
            logger.debug(f"No subscribers for event: {event_type}")
            return
        
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in event subscriber for {event_type}: {str(e)}",
                    exc_info=True
                )
    
    def clear_all(self) -> None:
        """Nettoie tous les souscripteurs (utile pour les tests)"""
        self._subscribers.clear()
        logger.debug("All event subscribers cleared")
    
    def get_subscribers_count(self, event_type: str = None) -> int:
        """Retourne le nombre de souscripteurs pour un type d'événement"""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())


# Instance globale singleton
event_bus = EventBus()