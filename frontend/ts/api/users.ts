/* eslint-disable @typescript-eslint/no-explicit-any */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import type {
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";

import type { UserResponse } from "@/types/user";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";

export const useGetUsers = ({
  columnFilters,
  pagination,
}: {
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) => {
  const { data, isLoading, error, refetch } = useQuery<UserResponse, AxiosError>({
    initialData: {
      items: [],
      meta: { total_items: 0, total_pages: 0, page: 0, page_size: 0 },
    },
    queryKey: ["users", JSON.stringify({ columnFilters, pagination })],
    queryFn: async () => {
      const params = {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        search: columnFilters.find((filter) => filter.id === "search")?.value,
        role_systeme: columnFilters.find(
          (filter) => filter.id === "role_systeme"
        )?.value,
        est_actif: columnFilters.find((filter) => filter.id === "est_actif")
          ?.value,
      };
      const res = await axios.get("/users/", {
        params: params,
      });
      return res.data;
    },
  });
  return { data, isLoading, error, refetch };
};

// Fonction pour désactiver/activer un utilisateur
const toggleUserStatus = async (userId: string, est_actif: boolean) => {
  const res = await axios.post(`/users/${userId}/toggle-status`, { est_actif });
  return res.data;
};

// Fonction pour supprimer un utilisateur
const deleteUser = async (userId: string) => {
  await axios.delete(`/users/${userId}`);
};

// Hook personnalisé
export const useUserActions = () => {
  const queryClient = useQueryClient();

  // Mutation pour toggle statut
  const toggleStatus = useMutation({
    mutationFn: ({
      userId,
      est_actif,
    }: {
      userId: string;
      est_actif: boolean;
    }) => toggleUserStatus(userId, est_actif),
    onSuccess: () => {
      // Invalide le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error: any) => {
      throw error;
    },
  });

  // Mutation pour suppression
  const removeUser = useMutation({
    mutationFn: (userId: string) => deleteUser(userId),
    onSuccess: () => {
      // Invalide le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error: any) => {
      throw error;
    },
  });

  return {
    toggleStatus,
    removeUser,
  };
};
