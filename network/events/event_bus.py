import logging
from typing import List, Callable, Dict
from .base import BaseEvent

logger = logging.getLogger(__name__)

class EventBus:
    _instance = None
    _subscribers: Dict[str, List[Callable]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def subscribe(cls, event_type: str, handler: Callable[[BaseEvent], None]):
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}")
    
    @classmethod
    def unsubscribe(cls, event_type: str, handler: Callable[[BaseEvent], None]):
        if event_type in cls._subscribers:
            if handler in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from {event_type}")

    @classmethod
    def publish(cls, event: BaseEvent):
        handlers = cls._subscribers.get(event.event_type, [])
        logger.info(f"Publishing event {event.event_type} to {len(handlers)} handlers")
        for handler in handlers:
            try:
                
                handler(event)
            except Exception as e:
                logger.error(f"Erreur handler {event.event_type}: {e}", exc_info=True)
    
    @classmethod
    def publish_async(cls, event: BaseEvent):
        """Pour utilisation avec Celery ou Huey si nécessaire"""
        # Pour l'instant on reste en synchrone ou on délègue à une tâche
        cls.publish(event)

# Instance globale
event_bus = EventBus()
