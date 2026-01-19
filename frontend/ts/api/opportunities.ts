import { useQuery } from "@tanstack/react-query";
import type {
  StageResponse,
  EmploiResponse,
  FormationResponse,
} from "@/types/opportunities";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";
import { useMemo } from "react";

export type Pagination = {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
};

export type FilerValue =
  | string
  | boolean
  | number
  | Set<string | number | boolean>;
export type Filters = {
  id: string;
  value: FilerValue;
};

export const useGetOpportunites = ({
  filters,
  pagination,
}: {
  filters: Filters[];
  pagination: Pagination;
}) => {
  // Créer une clé stable et sérialisable pour React Query
  const queryKey = useMemo(() => {
    // Normaliser les filtres pour la clé
    const normalizedFilters = filters.map((filter) => {
      let value = filter.value;

      // Convertir les Set en tableau trié
      if (value instanceof Set) {
        value = Array.from(value).sort().join(",");
      } else if (
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
      ) {
        // Garder les valeurs simples telles quelles
        value = value.toString();
      }

      return {
        id: filter.id,
        value: value,
      };
    });

    // Trier les filtres par id pour une clé stable
    normalizedFilters.sort((a, b) => a.id.localeCompare(b.id));

    // Retourner une clé de requête compatible avec React Query
    return [
      "opportunites",
      normalizedFilters,
      pagination.pageIndex,
      pagination.pageSize,
    ] as const;
  }, [filters, pagination.pageIndex, pagination.pageSize]);

  const { data, isLoading, error, refetch } = useQuery<
    StageResponse | EmploiResponse | FormationResponse,
    AxiosError
  >({
    initialData: {
      items: [],
      meta: {
        total_items: pagination.totalItems,
        total_pages: 0,
        page: pagination.pageIndex,
        page_size: pagination.pageSize,
      },
    },
    queryKey: queryKey,
    queryFn: async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const params: Record<string, any> = {
        statut: "active",
        page: pagination.pageIndex,
        page_size: pagination.pageSize,
      };

      filters.forEach((filter) => {
        if (filter.id === "search") {
          params.search = filter.value;
        } else if (filter.id === "opportunity_type") {
          // Déjà géré par l'URL
        } else if (filter.value instanceof Set) {
          params[filter.id] = Array.from(filter.value);
        } else if (Array.isArray(filter.value)) {
          params[filter.id] = filter.value.join(",");
        } else {
          params[filter.id] = filter.value;
        }
      });

      const opportunityType = filters.find(
        (filter) => filter.id === "opportunity_type"
      )?.value;

      let url = "/internships/";
      if (opportunityType === "formation") {
        url = "/trainings/";
      } else if (opportunityType === "emploi" || !opportunityType) {
        url = "/jobs/";
      }

      const res = await axios.get(url, {
        params,
      });

      return res.data;
    },
    // Options supplémentaires pour une meilleure expérience

    refetchOnWindowFocus: true,
  });

  return { data, isLoading, error, refetch };
};
