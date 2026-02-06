import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  MoreVertical,
  Settings,
  Trash2,
  Power,
  PowerOff,
  LogOut,
  Eye,
  UserPlus, // Icône pour les demandes
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

// Interface basée sur ton schéma GroupeOut
export interface GroupData {
  id: string | number;
  nom: string;
  slug: string;
  description: string;
  type_acces: "public" | "prive" | string;
  image_url?: string | null;
  nombre_membres: number;
  pending_request?: number | null; // Nombre de demandes en attente
  has_user_pending_request?: boolean | null; // L'utilisateur a envoyé une demande
  createur?: {
    id: string;
    nom: string;
  } | null;
  est_membre?: boolean | null;
  est_admin?: boolean | null;
  est_actif?: boolean | null;
}

export interface GroupCardProps {
  data?: GroupData;
  isLoading?: boolean;
  className?: string;
  // Props pour les callbacks d'actions
  onJoin?: (groupId: string | number) => Promise<void>;
  onLeave?: (groupId: string | number) => Promise<void>;
  onView?: (group: GroupData) => void;
  onEdit?: (group: GroupData) => void;
  onDelete?: (groupId: string | number) => Promise<void>;
  onToggleActive?: (groupId: string | number, active: boolean) => Promise<void>;
  onViewRequests?: (group: GroupData) => void;
  // Permission globale (super admin du site)
  isSiteAdmin?: boolean;
  isJoining?: boolean;
  isLeaving?: boolean;
}

