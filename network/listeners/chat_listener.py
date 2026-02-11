import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from network.events import event_bus, BaseEvent

logger = logging.getLogger(__name__)

class ChatEventListener:
    """
    Écoute les événements de l'EventBus et les diffuse sur le Channel Layer (WebSockets).
    C'est le pont entre la logique métier (Services) et le temps réel.
    """

    @staticmethod
    def register_handlers():
        # S'abonner à TOUS les types d'événements ou à une liste spécifique
        # Pour faire simple on peut utiliser une liste de types d'événements
        event_types = [
            'MessageEnvoye', 'MessageLu', 'MessageModifie', 'MessageSupprime', 'UtilisateurTape',
            'UtilisateurAjouteAuGroupe', 'UtilisateurRetireDuGroupe', 'UtilisateurARejointLeGroupe',
            'UtilisateurAQuitteLeGroupe', 'GroupeCree', 'GroupeModifie', 'GroupeFerme',
            'GroupeDesactive', 'GroupeReactive', 'RoleUtilisateurModifie'
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

        payload_dict = event.to_dict()

        target_groups = []

        # 1. Routage basé sur le type d'événement et le payload
        if event.event_type in ['MessageEnvoye', 'MessageLu', 'MessageModifie', 'MessageSupprime', 'UtilisateurTape']:
            # Ces événements concernent une conversation (DM ou Groupe)
            conv_id = event.payload.get('conversation_id')
            if conv_id:
                # On diffuse à la conversation. Le Consumer s'occupe de savoir s'il est DM ou Groupe ?
                # Pour respecter la consigne : conv_<uuid> pour DM, groupe_<id> pour groupe.
                # Il nous faut savoir si c'est un groupe.
                from network.models.chat import Conversation, ConversationType
                try:
                    conv = Conversation.objects.select_related('groupe').get(id=conv_id)
                    if conv.type == ConversationType.GROUP and conv.groupe:
                        target_groups.append(f"groupe_{conv.groupe.id}")
                    else:
                        target_groups.append(f"conv_{conv.id}")
                except Exception:
                    target_groups.append(f"conv_{conv_id}")

        # 2. Événements de groupe
        if event.event_type.startswith('Groupe') or 'groupe_id' in event.payload:
            gid = event.payload.get('groupe_id') or event.aggregate_id
            if gid:
                target_groups.append(f"groupe_{gid}")

        # 3. Événements utilisateur (notifications)
        if 'profil_id' in event.payload:
            target_groups.append(f"user_{event.payload['profil_id']}")

        # Cas spéciaux pour rejoindre des rooms en temps réel
        if event.event_type == 'UtilisateurAjouteAuGroupe':
            # Notifier l'utilisateur de rejoindre la nouvelle room
            async_to_sync(channel_layer.group_send)(
                f"user_{event.payload['profil_id']}",
                {
                    "type": "join_room",
                    "room_name": f"groupe_{event.payload['groupe_id']}"
                }
            )

        if event.event_type == 'ConversationCreee':
            # Notifier tous les participants de rejoindre la nouvelle room de conversation
            participants = event.payload.get('data', {}).get('participants', [])
            for p in participants:
                async_to_sync(channel_layer.group_send)(
                    f"user_{p['id']}",
                    {
                        "type": "join_room",
                        "room_name": f"conv_{event.payload['conversation_id']}"
                    }
                )

        # Envoi au Channel Layer
        for group_name in set(target_groups):
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "chat.message",  # Correspond à la méthode chat_message du Consumer
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "timestamp": payload['timestamp']
                }
            )
