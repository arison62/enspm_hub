import React, { useState, useEffect } from "react";
import { Check, X, Search } from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useDebounce } from "@uidotdev/usehooks";
import {
  InputGroup,
  InputGroupInput,
  InputGroupAddon,
} from "@/components/ui/input-group";
import {
  useGetGroupRequests,
  useAccessRequestActions,
} from "@/api/network/groups";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Link } from "@inertiajs/react";
import type { DemandeAccesGroupeOut } from "@/types/network";

interface PaginationType {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}

interface MemberAccessCardProps {
  demande: DemandeAccesGroupeOut;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isPending?: boolean;
}

const MemberAccessCardSkeleton: React.FC = () => (
  <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm animate-pulse">
    <div className="flex items-start gap-4">
      <div className="h-12 w-12 rounded-full bg-muted" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-1/3 bg-muted rounded" />
        <div className="h-3 w-1/2 bg-muted rounded" />
      </div>
      <div className="flex gap-2">
        <div className="h-9 w-20 bg-muted rounded" />
        <div className="h-9 w-20 bg-muted rounded" />
      </div>
    </div>
  </div>
);

const MemberAccessCard: React.FC<MemberAccessCardProps> = ({
  demande,
  onApprove,
  onReject,
  isPending = false,
}) => {
  const getStatusBadge = (status: string) => {
    const variants: Record<string, string> = {
      en_attente: "text-xs bg-yellow-100 text-yellow-800 hover:bg-yellow-100",
      approuve: "text-xs bg-green-100 text-green-800 hover:bg-green-100",
      refuse: "text-xs bg-red-100 text-red-800 hover:bg-red-100",
    };
    return variants[status] || "bg-gray-100 text-gray-800";
  };
  const getStatusDisplay = (status: string) => {
    if (status === "en_attente") {
      return "En attente";
    } else if (status === "approuve") {
      return "Approuvée";
    } else {
      return "Refusée";
    }
  };
  return (
    <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <Link href={`/profile/${demande.demandeur.slug}`}>
          <Avatar className="h-12 w-12 shrink-0">
            <AvatarImage src={demande.demandeur.photo_profil || ""} className="object-cover" />
            <AvatarFallback>
              {demande.demandeur.nom_complet
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-base truncate">
              {demande.demandeur.nom_complet}
            </h3>
            <Badge
              variant="secondary"
              className={getStatusBadge(demande.status)}
            >
              {getStatusDisplay(demande.status)}
            </Badge>
          </div>

          {demande.message && (
            <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
              {demande.message}
            </p>
          )}

          <p className="text-xs text-muted-foreground mt-2">
            Demande envoyée le{" "}
            {new Date(demande.created_at).toLocaleDateString("fr-FR")}
          </p>
        </div>

        {demande.status === "en_attente" && (
          <div className="flex gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              className="text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={() => onReject(demande.id)}
              disabled={isPending}
            >
              <X className="h-4 w-4 mr-1" />
              <span className="hidden md:inline">Refuser</span>
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-green-600 hover:bg-green-50"
              onClick={() => onApprove(demande.id)}
              disabled={isPending}
            >
              <Check className="h-4 w-4 mr-1" />
              <span className="hidden md:inline">Accepter</span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

interface GroupPageRequestsTabProps {
  groupId: string;
}

const GroupPageRequestsTab: React.FC<GroupPageRequestsTabProps> = ({
  groupId,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const searchDebounced = useDebounce(searchQuery, 300);
  const [status, setStatus] = useState<"en_attente" | "approuve" | "refuse">(
    "en_attente",
  );
  console.log("groupId", groupId);
  const [pagination, setPagination] = useState<PaginationType>({
    pageIndex: 0,
    pageSize: 12,
    totalItems: 0,
  });

  const { approveAccessRequest, rejectAccessRequest } =
    useAccessRequestActions();

  const { isLoading, data } = useGetGroupRequests({
    groupId,
    status,
    pagination: {
      pageIndex: pagination.pageIndex,
      pageSize: pagination.pageSize,
    },
  });

  const requests = data?.items || [];
  const pageCount = Math.ceil(
    (data?.meta?.total_items || 0) / pagination.pageSize,
  );

  useEffect(() => {
    if (data?.meta?.total_items !== undefined) {
      setPagination((prev) => ({
        ...prev,
        totalItems: data.meta.total_items,
      }));
    }
  }, [data?.meta?.total_items]);

  useEffect(() => {
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }, [status, searchDebounced]);

  const handlePageChange = (page: number) => {
    setPagination((prev) => ({
      ...prev,
      pageIndex: page,
    }));
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  };

  const handleApprove = async (requestId: string) => {
    await approveAccessRequest.mutateAsync(requestId);
  };

  const handleReject = async (requestId: string) => {
    await rejectAccessRequest.mutateAsync(requestId);
  };

  // Filtrage côté client pour la recherche (si l'API ne supporte pas la recherche)
  const filteredRequests = requests.filter(
    (req: DemandeAccesGroupeOut) =>
      req.demandeur.nom_complet
        .toLowerCase()
        .includes(searchDebounced.toLowerCase()) ||
      req.message?.toLowerCase().includes(searchDebounced.toLowerCase()),
  );

  return (
    <div className="space-y-4 md:space-y-6 max-w-3xl mx-2 sm:mx-auto">
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-center mt-4">
        <InputGroup className="max-w-xs">
          <InputGroupInput
            placeholder="Rechercher un membre..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
          <InputGroupAddon>
            <Search className="h-4 w-4" />
          </InputGroupAddon>
        </InputGroup>

        <Select
          value={status}
          onValueChange={(value: "en_attente" | "approuve" | "refuse") => {
            setStatus(value);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="en_attente">En attente</SelectItem>
            <SelectItem value="approuve">Approuvées</SelectItem>
            <SelectItem value="refuse">Refusées</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="text-sm text-muted-foreground text-center">
        {pagination.totalItems} résultat{pagination.totalItems > 1 ? "s" : ""}
      </div>

      <div className="grid grid-cols-1 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <MemberAccessCardSkeleton key={i} />
          ))
        ) : filteredRequests.length > 0 ? (
          filteredRequests.map((demande: DemandeAccesGroupeOut) => (
            <MemberAccessCard
              key={demande.id}
              demande={demande}
              onApprove={handleApprove}
              onReject={handleReject}
              isPending={
                approveAccessRequest.isPending || rejectAccessRequest.isPending
              }
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-muted-foreground bg-muted/50 rounded-lg">
            {searchDebounced
              ? "Aucune demande ne correspond à votre recherche."
              : status === "en_attente"
                ? "Aucune demande en attente."
                : status === "approuve"
                  ? "Aucune demande approuvée."
                  : "Aucune demande refusée."}
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
                const page = index;
                if (page >= 0 && page < pageCount) {
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
                          pagination.pageIndex === pageCount - 1
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        onClick={() => handlePageChange(pageCount - 1)}
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

export default GroupPageRequestsTab;
