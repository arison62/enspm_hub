/**
 * React Query hooks for Chat API
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";
import type { AxiosError } from "axios";

import axios from "@/lib/axios";

import type {
  GroupListResponse,
  GroupCreate,
  GroupUpdate,
  DemandeAccesListResponse,
  DemandeAccesGroupeCreate,
  MessageListResponse,
  MessageGroupeCreate,
  MessageDMOut,
  MessageDMCreate,
  ConversationOut,
  ConversationRecentOut,
  StatsMessagesOut,
  MembreGroupeListResponse,
} from "@/types/network";

/* ============================================================
   QUERY HOOKS
   ============================================================ */

/* =========================
   GROUPES
   ========================= */

export const useGetGroups = ({
  columnFilters,
  pagination,
}: {
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) =>
  useQuery<GroupListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["groups", JSON.stringify({ columnFilters, pagination })],
    queryFn: async () => {
      const params = {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        query: columnFilters.find((f) => f.id === "query")?.value,
        type_acces: columnFilters.find((f) => f.id === "type_acces")?.value,
        est_actif: columnFilters.find((f) => f.id === "est_actif")?.value,
      };
      const res = await axios.get("/network/chat/groupes/", { params });
      return res.data;
    },
  });

export const useGetMyGroups = ({
  role,
  pagination,
}: {
  role?: "membre" | "admin";
  pagination: PaginationState;
}) =>
  useQuery<GroupListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["myGroups", role, pagination.pageIndex, pagination.pageSize],
    queryFn: async () => {
      const res = await axios.get("/network/chat/groupes/mes-groupes/", {
        params: {
          role,
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

/* =========================
   MEMBRES
   ========================= */

export const useGetGroupMembers = ({
  groupId,
  columnFilters,
  pagination,
}: {
  groupId: string;
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) =>
  useQuery<MembreGroupeListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["groupMembers", JSON.stringify({ columnFilters, pagination })],
    queryFn: async () => {
      const params = {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        query: columnFilters.find((f) => f.id === "query")?.value,
        role: columnFilters.find((f) => f.id === "role")?.value,
      };
      const res = await axios.get(`/network/chat/groupes/${groupId}/membres/`, {
        params,
      });
      return res.data;
    },
  });

/* =========================
   DEMANDES D’ACCÈS
   ========================= */

export const useGetGroupRequests = ({
  groupId,
  status,
  pagination,
}: {
  groupId: string | null;
  status?: "en_attente" | "approuve" | "refuse";
  pagination: PaginationState;
}) =>
  useQuery<DemandeAccesListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["groupRequests", groupId, status, pagination.pageIndex],
    queryFn: async () => {
      if (!groupId) throw new Error("Group ID is required");
      const res = await axios.get(
        `/network/chat/groupes/${groupId}/demandes/`,
        {
          params: {
            status,
            page: pagination.pageIndex + 1,
            page_size: pagination.pageSize,
          },
        },
      );
      return res.data;
    },
    enabled: !!groupId,
  });

export const useGetMyRequests = ({
  status,
  pagination,
}: {
  status?: "en_attente" | "approuve" | "refuse";
  pagination: PaginationState;
}) =>
  useQuery<DemandeAccesListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["myRequests", status, pagination.pageIndex],
    queryFn: async () => {
      const res = await axios.get("/network/chat/demandes/mes-demandes/", {
        params: {
          status,
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

/* =========================
   MESSAGES DE GROUPE
   ========================= */

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
      const res = await axios.get(`/network/chat/direct/${conversationId}/messages/`, {
        params: { page, page_size },
      });
      return res.data;
    },
    enabled: !!conversationId,
    refetchInterval: 3000,
  });

export const useGetRecentConversations = () =>
  useQuery<ConversationRecentOut[], AxiosError>({
    queryKey: ["recentConversations"],
    queryFn: async () => {
      const res = await axios.get("/network/chat/direct/conversations/");
      return res.data;
    },
    refetchInterval: 10000,
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

/* ============================================================
   MUTATION HOOKS
   ============================================================ */

/* =========================
   GROUPES
   ========================= */

export const useGroupActions = () => {
  const queryClient = useQueryClient();

  const createGroup = useMutation({
    mutationFn: (data: GroupCreate) =>
      axios.post("/network/chat/groupes/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["myGroups"] });
    },
  });

  const updateGroup = useMutation({
    mutationFn: (data: { id: string } & GroupUpdate) =>
      axios.patch(`/network/chat/groupes/${data.id}/`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["myGroups"] });
      queryClient.invalidateQueries({
        queryKey: ["groupDetails", variables.id],
      });
    },
  });

  const deleteGroup = useMutation({
    mutationFn: (groupId: string) =>
      axios.delete(`/network/chat/groupes/${groupId}/`),
    onSuccess: (_, groupId) => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["myGroups"] });
      queryClient.removeQueries({ queryKey: ["groupDetails", groupId] });
    },
  });

  const joinPublicGroup = useMutation({
    mutationFn: (groupId: string) =>
      axios.post(`/network/chat/groupes/${groupId}/rejoindre/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["myGroups"] });
    },
  });

  const leaveGroup = useMutation({
    mutationFn: (groupId: string) =>
      axios.post(`/network/chat/groupes/${groupId}/quitter/`),
    onSuccess: (_, groupId) => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["myGroups"] });
      queryClient.invalidateQueries({ queryKey: ["groupDetails", groupId] });
    },
  });

  return {
    createGroup,
    updateGroup,
    deleteGroup,
    joinPublicGroup,
    leaveGroup,
  };
};

/* =========================
   DEMANDES D’ACCÈS
   ========================= */

export const useAccessRequestActions = () => {
  const queryClient = useQueryClient();

  const createAccessRequest = useMutation({
    mutationFn: (data: { groupId: string } & DemandeAccesGroupeCreate) =>
      axios.post(`/network/chat/groupes/${data.groupId}/demandes/`, {
        message: data.message,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
    },
  });

  const approveAccessRequest = useMutation({
    mutationFn: (demandeId: string) =>
      axios.post(`/network/chat/groupes/demandes/${demandeId}/approuver/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groupRequests"] });
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
    },
  });

  const rejectAccessRequest = useMutation({
    mutationFn: (demandeId: string) =>
      axios.post(`/network/chat/groupes/demandes/${demandeId}/refuser/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groupRequests"] });
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
    },
  });

  const cancelAccessRequest = useMutation({
    mutationFn: ({
      demandeId,
      groupId,
    }: {
      demandeId?: string;
      groupId?: string;
    }) => {
      if (!demandeId && !groupId) {
        throw new Error("Demande ID or Group ID is required");
      }
      return demandeId
        ? axios.post(`/network/chat/groupes/demandes/${demandeId}/annuler/`)
        : axios.post(`/network/chat/groupes/${groupId}/demandes/annuler/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
    },
  });

  return {
    createAccessRequest,
    approveAccessRequest,
    rejectAccessRequest,
    cancelAccessRequest,
  };
};

