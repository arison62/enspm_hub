/**
 * React Query hooks for Chat API
 * Covers all ChatService methods with proper typing
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";
import axios from "@/lib/axios";
import type { AxiosError } from "axios";
import type {
  GroupListResponse,
  GroupCreate,
  GroupUpdate,
  DemandeAccesListResponse,
  DemandeAccesGroupeCreate,
  MessageListResponse,
  MessageGroupeCreate,
  MessageDirectOut,
  MessageDirectCreate,
  ConversationOut,
  StatsMessagesOut,
} from "@/types/network";

// ============================================
// QUERY HOOKS - GROUPES
// ============================================

/**
 * Hook pour récupérer la liste des groupes avec filtres et pagination
 */
export const useGetGroups = ({
  columnFilters,
  pagination,
}: {
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) => {
  const { data, isLoading, isPending, error, refetch } = useQuery<
    GroupListResponse,
    AxiosError
  >({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["groups", JSON.stringify({ columnFilters, pagination })],
    queryFn: async () => {
      const params = {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        query: columnFilters.find((filter) => filter.id === "query")?.value,
        type_acces: columnFilters.find((filter) => filter.id === "type_acces")
          ?.value,
        est_actif: columnFilters.find((filter) => filter.id === "est_actif")
          ?.value,
      };
      const res = await axios.get("/network/chat/groupes/", {
        params: params,
      });
      return res.data;
    },
  });
  return { data, isLoading, isPending, error, refetch };
};

/**
 * Hook pour récupérer les groupes dont l'utilisateur est membre
 */
export const useGetMyGroups = ({
  role,
  pagination,
}: {
  role?: "membre" | "admin";
  pagination: PaginationState;
}) => {
  return useQuery<GroupListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["myGroups", role, pagination.pageIndex, pagination.pageSize],
    queryFn: async () => {
      const params = {
        role,
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
      };
      const res = await axios.get("/network/chat/groupes/mes-groupes/", {
        params,
      });
      return res.data;
    },
  });
};

// ============================================
// QUERY HOOKS - DEMANDES D'ACCÈS
// ============================================

/**
 * Hook pour récupérer les demandes d'accès d'un groupe (pour les admins)
 */
export const useGetGroupRequests = ({
  groupId,
  status,
  pagination,
}: {
  groupId: string | null;
  status?: "en_attente" | "approuve" | "refuse";
  pagination: PaginationState;
}) => {
  return useQuery<DemandeAccesListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: [
      "groupRequests",
      groupId,
      status,
      pagination.pageIndex,
      pagination.pageSize,
    ],
    queryFn: async () => {
      if (!groupId) throw new Error("Group ID is required");
      const params = {
        status,
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
      };
      const res = await axios.get(
        `/network/chat/groupes/${groupId}/demandes/`,
        { params },
      );
      return res.data;
    },
    enabled: !!groupId,
  });
};

/**
 * Hook pour récupérer les demandes d'accès de l'utilisateur
 */
export const useGetMyRequests = ({
  status,
  pagination,
}: {
  status?: "en_attente" | "approuve" | "refuse";
  pagination: PaginationState;
}) => {
  return useQuery<DemandeAccesListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["myRequests", status, pagination.pageIndex, pagination.pageSize],
    queryFn: async () => {
      const params = {
        status,
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
      };
      const res = await axios.get("/network/chat/demandes/mes-demandes/", {
        params,
      });
      return res.data;
    },
  });
};

// ============================================
// QUERY HOOKS - MESSAGES
// ============================================

/**
 * Hook pour récupérer les messages d'un groupe
 */
export const useGetGroupMessages = ({
  groupId,
  pagination,
}: {
  groupId: string | null;
  pagination: PaginationState;
}) => {
  return useQuery<MessageListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: [
      "groupMessages",
      groupId,
      pagination.pageIndex,
      pagination.pageSize,
    ],
    queryFn: async () => {
      if (!groupId) throw new Error("Group ID is required");
      const params = {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
      };
      const res = await axios.get(
        `/network/chat/groupes/${groupId}/messages/`,
        { params },
      );
      return res.data;
    },
    enabled: !!groupId,
    refetchInterval: 5000, // Auto-refresh toutes les 5 secondes
  });
};

/**
 * Hook pour récupérer une conversation directe
 */
export const useGetDirectMessages = ({
  profilId,
  limit = 50,
  offset = 0,
}: {
  profilId: string | null;
  limit?: number;
  offset?: number;
}) => {
  return useQuery<MessageDirectOut[], AxiosError>({
    queryKey: ["directMessages", profilId, limit, offset],
    queryFn: async () => {
      if (!profilId) throw new Error("Profil ID is required");
      const params = { limit, offset };
      const res = await axios.get(`/network/chat/direct/${profilId}/`, {
        params,
      });
      return res.data;
    },
    enabled: !!profilId,
    refetchInterval: 3000, // Auto-refresh toutes les 3 secondes
  });
};

/**
 * Hook pour récupérer les conversations récentes
 */
