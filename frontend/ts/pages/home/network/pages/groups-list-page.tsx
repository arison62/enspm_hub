import React, { useState, useEffect } from "react";
import { Search, Users, ChevronLeft, Plus, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useInternalNav } from "@/contexts/internal-nav-context";
import GroupFormPage from "./group-form-page";

interface Group {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  image: string;
  isJoined: boolean;
}

const mockGroups: Group[] = [
  {
    id: "1",
    name: "Club Robotique",
    description: "Passionnés de robotique et d'automatisation. Nous organisons des ateliers hebdomadaires.",
    memberCount: 124,
    image: "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400",
    isJoined: false,
  },
  {
    id: "2",
    name: "Alumni Paris",
    description: "Réseau des anciens élèves basés à Paris. Networking, événements et entraide.",
    memberCount: 342,
    image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400",
    isJoined: true,
  },
  {
    id: "3",
    name: "Data Science Hub",
    description: "Partage de connaissances, projets et opportunités dans le domaine de la Data Science.",
    memberCount: 287,
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400",
    isJoined: false,
  },
];

const GroupsListPage: React.FC = () => {
  const { pop, push } = useInternalNav();
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const filteredGroups = mockGroups.filter((group) =>
    group.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={pop} className="h-8 w-8">
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">Groupes de discussion</h1>
        </div>
        <Button className="gap-2 w-full sm:w-auto" onClick={() => push(GroupFormPage, "Créer un groupe")}>
          <Plus className="h-4 w-4" />
          Créer un groupe
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Rechercher un groupe..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="p-4 md:p-6">
              <div className="flex gap-4">
                <Skeleton className="h-16 w-16 md:h-20 md:w-20 rounded-lg shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-1/3" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-1/4" />
                </div>
              </div>
            </Card>
          ))
        ) : filteredGroups.length > 0 ? (
          filteredGroups.map((group) => (
            <Card key={group.id} className="hover:border-primary/50 transition-all">
              <CardContent className="p-4 md:p-6">
                <div className="flex gap-4">
                  <div className="h-16 w-16 md:h-20 md:w-20 rounded-lg overflow-hidden flex-shrink-0 bg-muted border">
                    <img
                      src={group.image}
                      alt={group.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div className="min-w-0">
                        <h3 className="font-semibold text-base md:text-lg mb-1 truncate">{group.name}</h3>
                        <p className="text-sm text-muted-foreground mb-2 line-clamp-1 md:line-clamp-2">
                          {group.description}
                        </p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {group.memberCount} membres
                        </p>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex gap-2 mt-4">
                      {group.isJoined ? (
                        <Button variant="outline" className="flex-1 h-9 text-xs sm:text-sm" disabled>
                          Déjà rejoint
                        </Button>
                      ) : (
                        <Button className="flex-1 h-9 text-xs sm:text-sm">Rejoindre</Button>
                      )}
                      <Button variant="outline" className="flex-1 h-9 text-xs sm:text-sm">Voir</Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-xl">
            Aucun groupe trouvé.
          </div>
        )}
      </div>
    </div>
  );
};

export default GroupsListPage;
