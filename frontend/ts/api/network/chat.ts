import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PaginationState } from "@tanstack/react-table";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";

import type {
  ConversationListResponse,
  Conversation,
  MessageListResponse,
  Message,
  MessageCreateIn,
} from "@/types/network";
import { useAuth } from "@/hooks/use-auth";
import { v4 as uuidv4 } from "uuid";
import { router } from "@inertiajs/react";
import type { ReferencePreviewOut } from "@/types/base";

export const chatKeys = {
  all: ["chat"] as const,
  conversations: (type?: string) =>
    [...chatKeys.all, "conversations", type] as const,
  messages: (conversationId: string) =>
    [...chatKeys.all, "messages", conversationId] as const,
  stats: () => [...chatKeys.all, "stats"] as const,
};

/* ============================================================
   CONVERSATIONS
   ============================================================ */

export const useGetConversations = ({
  pagination,
  type,
  query,
}: {
  pagination: PaginationState;
  type?: "dm" | "group";
  query: string | null;
}) =>
  useQuery<ConversationListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: [
      ...chatKeys.conversations(type),
      query,
      pagination.pageIndex,
      pagination.pageSize,
    ],
    queryFn: async () => {
      const res = await axios.get("/network/chat/conversations/", {
        params: {
          type,
          query,
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

export const useGetConversation = (conversationId: string | null) =>
  useQuery<Conversation, AxiosError>({
    enabled: !!conversationId,
    queryKey: chatKeys.conversations(),
    queryFn: async () => {
      const res = await axios.get(
        `/network/chat/conversations/${conversationId}/`,
      );
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

export const useInitReplyReference = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      profilId: string;
      referenceId: string;
      referenceType: string;
    }) => {
      const { profilId } = data;
      return axios.post<Conversation>(`/network/chat/direct/init/${profilId}/`);
    },
    onSuccess: (data, variables) => {
      const convId = data.data.id;
      const { referenceId, referenceType} = variables;
      router.visit(
        `/chat?dm=${convId}&ref=${referenceId}&type=${referenceType}`,
      );
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
    queryKey: [
      ...chatKeys.messages(conversationId || ""),
      pagination.pageIndex,
    ],
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

export const useGetReferencePreview = ({
  referenceId,
  referenceType,
  enabled,
}: {
  referenceId: string;
  referenceType: string;
  enabled: boolean;
}) => {
  return useQuery<ReferencePreviewOut, AxiosError>({
    queryKey: [referenceType, referenceId],
    queryFn: async () => {
      const res = await axios.get(
        `/network/chat/messages/preview/${referenceType}/${referenceId}/`,
      );
      return res.data;
    },
    enabled,
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();
  const { profil } = useAuth();

  return useMutation({
    mutationFn: async ({
      conversationId,
      data,
    }: {
      conversationId: string;
      data: MessageCreateIn;
    }) => {
      const res = await axios.post<Message>(
        `/network/chat/conversations/${conversationId}/messages/`,
        { ...data },
      );
      return res.data;
    },

    onMutate: async ({ conversationId, data }) => {
      const baseKey = chatKeys.messages(conversationId);

      // Annule tous les refetches en cours (toutes les pages)
      await queryClient.cancelQueries({
        queryKey: baseKey,
        exact: false,
      });

      // Snapshot de toutes les pages en cache
      const previousQueries = queryClient.getQueriesData<MessageListResponse>({
        queryKey: baseKey,
        exact: false,
      });

      const clientId = data.client_id;
      const replyId = data.reference_id;
      let replyMsg = undefined;
      previousQueries.forEach(([, data]) => {
        if (data !== undefined) {
          if (replyId && data.items.find((msg) => msg.id === replyId)) {
            replyMsg = data.items.find((msg) => msg.id === replyId);
          }
        }
      });

      // Message optimiste
      const optimisticMessage: Message = {
        id: clientId || uuidv4(),
        client_id: clientId,
        type: "user",
        conversation_id: conversationId,
        contenu: data.contenu,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reference: replyMsg,
        conversation_type: "dm",
        expediteur: profil
          ? {
              id: profil?.id,
              nom_complet: profil?.nom_complet,
              slug: profil?.slug,
              is_online: false,
              photo_url: profil?.photo_profil || "",
            }
          : undefined,
      };
      console.log("Optimistic message:", optimisticMessage);
      // === AJOUT UNIQUEMENT SUR LA DERNIÈRE PAGE CHARGÉE ===
      let maxPageIndex = 0;
      if (previousQueries.length > 0) {
        maxPageIndex = Math.max(
          ...previousQueries.map(([key]) => Number(key.at(-1) ?? 0)),
        );
      }

      // Cas rare : aucune page en cache → on crée la page 0
      if (previousQueries.length === 0) {
        const page0Key = [...baseKey, 0] as const;
        queryClient.setQueryData<MessageListResponse>(page0Key, {
          items: [optimisticMessage],
          meta: {
            page: 0,
            page_size: 10,
            total_items: 1,
            total_pages: 1,
          },
        });
      } else {
        // Mise à jour uniquement de la dernière page
        previousQueries.forEach(([queryKey, previousData]) => {
          const thisPage = Number(queryKey.at(-1) ?? 0);
          if (thisPage !== maxPageIndex || !previousData?.items) return;

          queryClient.setQueryData<MessageListResponse>(queryKey, {
            ...previousData,
            items: [...previousData.items, optimisticMessage],
            meta: {
              ...previousData.meta,
              total_items: previousData.meta.total_items + 1,
            },
          });
        });
      }

      return { previousQueries, clientId };
    },

    onError: (_err, _variables, context) => {
      // Rollback complet sur toutes les pages
      if (context?.previousQueries) {
        context.previousQueries.forEach(([queryKey, previousData]) => {
          if (previousData !== undefined) {
            queryClient.setQueryData(queryKey, previousData);
          }
        });
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
      queryClient.invalidateQueries({ queryKey: chatKeys.stats() });
    },
  });
};

export const useMarkConversationRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: string) =>
      axios.post(`/network/chat/conversations/${conversationId}/lu/`),
    onSuccess: (_, conversationId) => {
      queryClient.invalidateQueries({
        queryKey: chatKeys.messages(conversationId),
      });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
      queryClient.invalidateQueries({ queryKey: chatKeys.stats() });
    },
  });
};

export const useDeleteMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ messageId, conversationId }) =>
      axios.delete(
        `/network/chat/conversations/${conversationId}/messages/${messageId}/`,
      ),

    onMutate: async ({
      messageId,
      conversationId,
    }: {
      messageId: string;
      conversationId: string;
    }) => {
      const baseKey = chatKeys.messages(conversationId);

      await queryClient.cancelQueries({ queryKey: baseKey, exact: false });

      const previousQueries = queryClient.getQueriesData<MessageListResponse>({
        queryKey: baseKey,
        exact: false,
      });

      queryClient.setQueriesData<MessageListResponse>(
        { queryKey: baseKey, exact: false },
        (old) => {
          if (!old?.items) return old;
          const newItems = old.items.filter((msg) => msg.id !== messageId);
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

      return { previousQueries };
    },

    onError: (_, __, context) => {
      context?.previousQueries?.forEach(([key, data]) => {
        if (data !== undefined) queryClient.setQueryData(key, data);
      });
    },

    onSettled: () => {
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
