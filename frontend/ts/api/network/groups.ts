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
} from "@/types/network";
import { chatKeys } from "./chat";

export const groupKeys = {
  all: ['groups'] as const,
  list: (filters: any) => [...groupKeys.all, 'list', filters] as const,
  detail: (id: string) => [...groupKeys.all, 'detail', id] as const,
  members: (id: string) => [...groupKeys.all, 'members', id] as const,
};

/* ============================================================
   QUERIES
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
}: {
  groupId: string | null;
  pagination: PaginationState;
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
        },
      });
      return res.data;
    },
  });

/* ============================================================
   MUTATIONS
   ============================================================ */

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

  const leaveGroup = useMutation({
    mutationFn: (id: string) => axios.post(`/network/chat/groupes/${id}/quitter/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupKeys.all });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
  });

  return { createGroup, updateGroup, deleteGroup, leaveGroup };
};
