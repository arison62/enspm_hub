import React, { useState, useEffect } from "react";
import {
  Search,
  MapPin,
  Briefcase,
  BookmarkPlus,
  MessageSquare,
  UserPlus,
  MoreVertical,
  Users,
  Building2,
  ChevronDown,
  Plus,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useInternalNav } from "@/contexts/internal-nav-context";

// Subpages
import MembersListPage from "./members-list-page";
import GroupsListPage from "./groups-list-page";
import GroupFormPage from "./group-form-page";
import BecomeMentorPage from "./become-mentor-page";
import MentorSearchPage from "./mentor-search-page";

// Types
type UserRole = "student" | "alumni";

interface Member {
  id: string;
  name: string;
  position: string;
  company: string;
  promo: string;
  location: string;
  avatar: string;
  isMentor?: boolean;
}

interface Group {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  image: string;
  isJoined: boolean;
}

interface Organization {
  id: string;
  name: string;
  sector: string;
  location: string;
  logo: string;
  alumniCount: number;
}

const NetworkHome: React.FC = () => {
  const [activeTab, setActiveTab] = useState("members");
  const [isLoading, setIsLoading] = useState(true);
  const { push } = useInternalNav();

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 600);
    return () => clearTimeout(timer);
  }, []);

  const mockMembers: Member[] = [
    {
      id: "1",
      name: "Marie Curie",
      position: "Senior Engineer",
      company: "Google",
      promo: "2018",
      location: "Paris, France",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Marie",
      isMentor: true,
    },
    {
      id: "2",
      name: "Jean Dupont",
      position: "Data Scientist",
      company: "Microsoft",
      promo: "2020",
      location: "Lyon, France",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Jean",
    },
  ];

  const mockGroups: Group[] = [
    {
      id: "1",
      name: "Club Robotique",
      description: "Passionate about robotics and automation",
      memberCount: 124,
      image: "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400",
      isJoined: false,
    },
  ];

  const mockOrganizations: Organization[] = [
    {
      id: "1",
      name: "TotalEnergies",
      sector: "Energy • Tech",
      location: "Paris, France",
      logo: "https://logo.clearbit.com/totalenergies.com",
      alumniCount: 45,
    },
  ];

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
            <Badge variant="secondary" className="w-fit mb-3 bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border-0 uppercase text-xs font-bold">
              Programme de Mentorat
            </Badge>
            <h1 className="text-2xl md:text-4xl font-bold mb-4 tracking-tight">
              Accélérez votre carrière grâce au mentorat
            </h1>
            <p className="text-muted-foreground text-sm md:text-lg mb-8 max-w-2xl leading-relaxed">
              Connectez-vous avec plus de 5 000 alumni et étudiants pour partager vos connaissances,
              obtenir des conseils et évoluer ensemble dans le domaine de l'ingénierie.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button size="lg" className="gap-2 h-12 px-8" onClick={() => push(MentorSearchPage, "Trouver un mentor")}>
                <Search className="h-4 w-4" />
                Trouver un mentor
              </Button>
              <Button size="lg" variant="outline" className="gap-2 h-12 px-8" onClick={() => push(BecomeMentorPage, "Devenir mentor")}>
                <UserPlus className="h-4 w-4" />
                Devenir mentor
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Content Area */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="flex w-full overflow-x-auto bg-transparent border-b rounded-none h-auto p-0 scrollbar-none gap-4 md:gap-8">
          <TabsTrigger value="members" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold">
            Membres
          </TabsTrigger>
          <TabsTrigger value="groups" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold">
            Groupes
          </TabsTrigger>
          <TabsTrigger value="organizations" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold">
            Organisations
          </TabsTrigger>
          <TabsTrigger value="mentorship" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 pb-3 pt-2 font-semibold">
            Mentorat
          </TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="space-y-4 focus-visible:outline-none focus-visible:ring-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoading ? (
              Array.from({ length: 2 }).map((_, i) => (
                <Card key={i} className="p-6">
                  <div className="flex gap-4">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-1/3" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                </Card>
              ))
            ) : (
              mockMembers.map((member) => (
                <Card key={member.id} className="hover:border-primary/50 transition-all">
                  <CardContent className="p-4 md:p-6">
                    <div className="flex items-start gap-4 mb-4">
                      <Avatar className="h-12 w-12 border">
                        <AvatarImage src={member.avatar} />
                        <AvatarFallback>{member.name[0]}</AvatarFallback>
                      </Avatar>
                      <div className="min-w-0">
                        <h3 className="font-semibold text-base truncate">{member.name}</h3>
                        <p className="text-xs text-muted-foreground truncate">{member.position} @ {member.company}</p>
                        <p className="text-xs text-muted-foreground mt-1 font-medium">Promo {member.promo}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1 h-8 text-xs">Message</Button>
                      <Button size="sm" variant="outline" className="flex-1 h-8 text-xs">Profil</Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <Button variant="ghost" className="w-full gap-2 text-primary text-sm h-10" onClick={() => push(MembersListPage, "Tous les membres")}>
            Voir tous les membres
            <ChevronDown className="h-4 w-4" />
          </Button>
        </TabsContent>

        <TabsContent value="groups" className="space-y-4 focus-visible:outline-none">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoading ? (
               <Skeleton className="h-32 w-full" />
            ) : (
              mockGroups.map((group) => (
                <Card key={group.id} className="hover:border-primary/50 transition-all">
                  <CardContent className="p-4">
                    <div className="flex gap-3">
                      <div className="h-16 w-16 rounded bg-muted overflow-hidden shrink-0">
                        <img src={group.image} className="w-full h-full object-cover" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-sm truncate">{group.name}</h3>
                        <p className="text-xs text-muted-foreground line-clamp-1">{group.description}</p>
                        <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                          <Users className="h-3 w-3" />
                          {group.memberCount} membres
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <Button variant="outline" className="flex-1 h-10 text-sm" onClick={() => push(GroupsListPage, "Tous les groupes")}>
              Voir tous les groupes
            </Button>
            <Button className="flex-1 h-10 text-sm gap-2" onClick={() => push(GroupFormPage, "Créer un groupe")}>
              <Plus className="h-4 w-4" />
              Créer un groupe
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="mentorship" className="space-y-4 focus-visible:outline-none">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="hover:border-primary/50 transition-all border-dashed bg-muted/20">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Search className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-bold mb-2">Besoin d'aide ?</h3>
                <p className="text-xs text-muted-foreground mb-4">Trouvez un mentor pour vous guider dans votre parcours.</p>
                <Button variant="outline" size="sm" className="w-full" onClick={() => push(MentorSearchPage, "Trouver un mentor")}>
                  Chercher un mentor
                </Button>
              </CardContent>
            </Card>
            <Card className="hover:border-primary/50 transition-all border-dashed bg-muted/20">
              <CardContent className="p-6 flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <UserPlus className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-bold mb-2">Voulez-vous aider ?</h3>
                <p className="text-xs text-muted-foreground mb-4">Partagez vos connaissances et devenez mentor dès aujourd'hui.</p>
                <Button variant="outline" size="sm" className="w-full" onClick={() => push(BecomeMentorPage, "Devenir mentor")}>
                  S'inscrire comme mentor
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="organizations" className="space-y-4 focus-visible:outline-none">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockOrganizations.map((org) => (
              <Card key={org.id} className="hover:border-primary/50 transition-all">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="h-12 w-12 border rounded p-1 shrink-0 bg-white dark:bg-card">
                    <img src={org.logo} className="w-full h-full object-contain" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-semibold text-sm truncate">{org.name}</h3>
                    <p className="text-xs text-muted-foreground">{org.sector}</p>
                  </div>
                  <Button variant="ghost" size="icon" className="ml-auto shrink-0">
                    <BookmarkPlus className="h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          <Button variant="ghost" className="w-full text-sm text-muted-foreground">
            Voir plus d'organisations
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NetworkHome;
