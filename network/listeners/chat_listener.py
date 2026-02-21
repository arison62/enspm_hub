import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from network.events import event_bus, BaseEvent

logger = logging.getLogger(__name__)

class ChatEventListener:
    """
    Écoute les événements de l'EventBus et les diffuse sur le Channel Layer (WebSockets).
    """

    @staticmethod
    def register_handlers():
        event_types = [
            'MessageEnvoye', 'MessageLu', 'MessageModifie', 'MessageSupprime', 'UtilisateurTape',
            'UtilisateurAjouteAuGroupe', 'UtilisateurRetireDuGroupe', 'UtilisateurARejointLeGroupe',
            'UtilisateurAQuitteLeGroupe', 'GroupeCree', 'GroupeModifie', 'GroupeFerme',
            'GroupeDesactive', 'GroupeReactive', 'RoleUtilisateurModifie', 'ConversationCreee'
        ]

        for et in event_types:
            event_bus.subscribe(et, ChatEventListener.handle_event)

        logger.info("Chat event handlers registered")

    @staticmethod
    def handle_event(event: BaseEvent):
        """Diffuser l'événement vers les bons groupes Channel Layer"""
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        payload = event.payload
        target_groups = []

        room_id = payload.get('room_id')

        if room_id:
            target_groups.append(f"conv_{room_id}")
            
        # 2. Événements utilisateur (notifications directes)
        if 'profil_id' in payload:
            target_groups.append(f"user_{payload['profil_id']}")

        # Cas spéciaux pour rejoindre des rooms en temps réel
        if event.event_type == 'UtilisateurAjouteAuGroupe':
            async_to_sync(channel_layer.group_send)(
                f"user_{payload['profil_id']}",
                {
                    "type": "join.room",
                    "room_name": f"conv_{payload['conversation_id']}"
                }
            )

        if event.event_type == 'ConversationCreee':
            # Notifier tous les participants de rejoindre la nouvelle room de conversation
            participants = payload.get('data', {}).get('participants', [])
            for p in participants:
                async_to_sync(channel_layer.group_send)(
                    f"user_{p['id']}",
                    {
                        "type": "join.room",
                        
                        "room_name": f"conv_{payload['conversation_id']}"
                    }
                )

        # Envoi au Channel Layer
        for group_name in set(target_groups):
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "chat.message",
                    "event_type": event.event_type,
                    "payload": payload,
                    "timestamp": event.timestamp.isoformat()
                }
            )
