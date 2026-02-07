import { useEffect, useState, type ReactNode } from "react";
import { router, usePage, Deferred } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Users,
  MessageCircle,
  Settings,
  Send,
} from "lucide-react";
import type { GroupOut } from "@/types/network";
import AppLayout from "@/components/layouts/app-layout";
import GroupeSkeleton from "../components/network/group-page-skeleton";
import GroupPageHeader from "../components/network/group-page-header";
import GroupPageSettingsTab from "../components/network/group-page-settings-tab";
import GroupPageRequestsTab from "../components/network/group-page-requests-tab";
import GroupPageMembersTab from "../components/network/group-page-members-tab";
import { useAuthStore } from "@/stores/authStore";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";

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
  };
}

type TabType = "accueil" | "membres" | "discussion" | "parametres" | "demandes";

/**
 * Gets the current tab from the URL parameters.
 * @returns The current tab, strongly typed as "accueil" | "membres" | "discussion" | "parametres".
 */
function getTabURLParams(): TabType {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab") as TabType | null;
  return tab ?? "accueil";
}

export function GroupeContent({ groupe }: GroupeContentProps) {
  const isSiteAdmin = useAuthStore((state) => state.isAdmin);
  const profileId = useAuthStore((state) => state.user?.profil.id);
  const [activeTab, setActiveTab] = useState(getTabURLParams());
  const [editing] = useState(false);

  const {
    id,
    description,
    type_acces,
    nombre_membres,
    pending_request,
    is_member,
    is_admin,
    est_actif,
  } = groupe;

  const [form, setForm] = useState({
    nom: groupe.nom,
    description: groupe.description,
    type_acces: groupe.type_acces,
    status: groupe.status,
    est_ferme: groupe.est_ferme,
    image_base64: "",
  });
  const permissions = {
    can_view_members:
      type_acces === "public" || is_member || is_admin || isSiteAdmin,
    can_mange_members: is_admin || isSiteAdmin,
  };

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", activeTab);
    window.history.replaceState({}, "", url.href);
  }, [activeTab]);
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section - Style LinkedIn */}

      <GroupPageHeader
        groupe={groupe}
        form={form}
        setForm={setForm}
        editing={editing}
      />

      {/* Tabs Navigation - Style LinkedIn */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as TabType)}
          className="space-y-6"
        >
          <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent overflow-x-auto scrollbar-none">
            <TabsTrigger
              value="accueil"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
            >
              Accueil
            </TabsTrigger>

            <TabsTrigger
              value="membres"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
            >
              Membres
              <Badge variant="secondary" className="ml-2">
                {nombre_membres}
              </Badge>
            </TabsTrigger>

            {is_admin && (
              <TabsTrigger
                value="demandes"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-3"
              >
                Demandes
                {pending_request !== undefined && pending_request > 0 && (
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
                    {/* {visibleMembers.length > 0 ? (
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
                    )} */}
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
            {permissions.can_view_members ? (
              <GroupPageMembersTab
                groupId={id}
                canManage={permissions.can_mange_members}
                currentUserId={profileId}
              />
            ) : (
              <Empty>
                <EmptyHeader>
                  <EmptyMedia>
                    <Users className="w-16 h-16 text-muted-foreground" />
                  </EmptyMedia>
                  <EmptyTitle>Membres</EmptyTitle>
                  <EmptyDescription>
                    Les membres du groupe peuvent voir les membres si
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            )}
          </TabsContent>

          {/* Contenu Demandes (Admin only) */}
          <TabsContent value="demandes" className="mt-6">
            <GroupPageRequestsTab groupId={id} />
          </TabsContent>

          {/* Contenu Paramètres (Admin only) */}
          <TabsContent value="parametres" className="mt-6">
            <GroupPageSettingsTab
              groupe={groupe}
              form={form}
              setForm={setForm}
            />
          </TabsContent>
        </Tabs>
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
NetworkGroup.layout = (page: ReactNode) => <AppLayout>{page}</AppLayout>;

export default NetworkGroup;

interface GroupPageProps {
  groupe: GroupOut;
}

const NetworkContentWrapper = () => {
  const { groupe } = usePage().props as unknown as GroupPageProps;
  return (
    <GroupeContent
      groupe={{
        membres: [],
        ...groupe,
      }}
    />
  );
};