export const GroupCard = ({
  data,
  className,
  onJoin,
  onLeave,
  onView,
  onEdit,
  onDelete,
  onToggleActive,
  onViewRequests,
  isSiteAdmin = false,
  isLeaving = false,
  isJoining = false,
}: GroupCardProps) => {
  const [imageError, setImageError] = useState(false);

  if (!data) return null;

  const {
    id,
    nom,
    description,
    type_acces,
    image_url,
    nombre_membres,
    pending_request,
    has_user_pending_request,
    createur,
    est_membre,
    est_admin,
    est_actif,
  } = data;

  const isInactive = est_actif === false;
  const canManageGroup = isSiteAdmin || est_admin;
  const showDropdown = canManageGroup || est_membre;
  const canLeave = est_membre;

  const handleJoin = async () => {
    if (onJoin) await onJoin(id);
  };

  const handleLeave = async () => {
    if (onLeave) await onLeave(id);
  };

  const handleView = () => {
    if (onView) onView(data);
  };

  const handleEdit = () => {
    if (onEdit) onEdit(data);
  };

  const handleDelete = async () => {
    if (onDelete) {
      await onDelete(id);
    }
  };

  const handleToggleActive = async () => {
    if (onToggleActive) {
      await onToggleActive(id, !est_actif);
    }
  };

  const handleViewRequests = () => {
    if (onViewRequests) onViewRequests(data);
  };

  // Déterminer le texte et l'état du bouton rejoindre
  const getJoinButtonContent = () => {
    console.log(has_user_pending_request)
    if (isJoining) return "...";
    if (has_user_pending_request) return "Demande envoyée";
    return "Rejoindre";
  };

  const isJoinDisabled =
    isJoining || isInactive || has_user_pending_request;

  return (
    <Card
      className={cn(
        "hover:border-primary/50 transition-all overflow-hidden relative",
        isInactive && "opacity-60 bg-muted/30 border-muted",
        className,
      )}
    >
      {/* Badge statut inactif */}
      {isInactive && (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-gray-200 text-gray-600 text-[10px]"
        >
          Inactif
        </Badge>
      )}

      <CardContent className="p-4 md:p-6">
        <div className="flex gap-4">
          {/* Image du groupe */}
          <div
            className={cn(
              "h-16 w-16 md:h-20 md:w-20 rounded-lg overflow-hidden flex-shrink-0 border bg-muted",
              isInactive && "grayscale",
            )}
          >
            {!imageError && image_url ? (
              <img
                src={image_url}
                alt={nom}
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-primary/10">
                <Users className="h-6 w-6 md:h-8 md:w-8 text-primary/40" />
              </div>
            )}
          </div>

          {/* Contenu */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <div className="min-w-0 flex-1">
                {/* Nom + badges */}
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <h3
                    className={cn(
                      "font-semibold text-base md:text-lg truncate",
                      isInactive && "text-muted-foreground",
                    )}
                  >
                    {nom}
                  </h3>
                  {type_acces === "prive" && (
                    <Badge variant="outline" className="text-[10px] px-1.5 h-5">
                      Privé
                    </Badge>
                  )}
                </div>

                {/* Description */}
                <p
                  className={cn(
                    "text-sm text-muted-foreground mb-2 line-clamp-1 md:line-clamp-2",
                    isInactive && "text-muted-foreground/60",
                  )}
                >
                  {description || "Aucune description"}
                </p>

                {/* Meta infos */}
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {nombre_membres} membre{nombre_membres > 1 ? "s" : ""}
                  </span>
                  {createur && (
                    <span className="hidden sm:inline truncate">
                      par {createur.nom}
                    </span>
                  )}
                </div>
              </div>

              {/* Dropdown menu */}
              {showDropdown && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0 -mr-2"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    {/* Actions membre */}
                    {canLeave && !est_admin && (
                      <>
                        <DropdownMenuItem
                          onClick={handleLeave}
                          disabled={isLeaving}
                          className="text-destructive focus:text-destructive"
                        >
                          <LogOut className="h-4 w-4 mr-2" />
                          {isLeaving ? "Sortie..." : "Quitter le groupe"}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                      </>
                    )}

                    {/* Actions admin du groupe */}
                    {est_admin && (
                      <>
                        <DropdownMenuItem onClick={handleEdit}>
                          <Settings className="h-4 w-4 mr-2" />
                          Gérer le groupe
                        </DropdownMenuItem>

                        {/* Nouveau : Bouton Demandes avec badge */}
                        {pending_request && pending_request > 0 && (
                          <DropdownMenuItem onClick={handleViewRequests}>
                            <UserPlus className="h-4 w-4 mr-2 text-blue-500" />
                            <span>Demandes</span>
                            <Badge
                              variant="destructive"
                              className="ml-auto h-5 min-w-[20px] flex items-center justify-center text-[10px]"
                            >
                              {pending_request}
                            </Badge>
                          </DropdownMenuItem>
                        )}

                        <DropdownMenuSeparator />
                      </>
                    )}

                    {/* Actions super admin du site */}
                    {isSiteAdmin && (
                      <>
                        <DropdownMenuItem onClick={handleToggleActive}>
                          {est_actif ? (
                            <>
                              <PowerOff className="h-4 w-4 mr-2 text-orange-500" />
                              <span className="text-orange-600">
                                Désactiver
                              </span>
                            </>
                          ) : (
                            <>
                              <Power className="h-4 w-4 mr-2 text-green-500" />
                              <span className="text-green-600">Activer</span>
                            </>
                          )}
                        </DropdownMenuItem>

                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" className="text-destructive w-full justify-start">
                              <Trash2 className="h-4 w-4 mr-2" />
                              Supprimer
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent size="sm">
                            <AlertDialogHeader>
                              <AlertDialogTitle>
                                Êtes-vous sûr de vouloir supprimer ce groupe ?
                              </AlertDialogTitle>
                              <AlertDialogDescription>
                                Cette action est irréversible.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Annuler</AlertDialogCancel>
                              <AlertDialogAction
                                variant={"destructive"}
                                onClick={handleDelete}
                              >
                                Supprimer
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>

            {/* Boutons d'action - TOUS LES UTILISATEURS VOIENT CES BOUTONS */}
            <div className="flex gap-2 mt-4">
              {/* Bouton Voir - toujours visible pour tout le monde */}
              <Button
                variant="outline"
                className="text-xs sm:text-sm flex-1"
                onClick={handleView}
              >
                <Eye className="h-4 w-4 mr-2 hidden sm:inline" />
                Voir
              </Button>

              {/* Boutons conditionnels selon le statut */}
              {est_membre ? (
                // Membre du groupe (mais pas admin) peut quitter
                !est_admin &&
                canLeave && (
                  <Button
                    variant="outline"
                    className="text-xs sm:text-sm text-destructive hover:bg-destructive/10 flex-1"
                    onClick={handleLeave}
                    disabled={isLeaving}
                  >
                    <LogOut className="h-4 w-4 mr-2 hidden sm:inline" />
                    {isLeaving ? "..." : "Quitter"}
                  </Button>
                )
              ) : (
              
                <Button
                  className={cn(
                    "flex-1 h-9 text-xs sm:text-sm",
                    has_user_pending_request &&
                      "bg-muted text-muted-foreground hover:bg-muted cursor-not-allowed",
                  )}
                  onClick={handleJoin}
                  disabled={isJoinDisabled}
                >
                  {getJoinButtonContent()}
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Skeleton exporté séparément pour usage direct
export const GroupCardSkeleton = () => (
  <Card className="hover:border-primary/50 transition-all overflow-hidden">
    <CardContent className="p-4 md:p-6">
      <div className="flex gap-4">
        <Skeleton className="h-16 w-16 md:h-20 md:w-20 rounded-lg shrink-0" />
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-8 w-8 shrink-0 rounded-md" />
          </div>
          <div className="flex gap-2 mt-4">
            <Skeleton className="h-9 flex-1" />
            <Skeleton className="h-9 flex-1" />
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);