export const useGetRecentConversations = () => {
  return useQuery<ConversationOut[], AxiosError>({
    queryKey: ["recentConversations"],
    queryFn: async () => {
      const res = await axios.get("/network/chat/conversations/recentes/");
      return res.data;
    },
    refetchInterval: 10000, // Auto-refresh toutes les 10 secondes
  });
};

/**
 * Hook pour récupérer les statistiques de messagerie
 */
export const useGetMessageStats = () => {
  return useQuery<StatsMessagesOut, AxiosError>({
    queryKey: ["messageStats"],
    queryFn: async () => {
      const res = await axios.get("/network/chat/stats/messages/");
      return res.data;
    },
  });
};

// ============================================
// MUTATION HOOKS - GROUPES
// ============================================

/**
 * Hook pour les actions sur les groupes
 */
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

// ============================================
// MUTATION HOOKS - DEMANDES D'ACCÈS
// ============================================

/**
 * Hook pour les actions sur les demandes d'accès
 */
export const useAccessRequestActions = () => {
  const queryClient = useQueryClient();

  const createAccessRequest = useMutation({
    mutationFn: (data: { groupId: string } & DemandeAccesGroupeCreate) =>
      axios.post(`/network/chat/groupes/${data.groupId}/demandes/`, {
        message: data.message,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
      queryClient.invalidateQueries({
        queryKey: ["groupDetails", variables.groupId],
      });
    },
  });

  const approveAccessRequest = useMutation({
    mutationFn: (demandeId: string) =>
      axios.post(`/network/chat/groupes/demandes/${demandeId}/approuver/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groupRequests"] });
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
      queryClient.invalidateQueries({ queryKey: ["groupDetails"] });
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
    mutationFn: async ({
      demandeId,
      groupId,
    }: {
      demandeId?: string;
      groupId?: string;
    }) => {
      if (!demandeId && !groupId) {
        throw new Error("Demande ID or Group ID is required");
      }
      if (demandeId) {
        return axios.post(
          `/network/chat/groupes/demandes/${demandeId}/annuler/`,
        );
      }
      return axios.post(`/network/chat/groupes/${groupId}/demandes/annuler/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["myRequests"] });
      queryClient.invalidateQueries({ queryKey: ["groupDetails"] });
    },
  });

  return {
    createAccessRequest,
    approveAccessRequest,
    rejectAccessRequest,
    cancelAccessRequest,
  };
};

// ============================================
// MUTATION HOOKS - MEMBRES
// ============================================

/**
 * Hook pour les actions sur les membres de groupe
 */
export const useMemberActions = () => {
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
        role: data.role || "membre",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["groupDetails", variables.groupId],
      });
      queryClient.invalidateQueries({ queryKey: ["groupRequests"] });
    },
  });

  const removeMemberFromGroup = useMutation({
    mutationFn: (data: { groupId: string; membreId: string }) =>
      axios.delete(
        `/network/chat/groupes/${data.groupId}/membres/${data.membreId}/`,
      ),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["groupDetails", variables.groupId],
      });
    },
  });

  return {
    addMemberToGroup,
    removeMemberFromGroup,
  };
};

// ============================================
// MUTATION HOOKS - MESSAGES DE GROUPE
// ============================================

/**
 * Hook pour les actions sur les messages de groupe
 */
export const useGroupMessageActions = () => {
  const queryClient = useQueryClient();

  const sendGroupMessage = useMutation({
    mutationFn: (data: { groupId: string } & MessageGroupeCreate) =>
      axios.post(`/network/chat/groupes/${data.groupId}/messages/`, {
        contenu: data.contenu,
        reponse_a_id: data.reponse_a_id,
        piece_jointe_base64: data.piece_jointe_base64,
      }),
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

  return {
    sendGroupMessage,
    markGroupMessageAsRead,
  };
};

// ============================================
// MUTATION HOOKS - MESSAGES DIRECTS
// ============================================

/**
 * Hook pour les actions sur les messages directs
 */
export const useDirectMessageActions = () => {
  const queryClient = useQueryClient();

  const sendDirectMessage = useMutation({
    mutationFn: (data: MessageDirectCreate) =>
      axios.post("/network/chat/direct/", data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["directMessages", variables.destinataire_id],
      });
      queryClient.invalidateQueries({ queryKey: ["recentConversations"] });
    },
  });

  const markConversationAsRead = useMutation({
    mutationFn: (expediteurId: string) =>
      axios.post(`/network/chat/direct/${expediteurId}/lu/`),
    onSuccess: (_, expediteurId) => {
      queryClient.invalidateQueries({
        queryKey: ["directMessages", expediteurId],
      });
      queryClient.invalidateQueries({ queryKey: ["recentConversations"] });
      queryClient.invalidateQueries({ queryKey: ["messageStats"] });
    },
  });

  return {
    sendDirectMessage,
    markConversationAsRead,
  };
};

// ============================================
// HOOKS COMBINÉS (pour faciliter l'utilisation)
// ============================================

/**
 * Hook combiné pour toutes les actions de chat
 */
export const useChatActions = () => {
  return {
    ...useGroupActions(),
    ...useAccessRequestActions(),
    ...useMemberActions(),
    ...useGroupMessageActions(),
    ...useDirectMessageActions(),
  };
};
