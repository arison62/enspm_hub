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
  MoreVertical,
  Mail,
  Trash2,
  CheckCircle,
  MapPin,
  GraduationCap,
  ExternalLink,
  Shield,
  XCircle,
} from "lucide-react";
import { cn, getAvatarFallback } from "@/lib/utils";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { ProfilOut } from "@/types/user";

export interface MentorProfile extends ProfilOut {
  est_valide?: boolean | null;
  est_actif?: boolean | null;
  date_validation?: string | null;
  valide_par?: {
    id: string;
    nom_complet: string;
  } | null;

  est_proprietaire?: boolean;
}

export interface MentorCardProps {
  data?: MentorProfile;
  isLoading?: boolean;
  className?: string;

  // Actions
  onContact?: (mentor: MentorProfile) => void;
  onValidate?: (mentorId: string) => Promise<void>; // Admin uniquement
  onReject?: (mentorId: string) => Promise<void>; // Admin uniquement
  onView?: (mentor: MentorProfile) => void;
  onEdit?: (mentor: MentorProfile) => void;
  onDelete?: (mentorId: string) => Promise<void>; // Admin ou propriétaire

  // États
  isSiteAdmin?: boolean;
  isCurrentUser?: boolean; // Si c'est le profil de l'utilisateur connecté
  isContacting?: boolean;
  isValidating?: boolean;
  isRejecting?: boolean;
  isDeleting?: boolean;
}

/* ================= COMPONENT ================= */

