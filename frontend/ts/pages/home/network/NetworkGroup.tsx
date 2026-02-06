// components/groupe/groupe-content.tsx
import { useEffect, useState, type ReactNode } from "react";
import { useForm, router, usePage, Deferred } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Users,
  MessageCircle,
  Settings,
  MoreVertical,
  Lock,
  Globe,
  UserPlus,
  LogOut,
  Edit3,
  Camera,
  Shield,
  X,
  Send,
  Trash2,
} from "lucide-react";
import type { GroupOut } from "@/types/network";
import AppLayout from "@/components/layouts/app-layout";

interface Member {
  id: string;
  nom: string;
  avatar?: string;
  role: "admin" | "membre";
  joined_at: string;
}

interface GroupeContentProps {
  groupe: GroupOut & {
    membres: Member[];
    can_view_members: boolean;
  };
  authUser: {
    id: string;
    isSiteAdmin: boolean;
  };
}

/**
 * Gets the current tab from the URL parameters.
 * @returns The current tab, strongly typed as "accueil" | "membres" | "discussion" | "parametres".
 */
function getTabURLParams(): "accueil" | "membres" | "discussion" | "parametres" {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab") as "accueil" | "membres" | "discussion" | "parametres" | null;
  return tab ?? "accueil";
}

export function GroupeContent({ groupe, authUser }: GroupeContentProps) {
  const [activeTab, setActiveTab] = useState(getTabURLParams());
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);


  const {
    id,
    nom,
    description,
    type_acces,
    image_url,
    nombre_membres,
    pending_request,
    has_user_pending_request,
    is_member,
    is_admin,
    est_actif,
    membres,
    can_view_members,
    createur,
  } = groupe;

  const isInactive = est_actif === false;

  // Formulaires Inertia
  const joinForm = useForm({});
  const leaveForm = useForm({});
  const cancelRequestForm = useForm({});
  const updateForm = useForm({
    nom,
    description,
    image_url: image_url || "",
    est_actif,
    membres_seuls_ecrire: false, // à ajouter dans l'interface si besoin
  });

  const handleJoin = () => {
    if (type_acces === "public") {
      joinForm.post(`/groupes/${id}/rejoindre`);
    } else {
      joinForm.post(`/groupes/${id}/demander-rejoindre`);
    }
  };

  const handleCancelRequest = () => {
    cancelRequestForm.post(`/groupes/${id}/annuler-demande`);
  };

  const handleLeave = () => {
    if (confirm("Voulez-vous vraiment quitter ce groupe ?")) {
      leaveForm.delete(`/groupes/${id}/quitter`);
    }
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    updateForm.post(`/groupes/${id}/modifier`, {
      onSuccess: () => setIsEditDialogOpen(false),
    });
  };

  // Filtrer les membres visibles
  const visibleMembers =
    can_view_members || is_member || authUser.isSiteAdmin ? membres : [];
  useEffect(()=>{
    const url = new URL(window.location.href);
    url.searchParams.set("tab", activeTab);
    window.history.replaceState({}, "", url.href);
  },[activeTab])
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section - Style LinkedIn */}
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative -mt-12 md:-mt-16 mb-6">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row gap-6">
                  {/* Avatar du groupe */}
                  <div className="relative shrink-0">
                    <Avatar className="h-24 w-24 md:h-32 md:w-32 border-4 border-background shadow-md">
                      <AvatarImage src={image_url || undefined} alt={nom} />
                      <AvatarFallback className="bg-primary/10 text-primary text-2xl md:text-4xl">
                        {nom.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    {is_admin && (
                      <Button
                        size="icon"
                        variant="secondary"
                        className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full shadow-sm"
                      >
                        <Camera className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  {/* Infos principales */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 flex-wrap">
                          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
                            {nom}
                          </h1>
                          {type_acces === "prive" && (
                            <Badge variant="secondary" className="gap-1">
                              <Lock className="h-3 w-3" />
                              Privé
                            </Badge>
                          )}
                          {type_acces === "public" && (
                            <Badge variant="secondary" className="gap-1">
                              <Globe className="h-3 w-3" />
                              Public
                            </Badge>
                          )}
                          {is_admin && (
                            <Badge variant="default" className="gap-1">
                              <Shield className="h-3 w-3" />
                              Admin
                            </Badge>
                          )}
                        </div>

                        <p className="text-muted-foreground max-w-2xl">
                          {description || "Aucune description"}
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
                          {pending_request &&
                            pending_request > 0 &&
                            is_admin && (
                              <Badge variant="destructive" className="gap-1">
                                <UserPlus className="h-3 w-3" />
                                {pending_request} demande
                                {pending_request > 1 ? "s" : ""}
                              </Badge>
                            )}
                        </div>
                      </div>

                      {/* Actions principales */}
                      <div className="flex items-center gap-2 shrink-0">
                        {!is_member ? (
                          // Non membre
                          has_user_pending_request ? (
                            <Button
                              variant="outline"
                              onClick={handleCancelRequest}
                              disabled={cancelRequestForm.processing}
                              className="gap-2"
                            >
                              <X className="h-4 w-4" />
                              Annuler la demande
                            </Button>
                          ) : (
                            <Button
                              onClick={handleJoin}
                              disabled={joinForm.processing || isInactive}
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
                            <Button className="gap-2">
                              <MessageCircle className="h-4 w-4" />
                              Envoyer un message
                            </Button>

                            {is_admin && (
                              <Dialog
                                open={isEditDialogOpen}
                                onOpenChange={setIsEditDialogOpen}
                              >
                                <DialogTrigger asChild>
                                  <Button variant="outline" className="gap-2">
                                    <Edit3 className="h-4 w-4" />
                                    Modifier
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-lg">
                                  <DialogHeader>
                                    <DialogTitle>
                                      Modifier le groupe
                                    </DialogTitle>
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
                                        value={updateForm.data.nom}
                                        onChange={(e) =>
                                          updateForm.setData(
                                            "nom",
                                            e.target.value,
                                          )
                                        }
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>Description</Label>
                                      <Textarea
                                        value={updateForm.data.description}
                                        onChange={(e) =>
                                          updateForm.setData(
                                            "description",
                                            e.target.value,
                                          )
                                        }
                                        rows={4}
                                      />
                                    </div>
                                    <div className="space-y-2">
                                      <Label>URL de l'image</Label>
                                      <Input
                                        value={updateForm.data.image_url}
                                        onChange={(e) =>
                                          updateForm.setData(
                                            "image_url",
                                            e.target.value,
                                          )
                                        }
                                      />
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <div className="space-y-0.5">
                                        <Label>Groupe actif</Label>
                                        <p className="text-sm text-muted-foreground">
                                          Désactiver pour fermer temporairement
                                          le groupe
                                        </p>
                                      </div>
                                      <Switch
                                        checked={updateForm.data.est_actif}
                                        onCheckedChange={(checked) =>
                                          updateForm.setData(
                                            "est_actif",
                                            checked,
                                          )
                                        }
                                      />
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <div className="space-y-0.5">
                                        <Label>
                                          Membres seuls peuvent écrire
                                        </Label>
                                        <p className="text-sm text-muted-foreground">
                                          Seuls les admins pourront publier du
                                          contenu
                                        </p>
                                      </div>
                                      <Switch
                                        checked={
                                          updateForm.data.membres_seuls_ecrire
                                        }
                                        onCheckedChange={(checked) =>
                                          updateForm.setData(
                                            "membres_seuls_ecrire",
                                            checked,
                                          )
                                        }
                                      />
                                    </div>
                                    <div className="flex justify-end gap-2 pt-4">
                                      <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() =>
                                          setIsEditDialogOpen(false)
                                        }
                                      >
                                        Annuler
                                      </Button>
                                      <Button
                                        type="submit"
                                        disabled={updateForm.processing}
                                      >
                                        {updateForm.processing
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
                                {is_admin &&
                                  pending_request &&
                                  pending_request > 0 && (
                                    <DropdownMenuItem
                                      onClick={() => setActiveTab("demandes")}
                                    >
                                      <UserPlus className="h-4 w-4 mr-2 text-blue-500" />
                                      Voir les demandes ({pending_request})
                                    </DropdownMenuItem>
                                  )}
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

      {/* Tabs Navigation - Style LinkedIn */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
            <TabsTrigger
              value="accueil"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
            >
              Accueil
            </TabsTrigger>
            {(can_view_members || is_member || authUser.isSiteAdmin) && (
              <TabsTrigger
                value="membres"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
              >
                Membres
                <Badge variant="secondary" className="ml-2">
                  {nombre_membres}
                </Badge>
              </TabsTrigger>
            )}
            {is_admin && (
              <TabsTrigger
                value="demandes"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
              >
                Demandes
                {pending_request && pending_request > 0 && (
                  <Badge variant="destructive" className="ml-2">
                    {pending_request}
                  </Badge>
                )}
              </TabsTrigger>
            )}
            {is_admin && (
              <TabsTrigger
                value="parametres"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
              >
                Paramètres
              </TabsTrigger>
            )}
          </TabsList>

          {/* Contenu Accueil */}
          <TabsContent value="accueil" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Colonne principale */}
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">À propos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground whitespace-pre-wrap">
                      {description || "Aucune description disponible."}
                    </p>
                  </CardContent>
                </Card>

                {/* Zone de publication (si membre et permissions) */}
                {is_member && (
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarImage src={undefined} />
                          <AvatarFallback>U</AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <Button
                            variant="outline"
                            className="w-full justify-start text-muted-foreground h-12"
                            onClick={() =>
                              router.visit(`/groupes/${id}/publier`)
                            }
                          >
                            <Send className="h-4 w-4 mr-2" />
                            Commencer une publication...
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Feed de publications (placeholder) */}
                <div className="text-center py-12 text-muted-foreground">
                  <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>Aucune publication pour le moment</p>
                </div>
              </div>

              {/* Colonne latérale */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Membres
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {visibleMembers.length > 0 ? (
                      <div className="space-y-3">
                        {visibleMembers.slice(0, 5).map((member) => (
                          <div
                            key={member.id}
                            className="flex items-center gap-3"
                          >
                            <Avatar className="h-8 w-8">
                              <AvatarImage src={member.avatar} />
                              <AvatarFallback>
                                {member.nom.slice(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">
                                {member.nom}
                              </p>
                              {member.role === "admin" && (
                                <p className="text-xs text-muted-foreground">
                                  Admin
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                        {visibleMembers.length > 5 && (
                          <Button
                            variant="link"
                            className="w-full mt-2"
                            onClick={() => setActiveTab("membres")}
                          >
                            Voir tous les membres
                          </Button>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        {type_acces === "prive" && !is_member
                          ? "Les membres sont visibles uniquement par les membres du groupe"
                          : "Aucun membre"}
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Stats admin */}
                {is_admin && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Administration</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">
                          Statut
                        </span>
                        <Badge variant={est_actif ? "default" : "secondary"}>
                          {est_actif ? "Actif" : "Inactif"}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">
                          Type
                        </span>
                        <span className="text-sm font-medium capitalize">
                          {type_acces === "prive" ? "Privé" : "Public"}
                        </span>
                      </div>
                      <Separator />
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => setActiveTab("parametres")}
                      >
                        <Settings className="h-4 w-4 mr-2" />
                        Gérer le groupe
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Contenu Membres */}
          <TabsContent value="membres" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Tous les membres</CardTitle>
                <CardDescription>
                  {nombre_membres} membre{nombre_membres > 1 ? "s" : ""} dans ce
                  groupe
                </CardDescription>
              </CardHeader>
              <CardContent>
                {visibleMembers.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {visibleMembers.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                      >
                        <Avatar className="h-12 w-12">
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback>
                            {member.nom.slice(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{member.nom}</p>
                          <div className="flex items-center gap-2">
                            {member.role === "admin" && (
                              <Badge variant="secondary" className="text-xs">
                                <Shield className="h-3 w-3 mr-1" />
                                Admin
                              </Badge>
                            )}
                            <span className="text-xs text-muted-foreground">
                              Membre depuis{" "}
                              {new Date(member.joined_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        {is_admin && member.id !== authUser.id && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem className="text-destructive">
                                Retirer du groupe
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Users className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>Aucun membre à afficher</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Contenu Demandes (Admin only) */}
          <TabsContent value="demandes" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Demandes d'adhésion</CardTitle>
                <CardDescription>
                  Gérez les demandes pour rejoindre le groupe
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Liste des demandes à implémenter selon ton backend */}
                <div className="text-center py-12 text-muted-foreground">
                  <UserPlus className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>Aucune demande en attente</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Contenu Paramètres (Admin only) */}
          <TabsContent value="parametres" className="mt-6">
            <div className="max-w-2xl">
              <Card>
                <CardHeader>
                  <CardTitle>Paramètres du groupe</CardTitle>
                  <CardDescription>
                    Modifiez les paramètres avancés du groupe
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Visibilité du groupe</Label>
                        <p className="text-sm text-muted-foreground">
                          {type_acces === "public" ? "Public" : "Privé"}
                        </p>
                      </div>
                      <Badge
                        variant={
                          type_acces === "public" ? "default" : "secondary"
                        }
                      >
                        {type_acces === "public" ? (
                          <Globe className="h-3 w-3 mr-1" />
                        ) : (
                          <Lock className="h-3 w-3 mr-1" />
                        )}
                        {type_acces === "public" ? "Public" : "Privé"}
                      </Badge>
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Notifications</Label>
                        <p className="text-sm text-muted-foreground">
                          Recevoir les notifications du groupe
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator />
                    <div className="pt-4">
                      <Button
                        variant="destructive"
                        className="w-full sm:w-auto"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Supprimer le groupe
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// Skeleton pour le chargement
export function GroupeSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <div className="h-48 md:h-64 bg-muted animate-pulse" />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative -mt-12 md:-mt-16 mb-6">
          <Card className="border-0 shadow-sm">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row gap-6">
                <Skeleton className="h-24 w-24 md:h-32 md:w-32 rounded-full shrink-0" />
                <div className="flex-1 space-y-4">
                  <Skeleton className="h-8 w-64" />
                  <Skeleton className="h-4 w-full max-w-xl" />
                  <Skeleton className="h-4 w-48" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Skeleton className="h-10 w-full max-w-md" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
            </div>
            <div className="space-y-4">
              <Skeleton className="h-64 w-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function NetworkGroup() {
  return (
    <Deferred data="groupe" fallback={<GroupeSkeleton />}>
      <NetworkContentWrapper />
    </Deferred>
  );
}
NetworkGroup.layout = (page : ReactNode) => <AppLayout>{page}</AppLayout>;

export default NetworkGroup;

interface GroupPageProps {
  groupe: GroupOut;
}

const NetworkContentWrapper = () => {
  const { groupe } = usePage().props as unknown as GroupPageProps;
  return (
    <GroupeContent
      authUser={{
        isSiteAdmin: true,
        id: "idn",
      }}
      groupe={{
        membres: [],
        can_view_members: true,
        ...groupe,
      }}
    />
  );
};
