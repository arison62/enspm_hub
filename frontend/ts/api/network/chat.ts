import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PaginationState } from "@tanstack/react-table";
import type { AxiosError } from "axios";
import { v4 as uuidv4 } from "uuid";
import axios from "@/lib/axios";

import type {
  ConversationListResponse,
  Conversation,
  MessageListResponse,
  Message,
  MessageCreateIn,
} from "@/types/network";

export const chatKeys = {
  all: ['chat'] as const,
  conversations: () => [...chatKeys.all, 'conversations'] as const,
  messages: (conversationId: string) => [...chatKeys.all, 'messages', conversationId] as const,
  stats: () => [...chatKeys.all, 'stats'] as const,
};

/* ============================================================
   CONVERSATIONS
   ============================================================ */

export const useGetConversations = ({
  pagination,
}: {
  pagination: PaginationState;
}) =>
  useQuery<ConversationListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: [...chatKeys.conversations(), pagination.pageIndex, pagination.pageSize],
    queryFn: async () => {
      const res = await axios.get("/network/chat/conversations/", {
        params: {
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

export const useInitDM = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profilId: string) =>
      axios.post<Conversation>(`/network/chat/direct/init/${profilId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
  });
};

/* ============================================================
   MESSAGES
   ============================================================ */

export const useGetMessages = ({
  conversationId,
  pagination,
}: {
  conversationId: string | null;
  pagination: PaginationState;
}) =>
  useQuery<MessageListResponse, AxiosError>({
    enabled: !!conversationId,
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: [...chatKeys.messages(conversationId || ""), pagination.pageIndex],
    queryFn: async () => {
      const res = await axios.get(
        `/network/chat/conversations/${conversationId}/messages/`,
        {
          params: {
            page: pagination.pageIndex + 1,
            page_size: pagination.pageSize,
          },
        },
      );
      return res.data;
    },
  });

export const useSendMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ conversationId, data }: { conversationId: string; data: MessageCreateIn }) => {
      const clientId = data.client_id || uuidv4();
      const res = await axios.post<Message>(
        `/network/chat/conversations/${conversationId}/messages/`,
        { ...data, client_id: clientId }
      );
      return res.data;
    },

    onMutate: async ({ conversationId, data }) => {
      // Annuler les refetches en cours pour ne pas écraser l'optimistic update
      await queryClient.cancelQueries({ queryKey: chatKeys.messages(conversationId) });

      // Snapshot de l'état précédent
      const previousMessages = queryClient.getQueryData<MessageListResponse>(chatKeys.messages(conversationId));

      // Création du message optimiste
      const clientId = data.client_id || uuidv4();
      const optimisticMessage: Message = {
        id: clientId, // ID temporaire
        client_id: clientId,
        type: 'user',
        conversation_id: conversationId,
        contenu: data.contenu,
        nombre_reponses: 0,
        est_lu_par_moi: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        // Note: L'expéditeur devrait être ajouté ici idéalement via le hook useAuth
      };

      // Mise à jour du cache
      if (previousMessages) {
        queryClient.setQueryData<MessageListResponse>(chatKeys.messages(conversationId), {
          ...previousMessages,
          items: [...previousMessages.items, optimisticMessage],
          meta: { ...previousMessages.meta, total_items: previousMessages.meta.total_items + 1 }
        });
      }

      return { previousMessages };
    },

    onError: (err, variables, context) => {
      // Rollback en cas d'erreur
      if (context?.previousMessages) {
        queryClient.setQueryData(chatKeys.messages(variables.conversationId), context.previousMessages);
      }
    },

    onSettled: (data, error, variables) => {
      // Invalidation finale pour synchronisation
      queryClient.invalidateQueries({ queryKey: chatKeys.messages(variables.conversationId) });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    }
  });
};

export const useMarkConversationRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: string) =>
      axios.post(`/network/chat/conversations/${conversationId}/lu/`),
    onSuccess: (_, conversationId) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.messages(conversationId) });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
      queryClient.invalidateQueries({ queryKey: chatKeys.stats() });
    },
  });
};

/* ============================================================
   STATS
   ============================================================ */

export const useGetChatStats = () =>
  useQuery({
    queryKey: chatKeys.stats(),
    queryFn: async () => {
      const res = await axios.get("/network/chat/stats/");
      return res.data;
    },
  });
