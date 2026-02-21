import React, { useState } from "react";
import { Search, UserPlus, ChevronDown, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useInternalNav } from "@/contexts/internal-nav-context";

// Subpages
import MembersListPage from "./members-list-page";
import GroupsListPage from "./groups-list-page";
import GroupFormPage from "./group-form-page";
import BecomeMentorPage from "./become-mentor-page";
import MentorSearchPage from "./mentor-search-page";
import { useGetUsers } from "@/api/users";
import {
  MemberCard,
  MemberCardSkeleton,
} from "../../components/network/member-card";
import {
  useAccessRequestActions,
  useGetGroups,
  useGroupActions,
} from "@/api/network/groups";
import {
  GroupCard,
  GroupCardSkeleton,
} from "../../components/network/group-card";
import { router } from "@inertiajs/react";
import { useAuthStore } from "@/stores/authStore";

const NetworkHome: React.FC = () => {
  const isSiteAdmin = useAuthStore((state) => state.isAdmin);
  const { joinPublicGroup, leaveGroup, deleteGroup, updateGroup } =
    useGroupActions();
  const { createAccessRequest } = useAccessRequestActions();
  const [activeTab, setActiveTab] = useState("members");
  const {
    data: { items: members },
    isLoading: isLoadingMembers,
  } = useGetUsers({
    columnFilters: [],
    pagination: {
      pageIndex: 0,
      pageSize: 3,
    },
  });
  const {
    data: { items: groups },
    isLoading: isLoadingGroups,
  } = useGetGroups({
    columnFilters: [],
    pagination: {
      pageIndex: 0,
      pageSize: 3,
    },
  });
  const { push } = useInternalNav();

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
    updateGroup.mutateAsync({ id: groupId, data: { status: newStatus } });
  };
  const handleDelete = async (groupId: string) => {
    deleteGroup.mutateAsync(groupId);
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Hero Section - Mentorship CTA */}
      <Card className="overflow-hidden border-none shadow-md bg-gradient-to-br from-primary/5 to-background">
        <div className="flex flex-col md:flex-row">
          <div className="md:w-1/3 h-48 md:h-auto bg-muted relative overflow-hidden">
            <img
              src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800"
              alt="Mentorship"
              className="w-full h-full object-cover opacity-80"
            />
            <div className="absolute inset-0 bg-primary/10" />
          </div>
          <div className="p-6 md:p-10 md:w-2/3 flex flex-col justify-center">
            <Badge
              variant="secondary"
              className="w-fit mb-3 bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border-0 uppercase text-xs font-bold"
            >
              Programme de Mentorat
            </Badge>
            <h1 className="text-2xl md:text-4xl font-bold mb-4 tracking-tight">
              Accélérez votre carrière grâce au mentorat
            </h1>
            <p className="text-muted-foreground text-sm md:text-lg mb-8 max-w-2xl leading-relaxed">
              Connectez-vous avec plus de 5 000 alumni et étudiants pour
              partager vos connaissances, obtenir des conseils et évoluer
              ensemble dans le domaine de l'ingénierie.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                size="lg"
                className="gap-2 h-12 px-8"
                onClick={() => push(MentorSearchPage, "Trouver un mentor")}
              >
                <Search className="h-4 w-4" />
                Trouver un mentor
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="gap-2 h-12 px-8"
                onClick={() => push(BecomeMentorPage, "Devenir mentor")}
              >
                <UserPlus className="h-4 w-4" />
                Devenir mentor
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Content Area */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6 max-w-7xl mx-auto"
      >
        <TabsList className="flex w-full overflow-x-auto bg-transparent border-b rounded-none h-auto p-0 scrollbar-none gap-4 md:gap-8">
          <TabsTrigger
            value="members"
            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold"
          >
            Membres
          </TabsTrigger>
          <TabsTrigger
            value="groups"
            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold"
          >
            Groupes
          </TabsTrigger>
          <TabsTrigger
            value="mentorship"
            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold"
          >
            Mentorat
          </TabsTrigger>
        </TabsList>

        <TabsContent
          value="members"
          className="space-y-4 focus-visible:outline-none focus-visible:ring-0 flex flex-col"
        >
          <div className="grid place-items-center grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
            {isLoadingMembers
              ? Array.from({ length: 3 }).map((_, i) => (
                  <MemberCardSkeleton key={i} />
                ))
              : members.map((member) => (
                  <MemberCard
                    key={member.id}
                    className="w-full"
                    data={{
                      id: member.id,
                      profilId: member.profil.id,
                      name: member.profil.nom_complet,
                      title: member.profil.titre?.titre,
                      bio: member.profil?.bio || undefined,
                      avatar: member.profil.photo_profil || undefined,
                      promo: member.profil.annee_sortie?.libelle || undefined,
                      position:
                        member.profil.poste_actuel?.titre_poste || undefined,
                      company:
                        member.profil.poste_actuel?.nom_entreprise || undefined,
                      slug: member.profil.slug,
                      status_global: member.profil.statut_global,
                    }}
                  />
                ))}
          </div>
          <Button
            variant="ghost"
            className="gap-2 text-primary text-sm h-10 w-fit mx-auto"
            onClick={() => push(MembersListPage, "Tous les membres")}
          >
            Voir tous les membres
            <ChevronDown className="h-4 w-4" />
          </Button>
        </TabsContent>

        <TabsContent
          value="groups"
          className="space-y-4 focus-visible:outline-none"
        >
          <div className="grid place-items-center grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
            {isLoadingGroups ? (
              <GroupCardSkeleton />
            ) : (
              groups.map((group) => (
                <GroupCard
                  className="mx-auto w-full"
                  key={group.id}
                  onView={() => handleGoToPage(group.slug, "accueil")}
                  onLeave={() => handleLeave(group.id)}
                  onJoin={() =>
                    handleJoin(group.id, group.type_acces === "public")
                  }
                  onDelete={() => handleDelete(group.id)}
                  onToggleActive={() =>
                    handleToggleActive(group.id, group.status)
                  }
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
                      ? {
                          id: group.createur.id,
                          nom: group.createur.nom_complet,
                        }
                      : null,
                  }}
                />
              ))
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-2 w-fit mx-auto">
            <Button
              variant="outline"
              className="flex-1 h-10 text-sm w-fit"
              onClick={() => push(GroupsListPage, "Tous les groupes")}
            >
              Voir tous les groupes
            </Button>
            <Button
              className="flex-1 h-10 text-sm gap-2 w-fit"
              onClick={() => push(GroupFormPage, "Créer un groupe")}
            >
              <Plus className="h-4 w-4" />
              Créer un groupe
            </Button>
          </div>
        </TabsContent>

        <TabsContent
          value="mentorship"
          className="space-y-4 focus-visible:outline-none"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="hover:border-primary/50 transition-all border-dashed bg-muted/20 max-w-sm w-full mx-auto">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-bold mb-2">Besoin d'aide ?</h3>
                <p className="text-xs text-muted-foreground mb-4">
                  Trouvez un mentor pour vous guider dans votre parcours.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => push(MentorSearchPage, "Trouver un mentor")}
                >
                  Chercher un mentor
                </Button>
              </CardContent>
            </Card>
            <Card className="hover:border-primary/50 transition-all border-dashed bg-muted/20 max-w-sm w-full mx-auto">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <UserPlus className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-bold mb-2">Voulez-vous aider ?</h3>
                <p className="text-xs text-muted-foreground mb-4">
                  Partagez vos connaissances et devenez mentor dès aujourd'hui.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => push(BecomeMentorPage, "Devenir mentor")}
                >
                  S'inscrire comme mentor
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NetworkHome;
