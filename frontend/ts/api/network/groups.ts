/**
 * React Query hooks for Group API
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnFiltersState, PaginationState } from "@tanstack/react-table";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";

import type {
  GroupListResponse,
  GroupOut,
  GroupCreate,
  GroupUpdate,
  MembreGroupeListResponse,
  MembreGroupeCreate,
  MembreGroupeUpdate,
  DemandeAccesListResponse,
  DemandeAccesGroupeCreate,
} from "@/types/network";
import { chatKeys } from "./chat";

export const groupKeys = {
  all: ['groups'] as const,
  list: (filters: any) => [...groupKeys.all, 'list', filters] as const,
  my: (filters: any) => [...groupKeys.all, 'my', filters] as const,
  detail: (id: string) => [...groupKeys.all, 'detail', id] as const,
  members: (id: string) => [...groupKeys.all, 'members', id] as const,
  requests: (id: string) => [...groupKeys.all, 'requests', id] as const,
  myRequests: (status: string) => [...groupKeys.all, 'myRequests', status] as const,
};

/* ============================================================
   QUERY HOOKS
   ============================================================ */

export const useGetGroups = ({
  columnFilters,
  pagination,
}: {
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) => {
  const query = columnFilters.find((f) => f.id === "query")?.value;
  const type_acces = columnFilters.find((f) => f.id === "type_acces")?.value;

  return useQuery<GroupListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: groupKeys.list({ query, type_acces, pagination }),
    queryFn: async () => {
      const res = await axios.get("/network/chat/groupes/", {
        params: {
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
          query,
          type_acces,
        },
      });
      return res.data;
    },
  });
};

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
    queryKey: groupKeys.my({ role, pagination }),
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

export const useGetGroupDetails = (groupId: string | null) =>
  useQuery<GroupOut, AxiosError>({
    enabled: !!groupId,
    queryKey: groupKeys.detail(groupId || ""),
    queryFn: async () => {
      const res = await axios.get(`/network/chat/groupes/${groupId}/`);
      return res.data;
    },
  });

export const useGetGroupMembers = ({
  groupId,
  pagination,
  query,
}: {
  groupId: string | null;
  pagination: PaginationState;
  query?: string;
}) =>
  useQuery<MembreGroupeListResponse, AxiosError>({
    enabled: !!groupId,
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: groupKeys.members(groupId || ""),
    queryFn: async () => {
      const res = await axios.get(`/network/chat/groupes/${groupId}/membres/`, {
        params: {
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
          query,
        },
      });
      return res.data;
    },
  });

export const useGetGroupRequests = ({
  groupId,
  status,
  pagination,
}: {
  groupId: string | null;
  status?: string;
  pagination: PaginationState;
}) =>
  useQuery<DemandeAccesListResponse, AxiosError>({
    enabled: !!groupId,
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: groupKeys.requests(groupId || ""),
    queryFn: async () => {
      const res = await axios.get(`/network/chat/groupes/${groupId}/demandes/`, {
        params: {
          status,
          page: pagination.pageIndex + 1,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });

export const useGetMyRequests = ({
  status,
  pagination,
}: {
  status?: string;
  pagination: PaginationState;
}) =>
  useQuery<DemandeAccesListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: groupKeys.myRequests(status || "all"),
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
      axios.post<GroupOut>("/network/chat/groupes/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
  });

  const updateGroup = useMutation({
    mutationFn: ({ id, data }: { id: string; data: GroupUpdate }) =>
      axios.patch<GroupOut>(`/network/chat/groupes/${id}/`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: groupKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
    },
  });

  const deleteGroup = useMutation({
    mutationFn: (id: string) => axios.delete(`/network/chat/groupes/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
  });

  const joinPublicGroup = useMutation({
    mutationFn: (id: string) => axios.post(`/network/chat/groupes/${id}/rejoindre/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
  });

  const leaveGroup = useMutation({
    mutationFn: (id: string) => axios.post(`/network/chat/groupes/${id}/quitter/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
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
    mutationFn: ({ groupId, message }: { groupId: string; message?: string }) =>
      axios.post(`/network/chat/groupes/${groupId}/demandes/`, { message }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
    },
  });

  const approveAccessRequest = useMutation({
    mutationFn: (demandeId: string) =>
      axios.post(`/network/chat/groupes/demandes/${demandeId}/approuver/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
    },
  });

  const rejectAccessRequest = useMutation({
    mutationFn: (demandeId: string) =>
      axios.post(`/network/chat/groupes/demandes/${demandeId}/refuser/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
    },
  });

  const cancelAccessRequest = useMutation({
    mutationFn: (groupId: string) =>
      axios.post(`/network/chat/groupes/${groupId}/demandes/annuler/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
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
    mutationFn: ({ groupId, data }: { groupId: string; data: MembreGroupeCreate }) =>
      axios.post(`/network/chat/groupes/${groupId}/membres/`, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: groupKeys.members(vars.groupId) });
    },
  });

  const updateGroupMember = useMutation({
    mutationFn: ({
      groupId,
      membreId,
      data,
    }: {
      groupId: string;
      membreId: string;
      data: MembreGroupeUpdate;
    }) => axios.patch(`/network/chat/groupes/${groupId}/membres/${membreId}/`, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: groupKeys.members(vars.groupId) });
    },
  });

  const removeMemberFromGroup = useMutation({
    mutationFn: ({ groupId, membreId }: { groupId: string; membreId: string }) =>
      axios.delete(`/network/chat/groupes/${groupId}/membres/${membreId}/`),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: groupKeys.members(vars.groupId) });
    },
  });

  return {
    addMemberToGroup,
    updateGroupMember,
    removeMemberFromGroup,
  };
};

/* ============================================================
   HOOK COMBINÉ
   ============================================================ */

export const useChatActions = () => ({
  ...useGroupActions(),
  ...useAccessRequestActions(),
  ...useGroupMemberActions(),
});
