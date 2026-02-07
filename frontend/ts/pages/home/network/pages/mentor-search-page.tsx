import React, { useState, useEffect } from "react";
import { Search, MapPin, ChevronLeft, Filter, Star, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useInternalNav } from "@/contexts/internal-nav-context";
import MentoringRequestPage from "./mentoring-request-page";

interface Mentor {
  id: string;
  name: string;
  position: string;
  company: string;
  location: string;
  avatar: string;
  expertise: string[];
  rating: number;
  reviewCount: number;
}

const mockMentors: Mentor[] = [
  {
    id: "1",
    name: "Sarah Johnson",
    position: "Product Manager",
    company: "Amazon",
    location: "London, UK",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    expertise: ["Product Management", "Tech Strategy"],
    rating: 4.9,
    reviewCount: 24,
  },
  {
    id: "2",
    name: "Marie Curie",
    position: "Senior Engineer",
    company: "Google",
    location: "Paris, France",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Marie",
    expertise: ["Engineering Management", "Backend"],
    rating: 5.0,
    reviewCount: 18,
  },
  {
    id: "3",
    name: "Thomas Wilson",
    position: "CTO",
    company: "GreenTech",
    location: "Berlin, Germany",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Thomas",
    expertise: ["Leadership", "Sustainability"],
    rating: 4.8,
    reviewCount: 32,
  },
];

const MentorSearchPage: React.FC = () => {
  const { pop, push } = useInternalNav();
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const filteredMentors = mockMentors.filter((mentor) =>
    mentor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    mentor.expertise.some(e => e.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 md:gap-4">
          <Button variant="ghost" size="icon" onClick={pop} className="h-8 w-8 md:h-10 md:w-10">
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">Trouver un Mentor</h1>
        </div>
        <Button variant="outline" size="sm" className="gap-2 h-8 md:h-10">
          <Filter className="h-4 w-4" />
          <span className="hidden sm:inline">Filtres</span>
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Rechercher par nom, expertise, entreprise..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4 md:p-6">
              <div className="flex flex-col items-center text-center space-y-4">
                <Skeleton className="h-20 w-20 rounded-full" />
                <div className="space-y-2 w-full">
                  <Skeleton className="h-5 w-3/4 mx-auto" />
                  <Skeleton className="h-4 w-1/2 mx-auto" />
                  <Skeleton className="h-8 w-full" />
                </div>
              </div>
            </Card>
          ))
        ) : filteredMentors.length > 0 ? (
          filteredMentors.map((mentor) => (
            <Card key={mentor.id} className="hover:border-primary/50 transition-all flex flex-col h-full">
              <CardContent className="p-6 flex flex-col items-center text-center h-full">
                <Avatar className="h-20 w-20 md:h-24 md:w-24 border-4 border-muted mb-4">
                  <AvatarImage src={mentor.avatar} alt={mentor.name} />
                  <AvatarFallback>{mentor.name.split(" ").map(n => n[0]).join("")}</AvatarFallback>
                </Avatar>

                <div className="mb-2">
                  <h3 className="font-bold text-lg">{mentor.name}</h3>
                  <p className="text-sm text-muted-foreground">{mentor.position} @ {mentor.company}</p>
                </div>

                <div className="flex items-center gap-1 mb-4">
                  <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                  <span className="text-sm font-semibold">{mentor.rating}</span>
                  <span className="text-xs text-muted-foreground">({mentor.reviewCount} avis)</span>
                </div>

                <div className="flex flex-wrap justify-center gap-1.5 mb-6 flex-grow">
                  {mentor.expertise.map((exp) => (
                    <Badge key={exp} variant="secondary" className="text-xs">
                      {exp}
                    </Badge>
                  ))}
                </div>

                <div className="w-full space-y-2 mt-auto">
                  <div className="flex items-center justify-center text-xs text-muted-foreground gap-1 mb-2">
                    <MapPin className="h-3 w-3" />
                    {mentor.location}
                  </div>
                  <Button
                    className="w-full gap-2"
                    onClick={() => push(MentoringRequestPage, "Demande de Mentorat", { mentor })}
                  >
                    <MessageCircle className="h-4 w-4" />
                    Contacter
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            Aucun mentor trouvé.
          </div>
        )}
      </div>
    </div>
  );
};

export default MentorSearchPage;
