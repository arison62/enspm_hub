// frontend/ts/contexts/websocket-provider.tsx
import { useEffect } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocketMessage } from "@/hooks/use-websocket";
import { useAuth } from "@/hooks/use-auth";
import { chatKeys } from "@/api/network/chat";
import type {
  Message,
  MessageListResponse,
  ConversationListResponse,
} from "@/types/network";

export const WebSocketProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { connect, disconnect, status, error } = useWebSocket();
  const { isAuthenticated, profil } = useAuth();
  const profilId = profil?.id;
  const queryClient = useQueryClient();

  useEffect(() => {
    if (isAuthenticated) connect();
    return () => disconnect();
  }, [connect, disconnect, isAuthenticated]);

  useWebSocketMessage("chat.message", (event) => {
    const { event_type, payload } = event;
    const { conversation_id, data } = payload;
    if (!conversation_id) return;

    const baseKey = chatKeys.messages(conversation_id);

    if (event_type === "MessageEnvoye") {
      const newMessage = data as Message;
      const isOwn = newMessage.expediteur?.id === profilId;
      const clientId = newMessage.client_id;

      // Récupère toutes les pages en cache
      const currentQueries = queryClient.getQueriesData<MessageListResponse>({
        queryKey: baseKey,
        exact: false,
      });

      // Page la plus récente = celle avec le plus petit pageIndex (page 0 = dernières messages)
      const pageIndices = currentQueries.map(([key]) =>
        Number(key.at(-1) ?? 0),
      );
      const targetPageIndex =
        pageIndices.length > 0 ? Math.min(...pageIndices) : 0;

      // 1. Remplacement du message optimiste (sur TOUTES les pages)
      queryClient.setQueriesData<MessageListResponse>(
        { queryKey: baseKey, exact: false },
        (old) => {
          if (!old?.items) return old;
          const exists = old.items.some(
            (m) =>
              m.id === newMessage.id || (clientId && m.client_id === clientId),
          );
          if (exists) {
            return {
              ...old,
              items: old.items.map((m) =>
                m.id === newMessage.id || (clientId && m.client_id === clientId)
                  ? newMessage
                  : m,
              ),
            };
          }
          return old;
        },
      );

      // 2. Ajout du nouveau message UNIQUEMENT sur la page la plus récente (si ce n'est pas déjà présent)
      if (!isOwn || !clientId) {
        // message d'un autre utilisateur → on l'ajoute
        const targetKey = [...baseKey, targetPageIndex];
        queryClient.setQueryData<MessageListResponse>(targetKey, (old) => {
          if (!old?.items) return old;

          const alreadyThere = old.items.some(
            (m) =>
              m.id === newMessage.id || (clientId && m.client_id === clientId),
          );
          if (alreadyThere) return old;

          return {
            ...old,
            items: [...old.items, newMessage],
            meta: {
              ...old.meta,
              total_items: old.meta.total_items + 1,
            },
          };
        });
      }

      // Mise à jour de la liste des conversations (inchangée, très peu coûteuse)
      queryClient.setQueriesData<ConversationListResponse>(
        { queryKey: chatKeys.conversations() },
        (old) => {
          if (!old) return old;
          const convIndex = old.items.findIndex(
            (c) => c.id === conversation_id,
          );
          if (convIndex === -1) return old;

          const isOwnMsg = newMessage.expediteur?.id === profilId;
          const updatedConv = {
            ...old.items[convIndex],
            messages_non_lus: isOwnMsg
              ? old.items[convIndex].messages_non_lus
              : old.items[convIndex].messages_non_lus + 1,
            dernier_message: newMessage,
            updated_at: newMessage.created_at,
          };

          const newItems = [...old.items];
          newItems.splice(convIndex, 1);
          newItems.unshift(updatedConv);
          return { ...old, items: newItems };
        },
      );
    }

    if (event_type === "MessageSupprime") {
      const messageId = payload.message_id;

      if (!messageId) return;

      queryClient.setQueriesData<MessageListResponse>(
        { queryKey: baseKey, exact: false },
        (old) => {
          if (!old?.items) return old;
          const newItems = old.items.filter((m) => m.id !== messageId);
          return {
            ...old,
            items: newItems,
            meta: {
              ...old.meta,
              total_items: Math.max(0, old.meta.total_items - 1),
            },
          };
        },
      );

      // Conversations : on invalide seulement la liste (très léger)
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    }

    if (event_type === "MessageLu") {
      // Marque tout lu dans le cache (performant)
      queryClient.setQueriesData<MessageListResponse>(
        { queryKey: baseKey, exact: false },
        (old) => {
          if (!old?.items) return old;
          return {
            ...old,
            items: old.items.map((m) => ({ ...m, est_lu_par_moi: true })),
          };
        },
      );

      // Unread = 0 dans les conversations
      queryClient.setQueriesData<ConversationListResponse>(
        { queryKey: chatKeys.conversations() },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((c) =>
              c.id === conversation_id ? { ...c, messages_non_lus: 0 } : c,
            ),
          };
        },
      );
    }

    if (event_type === "ConversationCreee") {
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    }
  });

  // Logs de debug (optionnel)
  useEffect(() => {
    if (error) console.error("[WebSocket] Error:", error);
    if (status === "connected") console.log("[WebSocket] Connected");
  }, [error, status]);

  return <>{children}</>;
};
