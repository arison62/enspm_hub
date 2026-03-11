import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";

import {
  type MentorProfileListResponse,
  type MentorProfileOut,
  type MentorProfileCreate,
  type MentorProfileUpdate,
} from "@/types/network";

export const mentoringKeys = {
  all: ["mentoring"] as const,
  list: (filters: any) => [...mentoringKeys.all, "list", filters] as const,
  detail: (id: number) => [...mentoringKeys.all, "detail", id] as const,
  create: () => [...mentoringKeys.all, "create"] as const,
  update: (id: number) => [...mentoringKeys.all, "update", id] as const,
  delete: (id: number) => [...mentoringKeys.all, "delete", id] as const,
};

export const useGetMentorProfil = ({
  columnFilters,
  pagination,
}: {
  columnFilters?: ColumnFiltersState;
  pagination: PaginationState;
}) => {
  return useQuery<MentorProfileListResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: mentoringKeys.list({ columnFilters, pagination }),
    queryFn: async () => {
      const res = await axios.get("/network/mentoring/mentors/", {
        params: {
          page: pagination.pageIndex + 1,
          search: columnFilters?.find((f) => f.id === "search")?.value,
          page_size: pagination.pageSize,
        },
      });
      return res.data;
    },
  });
};

/* ============================================================
   MUTATION HOOKS
   ============================================================ */

/* =========================
   Mentoring
   ========================= */
export const useMentoringActions = () => {
  const queryClient = useQueryClient();
  const createMentorProfil = useMutation({
    mutationFn: (data: MentorProfileCreate) => {
      return axios.post<MentorProfileOut>("/network/mentoring/mentors/", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mentoringKeys.all });
    },
  });

  const updateMentorProfil = useMutation({
    mutationFn: ({ id, data }: { id: number; data: MentorProfileUpdate }) => {
      return axios.patch<MentorProfileOut>(
        `/network/mentoring/mentors/${id}/`,
        data
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mentoringKeys.all });
    },
  });

  const deleteMentorProfil = useMutation({
    mutationFn: (id: number) => {
      return axios.delete(`/network/mentoring/mentors/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mentoringKeys.all });
    },
  });
  
  const validateMentorProfil = useMutation({
    mutationFn: (id: number) => {
      return axios.post(`/network/mentoring/mentors/${id}/valider/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mentoringKeys.all });
    },
  });
  
  return {
    createMentorProfil,
    updateMentorProfil,
    deleteMentorProfil,
    validateMentorProfil,
  };
};
