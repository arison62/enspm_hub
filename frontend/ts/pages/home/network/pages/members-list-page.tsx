import React, { useState, useEffect } from "react";
import { Search, MapPin, Briefcase, ChevronLeft, MessageSquare, BookmarkPlus, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useInternalNav } from "@/contexts/internal-nav-context";

interface Member {
  id: string;
  name: string;
  position: string;
  company: string;
  promo: string;
  location: string;
  avatar: string;
  isMentor?: boolean;
  bio?: string;
  status_global: string;
}

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
    bio: "Passionnée par la recherche et l'innovation en génie chimique.",
    status_global: "ALUMNI",
  },
  {
    id: "2",
    name: "Jean Dupont",
    position: "Stagiaire Data Scientist",
    company: "Microsoft",
    promo: "2024",
    location: "Lyon, France",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Jean",
    isMentor: false,
    bio: "Étudiant en dernière année, spécialisé en Data Science.",
    status_global: "ÉTUDIANT",
  },
  {
    id: "3",
    name: "Sarah Johnson",
    position: "Product Manager",
    company: "Amazon",
    promo: "2019",
    location: "London, UK",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    isMentor: true,
    bio: "Product Manager avec une forte expérience dans le secteur de l'énergie.",
    status_global: "ALUMNI",
  },
  {
    id: "4",
    name: "Lucas Martin",
    position: "Professeur",
    company: "ENSPM",
    promo: "1995",
    location: "Toulouse, France",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Lucas",
    isMentor: false,
    bio: "Professeur de Thermodynamique et chercheur.",
    status_global: "ENSEIGNANT",
  },
];

const MembersListPage: React.FC = () => {
  const { pop } = useInternalNav();
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const filteredMembers = mockMembers.filter((member) =>
    member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    member.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center gap-2 md:gap-4">
        <Button variant="ghost" size="icon" onClick={pop} className="h-8 w-8 md:h-10 md:w-10">
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-xl md:text-2xl font-bold tracking-tight">Membres du Réseau</h1>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Rechercher un membre par nom ou entreprise..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="p-6">
              <div className="flex gap-4 mb-4">
                <Skeleton className="h-16 w-16 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-1/4" />
                </div>
              </div>
              <Skeleton className="h-4 w-full mb-4" />
              <div className="flex gap-2">
                <Skeleton className="h-10 flex-1" />
                <Skeleton className="h-10 w-10" />
              </div>
            </Card>
          ))
        ) : filteredMembers.length > 0 ? (
          filteredMembers.map((member) => (
            <Card key={member.id} className="hover:border-primary/50 transition-all overflow-hidden">
              <CardContent className="p-4 md:p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3 md:gap-4">
                    <Avatar className="h-12 w-12 md:h-16 md:w-16 border">
                      <AvatarImage src={member.avatar} alt={member.name} />
                      <AvatarFallback>{member.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-base md:text-lg mb-1 truncate">
                        {member.name}
                      </h3>
                      <div className="flex flex-wrap gap-1 mb-2">
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                          {member.status_global}
                        </Badge>
                        <Badge variant="outline" className="text-xs px-1.5 py-0">
                          Promo {member.promo}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground flex items-center gap-1 truncate">
                        <Briefcase className="h-3 w-3 shrink-0" />
                        {member.position} @ {member.company}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </div>

                <p className="text-sm text-muted-foreground mb-4 line-clamp-2 italic">
                  "{member.bio}"
                </p>

                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
                  <MapPin className="h-3 w-3 shrink-0" />
                  {member.location}
                </div>

                <div className="flex gap-2">
                  <Button className="flex-1 gap-2 h-9 md:h-10">
                    <MessageSquare className="h-4 w-4" />
                    <span className="hidden sm:inline">Message</span>
                    <span className="sm:hidden text-xs">Message</span>
                  </Button>
                  <Button variant="outline" size="icon" className="h-9 w-9 md:h-10 md:w-10">
                    <BookmarkPlus className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            Aucun membre ne correspond à votre recherche.
          </div>
        )}
      </div>
    </div>
  );
};

export default MembersListPage;
