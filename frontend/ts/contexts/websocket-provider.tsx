// frontend/ts/contexts/websocket-provider.tsx

import { useEffect } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocketMessage } from "@/hooks/use-websocket";
import { useAuth } from "@/hooks/use-auth";
import { chatKeys } from "@/api/network/chat";
import { Message, MessageListResponse, ConversationListResponse, Conversation } from "@/types/network";

export const WebSocketProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { connect, disconnect, status, error } = useWebSocket();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [connect, disconnect, isAuthenticated]);

  useWebSocketMessage("chat.message", (event) => {
    const { event_type, payload } = event;
    const { conversation_id, data } = payload;

    console.log(`[WebSocket] Event ${event_type} received for conv ${conversation_id}`);

    if (event_type === 'MessageEnvoye') {
      const newMessage = data as Message;

      // 1. Mettre à jour la liste des messages de la conversation
      queryClient.setQueriesData<MessageListResponse>(
        { queryKey: chatKeys.messages(conversation_id) },
        (old) => {
          if (!old) return old;

          // Éviter les doublons (si le message optimiste est déjà là ou si on a reçu l'event deux fois)
          const exists = old.items.some(m => m.id === newMessage.id || (m.client_id && m.client_id === newMessage.client_id));
          if (exists) {
            // Remplacer le message optimiste (qui a le même client_id) par le vrai message du serveur
            return {
              ...old,
              items: old.items.map(m => (m.client_id && m.client_id === newMessage.client_id) ? newMessage : m)
            };
          }

          return {
            ...old,
            items: [...old.items, newMessage],
            meta: { ...old.meta, total_items: old.meta.total_items + 1 }
          };
        }
      );

      // 2. Mettre à jour la liste des conversations
      queryClient.setQueriesData<ConversationListResponse>(
        { queryKey: chatKeys.conversations() },
        (old) => {
          if (!old) return old;

          const convIndex = old.items.findIndex(c => c.id === conversation_id);
          if (convIndex === -1) {
            // Si la conversation n'est pas dans la liste, on invalide pour la récupérer
            queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
            return old;
          }

          const updatedConv = {
            ...old.items[convIndex],
            dernier_message: newMessage,
            updated_at: newMessage.created_at,
            // On pourrait incrémenter messages_non_lus si ce n'est pas nous l'expéditeur
          };

          // On remonte la conversation en haut de liste
          const newItems = [...old.items];
          newItems.splice(convIndex, 1);
          newItems.unshift(updatedConv);

          return { ...old, items: newItems };
        }
      );
    }

    if (event_type === 'MessageLu') {
      // Mettre à jour le statut de lecture dans le cache si nécessaire
      // Pour l'instant on peut invalider ou faire une mise à jour précise
      queryClient.invalidateQueries({ queryKey: chatKeys.messages(conversation_id) });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    }

    if (event_type === 'ConversationCreee') {
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    }
  });

  useEffect(() => {
    if (error) {
      console.error("[WebSocket] Error: ", error);
    }
  }, [error]);

  useEffect(() => {
    if (status === "connected") {
      console.log("[WebSocket] Connected to server");
    }
  }, [status]);

  return <>{children}</>;
};
