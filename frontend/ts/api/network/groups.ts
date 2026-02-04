import { useMutation} from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import type {
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";
import axios from "@/lib/axios";
import type { GroupListResponse } from "@/types/network";
import type { AxiosError } from "axios";


export const useGetGroups = ({
  columnFilters,
  pagination,
}: {
  columnFilters: ColumnFiltersState;
  pagination: PaginationState;
}) => {
  const { data, isLoading, isPending, error, refetch } = useQuery<GroupListResponse, AxiosError>({
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

export const useGroupActions = () => {
    const createGroup = useMutation({
        mutationFn: (
            data: {
                nom: string;
                description: string;
                type_acces: "public" | "private";
                 base64_image?: string;
            }
        ) =>  axios.post("/network/chat/groupes/", data),
        
    })

    const updateGroup = useMutation({
        mutationFn: (
            data: {
                id: string;
                nom?: string;
                description?: string;
                type_acces?: "public" | "private";
                 base64_image?: string | null;
            }
        ) =>  axios.patch(`/network/chat/groupes/${data.id}/`, data),
    })

    const deleteGroup = useMutation({
        mutationFn: (groupId: string) => axios.delete(`/network/chat/groupes/${groupId}/`),
    })
    const leaveGroup = useMutation({
        mutationFn: (groupId: string) => axios.post(`/network/chat/groupes/${groupId}/quitter`),
    })
    const addMemberToGroup = useMutation({
        mutationFn: (
            data: {
                groupId: string;
                profilId: string;
                role?: "member" | "admin";
            }
        ) => axios.post(`/network/chat/groupes/${data.groupId}/membres`, { profil_id: data.profilId, role: data.role }),
    })

    const removeMemberFromGroup = useMutation({
        mutationFn: (
            data: {
                groupId: string;
                profilId: string;
            }
        ) => axios.delete(`/network/chat/groupes/${data.groupId}/membres/${data.profilId}`),
    })
    return {
        createGroup,
        updateGroup,
        deleteGroup,
        leaveGroup,
        addMemberToGroup,
        removeMemberFromGroup
    }
}