/* =========================
   MEMBRES
   ========================= */

export const useGroupMemberActions = () => {
  const queryClient = useQueryClient();

  const addMemberToGroup = useMutation({
    mutationFn: (data: {
      groupId: string;
      profil_id: string;
      role?: "membre" | "admin";
    }) =>
      axios.post(`/network/chat/groupes/${data.groupId}/membres/`, {
        groupe_id: data.groupId,
        profil_id: data.profil_id,
        role: data.role ?? "membre",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["groupMembers"],
      });
    }
  });

  const removeMemberFromGroup = useMutation({
    mutationFn: (data: { groupId: string; membreId: string }) =>
      axios.delete(
        `/network/chat/groupes/${data.groupId}/membres/${data.membreId}/`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["groupMembers"],
      });
    },
  });

  const promoteMemberToAdmin = useMutation({
    mutationFn: (data: { groupId: string; membreId: string }) =>
      axios.patch(
        `/network/chat/groupes/${data.groupId}/membres/${data.membreId}/`,
        { role: "admin" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["groupMembers"],
      });
    },
  });

  const revokeAdminStatus = useMutation({
    mutationFn: (data: { groupId: string; membreId: string }) =>
      axios.patch(
        `/network/chat/groupes/${data.groupId}/membres/${data.membreId}/`,
        { role: "membre" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["groupMembers"],
      });
    },
  });

  return {
    addMemberToGroup,
    removeMemberFromGroup,
    promoteMemberToAdmin,
    revokeAdminStatus,
  };
};

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
      queryClient.invalidateQueries({ queryKey: ["recentConversations"] });
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

/* ============================================================
   HOOK COMBINÉ
   ============================================================ */

export const useChatActions = () => ({
  ...useGroupActions(),
  ...useAccessRequestActions(),
  ...useGroupMemberActions(),
  ...useGroupMessageActions(),
  ...useDirectMessageActions(),
  useInitConversation,
});
