import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";

import {
  MemberCard,
  MemberCardSkeleton,
} from "../../components/network/member-card";
import { useGetUsers } from "@/api/users";
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

interface PaginationType {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}
const MembersListPage: React.FC = () => {
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
  const { isLoading, data } = useGetUsers({
    columnFilters: filters,
    pagination: {
      pageIndex: pagination.pageIndex,
      pageSize: pagination.pageSize,
    },
  });
  const members = data.items;
  const pageCount = Math.ceil(pagination.totalItems / pagination.pageSize);

  useEffect(() => {
    if (data.meta.page !== pagination.pageIndex) {
      setPagination((prevPagination) => ({
        ...prevPagination,
        totalItems: data.meta.total_items,
      }));
    }
  }, [data.meta.page, data.meta.total_items, pagination.pageIndex]);
  useEffect(() => {
    const newFilters = filters.filter((filter) => filter.id !== "search");
    newFilters.push({ id: "search", value: searchDebounced });
    setFilters(newFilters);
  }, [filters, searchDebounced]);

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

  return (
    <div className="space-y-4 md:space-y-6 max-w-3xl mx-auto">
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
          Array.from({ length: 4 }).map((_, i) => (
            <MemberCardSkeleton key={i} />
          ))
        ) : members.length > 0 ? (
          members.map((member) => (
            <MemberCard
              key={member.id}
              data={{
                id: member.id,
                name: member.profil.nom_complet,
                title: member.profil.titre?.titre,
                bio: member.profil?.bio || undefined,
                avatar: member.profil.photo_profil || undefined,
                promo: member.profil.annee_sortie?.libelle || undefined,
                position: member.profil.poste_actuel?.titre_poste || undefined,
                company:
                  member.profil.poste_actuel?.nom_entreprise || undefined,
                slug: member.profil.slug,
                status_global: member.profil.statut_global,
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

export default MembersListPage;
