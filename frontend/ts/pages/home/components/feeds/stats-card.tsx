import { useGetProfilStats } from "@/api/feeds";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import { Calendar } from "lucide-react";
import { UserCard } from "./user-card";
import { getAvatarFallback } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const StatsCard = () => {
  // 1. Récupération sécurisée du store
  const user = useAuthStore((state) => state.user);
  const profil = user?.profil;

  // 2. Requête API (activée seulement si on a un ID)
  const { data: stats, isLoading } = useGetProfilStats(profil?.id || "");

  if (!user || !profil) {
    return <StatsCardSkeleton />;
  }

  return (
    <div className="space-y-4">
      <UserCard
        user={{
          name: profil.nom_complet,
          headline: profil.bio || "Membre de l'ENSPM Hub",
          avatarInitials: getAvatarFallback(profil.nom_complet),
          posts: isLoading ? "..." : stats?.posts_count_display,
          views: isLoading ? "..." : stats?.views_count_display,
          likes: isLoading ? "..." : stats?.likes_received_count_display,
          comments: isLoading ? "..." : stats?.comments_received_count_display,
        }}
      />

      <Card className="shadow-sm border-none">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Calendar className="h-4 w-4 text-blue-600" />
            Événements
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2].map((_, i) => (
            <div key={i} className="group cursor-pointer">
              <p className="text-xs font-medium group-hover:text-blue-600 transition-colors">
                Conférence sur l'IA
              </p>
              <p className="text-[10px] text-muted-foreground">
                15 Jan 2026 • En ligne
              </p>
            </div>
          ))}
          <Button variant="ghost" size="sm" className="w-full text-xs h-8">
            Voir tout
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

// Sous-composant Skeleton pour la maintenance
const StatsCardSkeleton = () => (
  <div className="space-y-4">
    <Card className="p-4 space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-48" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 pt-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </Card>
  </div>
);

export default StatsCard;
