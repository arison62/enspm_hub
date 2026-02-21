/* eslint-disable @typescript-eslint/no-explicit-any */
import { useAccessRequestActions, useGroupActions } from "@/api/network/groups";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenuTrigger,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { convertFileToBase64 } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import type { GroupOut } from "@/types/network";
import { router } from "@inertiajs/react";

import {
  Camera,
  Edit3,
  Globe,
  LogOut,
  MessageCircle,
  MoreVertical,
  UserPlus,
  Users,
  X,
  Lock,
} from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

interface GroupPageHeaderProps {
  groupe: GroupOut;
  form: {
    nom: string;
    description: string;
    type_acces: "public" | "prive";
    status: "actif" | "inactif";
    est_ferme: boolean;
    image_base64: string;
  };
  setForm: React.Dispatch<
    React.SetStateAction<{
      nom: string;
      description: string;
      type_acces: "public" | "prive";
      status: "actif" | "inactif";
      est_ferme: boolean;
      image_base64: string;
    }>
  >;
  editing: boolean;
}

interface LoadingState {
  joining: boolean;
  leaving: boolean;
  editing: boolean;
  cancelRequest: boolean;
}

export default function GroupPageHeader({
  groupe,
  form,
  setForm,
  editing,
}: GroupPageHeaderProps) {
  const { updateGroup, leaveGroup, joinPublicGroup } = useGroupActions();
  const { cancelAccessRequest, createAccessRequest } =
    useAccessRequestActions();

  const imageRef = useRef<HTMLInputElement>(null);
  const isSiteAdmin = useAuthStore((state) => state.isAdmin);

  /* ================= DATA ================= */

  const {
    id,
    nom,
    image_url,
    type_acces,
    is_admin,
    status,
    pending_request,
    is_member,
    est_ferme,
    has_user_pending_request,
    createur,
    nombre_membres,
    conversation_id,
  } = groupe;

  const isInactive = status === "inactif";

  /* ================= STATE ================= */

  const [editOpen, setEditOpen] = useState(false);

  const [loading, setLoading] = useState<LoadingState>({
    joining: false,
    leaving: false,
    editing: editing,
    cancelRequest: false,
  });

  const permissions = {
    canLeave: est_ferme,
    canEdit: Boolean(is_admin || isSiteAdmin),
    canSendMessage: Boolean(
      (is_member && !est_ferme && !isInactive) || is_admin,
    ),
    canViewRequests: Boolean(
      (is_admin || isSiteAdmin) &&
      pending_request != null &&
      pending_request > 0,
    ),
  };

  /* ================= HELPERS ================= */

  const setLoad = (key: keyof LoadingState, value: boolean) =>
    setLoading((prev) => ({ ...prev, [key]: value }));

  const showError = (error: any) =>
    toast.error(error?.message ?? "Une erreur est survenue");

  /* ================= ACTIONS ================= */

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoad("editing", true);

    try {
      await updateGroup.mutateAsync({ id, data: form });
      setEditOpen(false);
      toast.success("Groupe mis à jour");
    } catch (error) {
      showError(error);
    } finally {
      setLoad("editing", false);
    }
  };

  const handleLeave = async () => {
    setLoad("leaving", true);

    try {
      await leaveGroup.mutateAsync(id);
      toast.success("Vous avez quitté le groupe");
      router.reload();
    } catch (error) {
      showError(error);
    } finally {
      setLoad("leaving", false);
    }
  };

  const handleJoin = async () => {
    setLoad("joining", true);

    try {
      if (type_acces === "prive") {
        await createAccessRequest.mutateAsync({ groupId: id });
        toast.success("Demande envoyée");
      } else {
        await joinPublicGroup.mutateAsync(id);
        toast.success("Vous avez rejoint le groupe");
      }
    } catch (error) {
      showError(error);
    } finally {
      setLoad("joining", false);
    }
  };

  const handleCancelRequest = async () => {
    setLoad("cancelRequest", true);

    try {
      await cancelAccessRequest.mutateAsync(id);
      toast.success("Demande annulée");
    } catch (error) {
      showError(error);
    } finally {
      setLoad("cancelRequest", false);
    }
  };

  /* ================= IMAGE ================= */

  const handlePhoto = () => {
    imageRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;

    try {
      const base64 = await convertFileToBase64(e.target.files[0]);

      setForm((p) => ({ ...p, image_base64: base64 }));
      await updateGroup.mutateAsync({ id, data: { image_base64: base64 } });
    } catch (error: any) {
      showError(error);
    }
  };

  /* ================= RENDER ================= */

  return (
    <div className="relative">
      {/* Bannière/Cover */}
      <div className="h-48 md:h-64 bg-gradient-to-r from-muted to-muted/50 relative overflow-hidden">
        <div className="absolute inset-0 opacity-30 bg-[url('https://www.transparenttextures.com/patterns/black-thread.png')]" />

        {/* Overlay si inactif */}
        {isInactive && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <Badge variant="secondary" className="text-lg px-4 py-2">
              Groupe Inactif
            </Badge>
          </div>
        )}
      </div>

      {/* Container du contenu */}
      <div className="max-w-6xl mx-auto px-2 sm:px-6 lg:px-8">
        <div className="relative -mt-8 md:-mt-16 mb-6">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Avatar du groupe */}
                <div className="relative shrink-0">
                  <Avatar className="h-24 w-24 md:h-32 md:w-32 border-4 border-background shadow-md">
                    <AvatarImage
                      src={form.image_base64 || image_url || undefined}
                      className="object-cover"
                      alt={nom}
                    />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl md:text-4xl">
                      {nom.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {is_admin && (
                    <Button
                      onClick={handlePhoto}
                      size="icon"
                      variant="secondary"
                      className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full shadow-sm"
                    >
                      <Camera className="h-4 w-4" />
                      <input
                        type="file"
                        accept="image/*"
                        ref={imageRef}
                        onChange={handleFileChange}
                        hidden
                      />
                    </Button>
                  )}
                </div>

                {/* Infos principales */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h1 className="text-2xl md:text-3xl font-bold text-foreground">
                          {form.nom}
                        </h1>
                        {form.type_acces === "prive" && (
                          <Badge variant="secondary" className="gap-1">
                            <Lock className="h-3 w-3" />
                            Privé
                          </Badge>
                        )}
                        {form.type_acces === "public" && (
                          <Badge variant="secondary" className="gap-1">
                            <Globe className="h-3 w-3" />
                            Public
                          </Badge>
                        )}
                      </div>

                      <p className="text-muted-foreground max-w-2xl">
                        {form.description || "Aucune description"}
                      </p>

                      <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                        <span className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          {nombre_membres} membre
                          {nombre_membres > 1 ? "s" : ""}
                        </span>
                        {createur && (
                          <span>
                            Créé par{" "}
                            <span className="font-medium text-foreground">
                              {createur.nom_complet}
                            </span>
                          </span>
                        )}
                        {permissions.canViewRequests && (
                          <Badge variant="destructive" className="gap-1">
                            <UserPlus className="h-3 w-3" />
                            {pending_request} demande
                            {pending_request! > 1 ? "s" : ""}
                          </Badge>
                        )}
                      </div>
                      {form.est_ferme && (
                        <p
                          className="text-muted-foreground text-xs flex 
                        flex-col items-start lg:flex-row lg:items-center gap-1"
                        >
                          {" "}
                          <Badge variant="outline" className="gap-1">
                            <Lock className="h-2 w-2" />
                            Fermé
                          </Badge>
                          Seuls les administrateurs peuvent envoyer des messages
                        </p>
                      )}
                    </div>

                    {/* Actions principales */}
                    <div className="flex items-center gap-2 shrink-0">
                      {!is_member ? (
                        // Non membre
                        has_user_pending_request ? (
                          <Button
                            variant="outline"
                            disabled={loading.cancelRequest}
                            onClick={() => {
                              handleCancelRequest();
                            }}
                            className="gap-2"
                          >
                            <X className="h-4 w-4" />
                            Annuler la demande
                          </Button>
                        ) : (
                          <Button
                            onClick={handleJoin}
                            disabled={loading.joining || isInactive}
                            className="gap-2"
                          >
                            <UserPlus className="h-4 w-4" />
                            {type_acces === "public"
                              ? "Rejoindre"
                              : "Demander à rejoindre"}
                          </Button>
                        )
                      ) : (
                        // Membre
                        <>
                          {permissions.canSendMessage && (
                            <Button
                              className="gap-2"
                              onClick={() =>
                                router.visit(`/chat?group=${conversation_id}`)
                              }
                            >
                              <MessageCircle className="h-4 w-4" />
                              Envoyer un message
                            </Button>
                          )}

                          {permissions.canEdit && (
                            <Dialog open={editOpen} onOpenChange={setEditOpen}>
                              <DialogTrigger asChild>
                                <Button variant="outline" className="gap-2">
                                  <Edit3 className="h-4 w-4" />
                                  Modifier
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-lg">
                                <DialogHeader>
                                  <DialogTitle>Modifier le groupe</DialogTitle>
                                  <DialogDescription>
                                    Modifiez les informations du groupe
                                    ci-dessous.
                                  </DialogDescription>
                                </DialogHeader>
                                <form
                                  onSubmit={handleUpdate}
                                  className="space-y-4 mt-4"
                                >
                                  <div className="space-y-2">
                                    <Label>Nom du groupe</Label>
                                    <Input
                                      value={form.nom}
                                      onChange={(e) =>
                                        setForm((prev) => ({
                                          ...prev,
                                          nom: e.target.value,
                                        }))
                                      }
                                    />
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Description</Label>
                                    <Textarea
                                      value={form.description}
                                      onChange={(e) =>
                                        setForm((prev) => ({
                                          ...prev,
                                          description: e.target.value,
                                        }))
                                      }
                                      rows={4}
                                    />
                                  </div>

                                  <div className="flex justify-end gap-2 pt-4">
                                    <Button
                                      type="button"
                                      variant="outline"
                                      onClick={() => setEditOpen(false)}
                                    >
                                      Annuler
                                    </Button>
                                    <Button
                                      type="submit"
                                      disabled={loading.editing}
                                    >
                                      {loading.editing
                                        ? "Enregistrement..."
                                        : "Enregistrer"}
                                    </Button>
                                  </div>
                                </form>
                              </DialogContent>
                            </Dialog>
                          )}

                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={handleLeave}
                                className="text-destructive"
                              >
                                <LogOut className="h-4 w-4 mr-2" />
                                Quitter le groupe
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
