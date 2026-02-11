import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  PaginationState,
} from "@tanstack/react-table";
import type { AxiosError } from "axios";

import axios from "@/lib/axios";

import type {
  MessageListResponse,
  MessageGroupeCreate,
  MessageDMOut,
  MessageDMCreate,
  ConversationOut,
  ConversationRecentOut,
  StatsMessagesOut,
  ConversationListResponse,
} from "@/types/network";

export const useGetGroupMessages = ({
  groupId,
  pagination,
}: {
  groupId: string | null;
  pagination: PaginationState;
}) =>
  useQuery<MessageListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["groupMessages", groupId, pagination.pageIndex],
    queryFn: async () => {
      if (!groupId) throw new Error("Group ID is required");
      const res = await axios.get(
        `/network/chat/groupes/${groupId}/messages/`,
        {
          params: {
            page: pagination.pageIndex + 1,
            page_size: pagination.pageSize,
          },
        },
      );
      return res.data;
    },
    enabled: !!groupId,
    refetchInterval: 5000,
  });

/* =========================
   MESSAGES DIRECTS & CONVERSATIONS
   ========================= */

export const useInitConversation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profilId: string) =>
      axios.post<ConversationOut>(`/network/chat/direct/init/${profilId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recentConversations"] });
    },
  });
};

export const useGetConversationMessages = ({
  conversationId,
  page = 1,
  page_size = 50,
}: {
  conversationId: string | null;
  page?: number;
  page_size?: number;
}) =>
  useQuery<{ items: MessageDMOut[] }, AxiosError>({
    queryKey: ["conversationMessages", conversationId, page, page_size],
    queryFn: async () => {
      if (!conversationId) throw new Error("Conversation ID is required");
      const res = await axios.get(
        `/network/chat/direct/${conversationId}/messages/`,
        {
          params: { page, page_size },
        },
      );
      return res.data;
    },
    enabled: !!conversationId,
    refetchInterval: 3000,
  });

export const useGetRecentConversation = (conversationId: string) =>
  useQuery<ConversationRecentOut, AxiosError>({
    queryKey: ["convesation", conversationId],
    queryFn: async () => {
      const res = await axios.get(
        `/network/chat/direct/conversations/${conversationId}/`,
      );
      return res.data;
    },
  });

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
    queryKey: ["conversations", pagination.pageIndex],
    queryFn: async () => {
      const res = await axios.get("/network/chat/direct/conversations/", {
        params: {
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

/* =========================
   STATISTIQUES
   ========================= */

export const useGetMessageStats = () =>
  useQuery<StatsMessagesOut, AxiosError>({
    queryKey: ["messageStats"],
    queryFn: async () => {
      const res = await axios.get("/network/chat/stats/messages/");
      return res.data;
    },
  });


  /* =========================
     MESSAGES
     ========================= */
  
  export const useGroupMessageActions = () => {
    const queryClient = useQueryClient();
  
    const sendGroupMessage = useMutation({
      mutationFn: (data: { groupId: string } & MessageGroupeCreate) =>
        axios.post(`/network/chat/groupes/${data.groupId}/messages/`, data),
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["groupMessages", variables.groupId],
        });
      },
    });
  
    const markGroupMessageAsRead = useMutation({
      mutationFn: (messageId: string) =>
        axios.post(`/network/chat/messages/${messageId}/lu/`),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["groupMessages"] });
      },
    });
  
    return { sendGroupMessage, markGroupMessageAsRead };
  };
  
  export const useDirectMessageActions = () => {
    const queryClient = useQueryClient();
  
    const sendDMMessage = useMutation({
      mutationFn: (data: { conversationId: string } & MessageDMCreate) =>
        axios.post(`/network/chat/direct/${data.conversationId}/messages/`, {
          contenu: data.contenu,
          piece_jointe_base64: data.piece_jointe_base64,
        }),
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries({
          queryKey: ["conversationMessages", variables.conversationId],
        });
        queryClient.invalidateQueries({ queryKey: ["conversations", variables.conversationId] });
      },
    });
  
    const markConversationAsRead = useMutation({
      mutationFn: (conversationId: string) =>
        axios.post(`/network/chat/direct/${conversationId}/lu/`),
      onSuccess: (_, conversationId) => {
        queryClient.invalidateQueries({
          queryKey: ["conversationMessages", conversationId],
        });
        queryClient.invalidateQueries({ queryKey: ["recentConversations"] });
        queryClient.invalidateQueries({ queryKey: ["messageStats"] });
      },
    });
  
    return { sendDMMessage, markConversationAsRead };
  };
  