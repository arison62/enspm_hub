import React, { useState, useEffect } from "react";
import {
  Search,
  Shield,
  MoreVertical,
  Crown,
  UserX,
} from "lucide-react";
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
  useGetGroupMembers,
  useGroupMemberActions,
} from "@/api/network/groups";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import type { MembreGroupeOut } from "@/types/network";

interface PaginationType {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}

interface MemberCardProps {
  membre: MembreGroupeOut;
  canManage: boolean;
  currentUserId?: string;
  groupId: string;
  onPromote: (membreId: string) => void;
  onRevoke: (membreId: string) => void;
  onRemove: (membreId: string) => void;
  isPendingPromote: boolean;
  isPendingRemove: boolean;
}

const MemberCardSkeleton: React.FC = () => (
  <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm animate-pulse">
    <div className="flex items-center gap-4">
      <div className="h-12 w-12 rounded-full bg-muted" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-1/3 bg-muted rounded" />
        <div className="h-3 w-1/2 bg-muted rounded" />
      </div>
      <div className="h-8 w-8 bg-muted rounded-full" />
    </div>
  </div>
);

const MemberCard: React.FC<MemberCardProps> = ({
  membre,
  canManage,
  currentUserId,
  onPromote,
  onRevoke,
  onRemove,
  isPendingPromote,
  isPendingRemove,
}) => {
  const isCurrentUser = membre.profil.id === currentUserId;
  const isAdmin = membre.role === "admin";

  return (
    <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Avatar className="h-12 w-12 shrink-0">
            <AvatarImage
              src={membre.profil.photo_profil || ""}
              className="object-cover"
            />
            <AvatarFallback>
              {membre.profil.nom_complet
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()}
            </AvatarFallback>
          </Avatar>
          {isAdmin && (
            <div className="absolute -bottom-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
              <Shield className="h-3 w-3" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-base truncate">
              {membre.profil.nom_complet}
            </h3>
            {isAdmin && (
              <Badge variant="default" className="text-xs">
                <Shield className="h-3 w-3 mr-1" />
                Admin
              </Badge>
            )}
            {isCurrentUser && (
              <Badge variant="outline" className="text-xs">
                Vous
              </Badge>
            )}
          </div>

          {membre.profil.bio && (
            <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
              {membre.profil.bio}
            </p>
          )}

          <p className="text-xs text-muted-foreground mt-1">
            Membre depuis le{" "}
            {new Date(membre.date_membre).toLocaleDateString("fr-FR")}
          </p>
        </div>

        {canManage && !isCurrentUser && (
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="shrink-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-2" align="end">
              <div className="space-y-1">
                {!isAdmin ? (
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm"
                    onClick={() => onPromote(membre.profil.id)}
                    disabled={isPendingPromote}
                  >
                    <Crown className="h-4 w-4 mr-2 text-amber-500" />
                    Nommer administrateur
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm"
                    onClick={() => onRevoke(membre.profil.id)}
                    disabled={isPendingPromote}
                  >
                    <Shield className="h-4 w-4 mr-2 text-orange-500" />
                    Révoquer admin
                  </Button>
                )}

                <div className="h-px bg-border my-1" />

                <Button
                  variant="ghost"
                  className="w-full justify-start text-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={() => onRemove(membre.profil.id)}
                  disabled={isPendingRemove}
                >
                  <UserX className="h-4 w-4 mr-2" />
                  Retirer du groupe
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        )}
      </div>
    </div>
  );
};

interface GroupPageMembersTabProps {
  groupId: string;
  canManage: boolean;
  currentUserId?: string;
}

const GroupPageMembersTab: React.FC<GroupPageMembersTabProps> = ({
  groupId,
  canManage,
  currentUserId,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const searchDebounced = useDebounce(searchQuery, 300);

  const [pagination, setPagination] = useState<PaginationType>({
    pageIndex: 0,
    pageSize: 12,
    totalItems: 0,
  });

  const { data, isLoading } = useGetGroupMembers({
    groupId,
    query: searchDebounced,
    pagination: {
      pageIndex: pagination.pageIndex,
      pageSize: pagination.pageSize,
    },
  });

  const { promoteMemberToAdmin, removeMemberFromGroup, revokeAdminStatus } =
    useGroupMemberActions();

  // Mise à jour du total quand les données arrivent
  useEffect(() => {
    if (data?.meta?.total_items !== undefined) {
      setPagination((prev) => ({
        ...prev,
        totalItems: data.meta.total_items,
      }));
    }
  }, [data?.meta?.total_items]);



  const members = data?.items || [];
  console.log("members", members);
  const pageCount = Math.ceil(pagination.totalItems / pagination.pageSize);

  const handlePageChange = (page: number) => {
    setPagination((prev) => ({
      ...prev,
      pageIndex: page,
    }));
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
  };

  const handlePromote = async (membreId: string) => {
    await promoteMemberToAdmin.mutateAsync({ groupId, membreId });
  };

  const handleRevoke = async (membreId: string) => {
    await revokeAdminStatus.mutateAsync({ groupId, membreId });
  };

  const handleRemove = async (membreId: string) => {
    await removeMemberFromGroup.mutateAsync({ groupId, membreId });
  };

  return (
    <div className="space-y-4 md:space-y-6 max-w-3xl mx-2 sm:mx-auto">
      <div className="relative flex justify-center mt-4">
        <InputGroup className="max-w-xs">
          <InputGroupInput
            placeholder="Rechercher un membre..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
          <InputGroupAddon>
            <Search className="h-4 w-4" />
          </InputGroupAddon>
          <InputGroupAddon align="inline-end">
            {pagination.totalItems} résultat
            {pagination.totalItems > 1 ? "s" : ""}
          </InputGroupAddon>
        </InputGroup>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <MemberCardSkeleton key={i} />
          ))
        ) : members.length > 0 ? (
          members.map((membre: MembreGroupeOut) => (
            <MemberCard
              key={membre.id}
              membre={membre}
              canManage={canManage}
              currentUserId={currentUserId}
              groupId={groupId}
              onPromote={handlePromote}
              onRevoke={handleRevoke}
              onRemove={handleRemove}
              isPendingPromote={
                promoteMemberToAdmin.isPending || revokeAdminStatus.isPending
              }
              isPendingRemove={removeMemberFromGroup.isPending}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-muted-foreground bg-muted/50 rounded-lg">
            {searchDebounced
              ? "Aucun membre ne correspond à votre recherche."
              : "Aucun membre dans ce groupe."}
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

export default GroupPageMembersTab;