export const MentorCard = ({
  data,
  className,
  onContact,
  onValidate,
  onReject,
  onView,
  onEdit,
  onDelete,
  isSiteAdmin = false,
  isCurrentUser = false,
  isContacting = false,
  isValidating = false,
  isRejecting = false,
  isDeleting = false,
}: MentorCardProps) => {

  if (!data) return null;

  const {
    id,
    nom_complet,
    annee_sortie,
    domaine,
    bio,
    photo_profil,
    pays_nom,
    ville,
    est_valide,
    est_actif,
  } = data;

  /* ================= PERMISSIONS ================= */
  const permissions = {
    // Validation : admin uniquement et profil en attente
    canValidate: isSiteAdmin && est_valide === false,
    canReject: isSiteAdmin && est_valide === false,

    // Suppression : admin OU propriétaire
    canDelete: isSiteAdmin || isCurrentUser,

    // Édition : propriétaire uniquement (ou admin)
    canEdit: isCurrentUser || isSiteAdmin,

    // Contact : tout le monde sauf soi-même
    canContact: !isCurrentUser,

    // Voir détails : tout le monde
    canView: true,
  };

  const showDropdown =
    permissions.canDelete || permissions.canEdit || permissions.canValidate;
  const isPendingValidation = est_valide === false;
  const isInactive = est_actif === false;


  /* ================= ACTIONS ================= */

  const handleContact = () => {
    if (onContact) onContact(data);
  };

  const handleValidate = async () => {
    if (onValidate) await onValidate(id);
  };

  const handleReject = async () => {
    if (onReject) await onReject(id);
  };

  const handleView = () => {
    if (onView) onView(data);
  };

  const handleEdit = () => {
    if (onEdit) onEdit(data);
  };

  const handleDelete = async () => {
    if (onDelete) await onDelete(id);
  };

  /* ================= RENDER ================= */

  return (
    <Card
      className={cn(
        "hover:border-primary/50 transition-all overflow-hidden relative",
        isInactive && "opacity-60 bg-muted/30 border-muted",
        isPendingValidation && "border-yellow-400/50 bg-yellow-50/10",
        className,
      )}
    >
      {/* Badges de statut */}
      {isPendingValidation && (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-yellow-100 text-yellow-700 text-[10px] border-yellow-200"
        >
          En attente
        </Badge>
      )}

      {isInactive && (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-gray-200 text-gray-600 text-[10px]"
        >
          Inactif
        </Badge>
      )}

      {!est_valide && est_valide !== false && (
        <Badge
          variant="secondary"
          className="absolute top-2 right-2 bg-blue-100 text-blue-700 text-[10px]"
        >
          Profil incomplet
        </Badge>
      )}

      <CardContent className="p-4 md:p-6">
        <div className="flex gap-4">
          {/* Avatar */}

          <Avatar>
            <AvatarImage src={photo_profil ?? ""} alt={nom_complet} />
            <AvatarFallback>{getAvatarFallback(nom_complet)}</AvatarFallback>
          </Avatar>

          {/* CONTENT */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-2">
              <div className="min-w-0 flex-1">
                {/* TITLE */}
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <h3
                    className={cn(
                      "font-semibold text-base md:text-lg truncate",
                      isInactive && "text-muted-foreground",
                    )}
                  >
                    {nom_complet}
                  </h3>
                </div>

                {/* MÉTIER / DOMAINE */}
                {domaine && (
                  <p className="text-sm font-medium text-primary mb-1">
                    {domaine.nom}
                  </p>
                )}

                {/* BIO */}
                <p
                  className={cn(
                    "text-sm text-muted-foreground mb-2 line-clamp-1 md:line-clamp-2",
                    isInactive && "text-muted-foreground/60",
                  )}
                >
                  {bio || "Aucune biographie disponible"}
                </p>

                {/* META INFO */}
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                  {/* Promotion */}
                  {annee_sortie && (
                    <span className="flex items-center gap-1">
                      <GraduationCap className="h-3 w-3" />
                      Promo {annee_sortie.annee}
                    </span>
                  )}

                  {/* Localisation */}
                  {(ville || pays_nom) && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {[ville, pays_nom].filter(Boolean).join(", ")}
                    </span>
                  )}
                </div>
              </div>

              {/* DROPDOWN */}
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

                  <DropdownMenuContent align="end" className="w-56">
                    {/* Actions Admin - Validation */}
                    {permissions.canValidate && (
                      <>
                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                          Administration
                        </div>

                        <DropdownMenuItem
                          onClick={handleValidate}
                          disabled={isValidating}
                          className="text-green-600 focus:text-green-600"
                        >
                          <CheckCircle className="h-4 w-4 mr-2" />
                          {isValidating ? "Validation..." : "Valider le profil"}
                        </DropdownMenuItem>

                        {onReject && (
                          <DropdownMenuItem
                            onClick={handleReject}
                            disabled={isRejecting}
                            className="text-orange-600 focus:text-orange-600"
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            {isRejecting ? "Rejet..." : "Rejeter"}
                          </DropdownMenuItem>
                        )}

                        <DropdownMenuSeparator />
                      </>
                    )}

                    {/* Édition */}
                    {permissions.canEdit && (
                      <DropdownMenuItem onClick={handleEdit}>
                        <Shield className="h-4 w-4 mr-2" />
                        Modifier le profil
                      </DropdownMenuItem>
                    )}

                    {/* Suppression - Admin ou Propriétaire */}
                    {permissions.canDelete && (
                      <>
                        <DropdownMenuSeparator />

                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <DropdownMenuItem
                              onSelect={(e) => e.preventDefault()}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Supprimer le profil
                            </DropdownMenuItem>
                          </AlertDialogTrigger>

                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>
                                Supprimer ce profil mentor ?
                              </AlertDialogTitle>
                              <AlertDialogDescription>
                                Cette action est irréversible. Toutes les
                                données associées seront perdues.
                                {isCurrentUser &&
                                  !isSiteAdmin &&
                                  " Vous perdrez l'accès à votre compte."}
                              </AlertDialogDescription>
                            </AlertDialogHeader>

                            <AlertDialogFooter>
                              <AlertDialogCancel>Annuler</AlertDialogCancel>
                              <AlertDialogAction
                                variant="destructive"
                                onClick={handleDelete}
                                disabled={isDeleting}
                              >
                                {isDeleting ? "Suppression..." : "Supprimer"}
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

            {/* ACTION BUTTONS */}
            <div className="flex gap-2 mt-4">
              <Button
                variant="outline"
                className="text-xs sm:text-sm flex-1"
                onClick={handleView}
              >
                <ExternalLink className="h-4 w-4 mr-2 hidden sm:inline" />
                Voir profil
              </Button>

              {/* Bouton Contacter - caché pour soi-même */}
              {permissions.canContact && (
                <Button
                  className="flex-1 h-9 text-xs sm:text-sm"
                  onClick={handleContact}
                  disabled={isContacting || isPendingValidation || isInactive}
                  title={
                    isPendingValidation
                      ? "En attente de validation"
                      : isInactive
                        ? "Compte inactif"
                        : ""
                  }
                >
                  <Mail className="h-4 w-4 mr-2 hidden sm:inline" />
                  {isContacting ? "Envoi..." : "Contacter"}
                </Button>
              )}

              {/* Si c'est mon profil, bouton "Mon profil" désactivé ou "Modifier" */}
              {isCurrentUser && (
                <Button
                  variant="secondary"
                  className="flex-1 h-9 text-xs sm:text-sm"
                  onClick={handleEdit}
                >
                  <Shield className="h-4 w-4 mr-2 hidden sm:inline" />
                  Mon profil
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/* ================= SKELETON ================= */

export const MentorCardSkeleton = () => (
  <Card className="hover:border-primary/50 transition-all overflow-hidden">
    <CardContent className="p-4 md:p-6">
      <div className="flex gap-4">
        {/* Avatar Skeleton */}
        <Skeleton className="h-16 w-16 md:h-20 md:w-20 rounded-full shrink-0" />

        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              {/* Titre + badges */}
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-5 w-20" />
              </div>

              {/* Domaine */}
              <Skeleton className="h-4 w-32" />

              {/* Bio */}
              <Skeleton className="h-4 w-full" />

              {/* Meta info */}
              <div className="flex gap-3">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>

            {/* Menu skeleton */}
            <Skeleton className="h-8 w-8 shrink-0 rounded-md" />
          </div>

          {/* Buttons */}
          <div className="flex gap-2 mt-4">
            <Skeleton className="h-9 flex-1" />
            <Skeleton className="h-9 flex-1" />
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);

/* ================= EXPORTS ================= */

export default MentorCard;
