import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";

import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Button } from "@/components/ui/button";
import { useDebounce } from "@uidotdev/usehooks";
import {
  InputGroup,
  InputGroupInput,
  InputGroupAddon,
} from "@/components/ui/input-group";
import {
  useAccessRequestActions,
  useGetGroups,
  useGroupActions,
} from "@/api/network/groups";
import {
  GroupCard,
  GroupCardSkeleton,
} from "../../components/network/group-card";
import { useAuthStore } from "@/stores/authStore";
import { router } from "@inertiajs/react";

interface PaginationType {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}

const GroupsListPage: React.FC = () => {
  const isSiteAdmin = useAuthStore((state) => state.isAdmin);
  const [searchQuery, setSearchQuery] = useState("");
  const searchDebounced = useDebounce(searchQuery, 300);
  const [filters, setFilters] = useState<Array<{ id: string; value: string }>>(
    [],
  );
  const [pagination, setPagination] = useState<PaginationType>({
    pageIndex: 0,
    pageSize: 12,
    totalItems: 0,
  });
  const { joinPublicGroup, leaveGroup, deleteGroup, updateGroup } =
    useGroupActions();
  const { createAccessRequest } = useAccessRequestActions();

  const { isLoading, data } = useGetGroups({
    columnFilters: filters,
    pagination: {
      pageIndex: pagination.pageIndex,
      pageSize: pagination.pageSize,
    },
  });
  const groups = data.items;
  const pageCount = Math.ceil(pagination.totalItems / pagination.pageSize);

  useEffect(() => {
    if (data.meta.page != 0) {
      setPagination((prevPagination) => ({
        ...prevPagination,
        totalItems: data.meta.total_items,
      }));
    }
  }, [data.meta.page]);

  useEffect(() => {
    const newFilters = filters.filter((filter) => filter.id !== "query");
    newFilters.push({ id: "query", value: searchDebounced });
    setFilters(newFilters);
  }, [searchDebounced]);

  const handlePageChange = (page: number) => {
    setPagination((prevPagination) => ({
      ...prevPagination,
      pageIndex: page,
    }));
  };
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  };

  const handleLeave = async (groupId: string) => {
    leaveGroup.mutateAsync(groupId);
  };
  const handleJoin = async (groupId: string, isPublic: boolean = false) => {
    if (isPublic) {
      joinPublicGroup.mutateAsync(groupId);
    } else {
      createAccessRequest.mutateAsync({ groupId });
    }
  };
  const handleGoToPage = async (slug: string, action: string) => {
    router.get(`/network/groups/${slug}?tab=${action}`);
  };
  const handleToggleActive = async (groupId: string, prevStatus: string) => {
    const newStatus = prevStatus === "actif" ? "inactif" : "actif";
    updateGroup.mutateAsync({ id: groupId, status: newStatus });
  };
  const handleDelete = async (groupId: string) => {
    deleteGroup.mutateAsync(groupId);
  };
  return (
    <div className="space-y-4 md:space-y-6 max-w-3xl mx-2 sm:mx-auto">
      <div className="relative flex justify-center mt-4">
        <InputGroup className="max-w-xs">
          <InputGroupInput
            placeholder="Recherche..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
          <InputGroupAddon>
            <Search />
          </InputGroupAddon>
          <InputGroupAddon align="inline-end">
            {pagination.totalItems} resultats
          </InputGroupAddon>
        </InputGroup>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <GroupCardSkeleton key={i} />)
        ) : groups.length > 0 ? (
          groups.map((group) => (
            <GroupCard
              className="mx-auto w-full"
              key={group.id}
              onView={() => handleGoToPage(group.slug, "accueil")}
              onLeave={() => handleLeave(group.id)}
              onJoin={() => handleJoin(group.id, group.type_acces === "public")}
              onDelete={() => handleDelete(group.id)}
              onToggleActive={() => handleToggleActive(group.id, group.status)}
              onViewRequests={() => handleGoToPage(group.slug, "demandes")}
              onEdit={() => handleGoToPage(group.slug, "parametres")}
              isSiteAdmin={isSiteAdmin}
              data={{
                id: group.id,
                nom: group.nom,
                description: group.description,
                type_acces: group.type_acces,
                image_url: group.image_url,
                nombre_membres: group.nombre_membres,
                has_user_pending_request: group.has_user_pending_request,
                pending_request: group.pending_request,
                est_membre: group.is_member,
                est_admin: group.is_admin,
                est_actif: group.est_actif,
                slug: group.id,
                createur: group.createur
                  ? { id: group.createur.id, nom: group.createur.nom_complet }
                  : null,
              }}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            Aucun membre ne correspond à votre recherche.
          </div>
        )}
      </div>
      {!isLoading && pagination.totalItems > 0 && (
        <div className="pt-4">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  className={`cursor-pointer ${
                    pagination.pageIndex === 0
                      ? "pointer-events-none opacity-50"
                      : ""
                  }`}
                  onClick={() => handlePageChange(pagination.pageIndex - 1)}
                />
              </PaginationItem>

              {[...Array(Math.min(5, pageCount))].map((_, index) => {
                const page = index; // Commence à 1
                if (page >= 0 && page <= pageCount) {
                  return (
                    <PaginationItem key={page}>
                      <Button
                        variant={
                          pagination.pageIndex === page ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() => handlePageChange(page)}
                        className="w-8 h-8 p-0"
                      >
                        {page + 1}
                      </Button>
                    </PaginationItem>
                  );
                }
                return null;
              })}

              {pageCount > 5 && (
                <>
                  {pagination.pageIndex < pageCount - 3 && (
                    <PaginationItem>
                      <PaginationEllipsis />
                    </PaginationItem>
                  )}
                  {pagination.pageIndex < pageCount - 2 && (
                    <PaginationItem>
                      <Button
                        variant={
                          pagination.pageIndex === pageCount
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        onClick={() => handlePageChange(pageCount)}
                        className="w-8 h-8 p-0"
                      >
                        {pageCount}
                      </Button>
                    </PaginationItem>
                  )}
                </>
              )}

              <PaginationItem>
                <PaginationNext
                  className={`cursor-pointer ${
                    pagination.pageIndex + 1 >= pageCount
                      ? "pointer-events-none opacity-50"
                      : ""
                  }`}
                  onClick={() => handlePageChange(pagination.pageIndex + 1)}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>

          <div className="mt-2 text-sm text-muted-foreground text-center">
            Page {pagination.pageIndex + 1} sur {pageCount} (
            {pagination.totalItems} résultats)
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupsListPage;
