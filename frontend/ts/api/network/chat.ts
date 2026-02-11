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
  WebSocketEvent
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
    // Note: Optimistic UI logic would go here in onMutate
    onSuccess: (newMessage, variables) => {
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
