import { useGetProfilStats } from "@/api/feeds";
import { Card } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
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
          photo_url: profil.photo_profil || "",
          headline: profil.bio || "Membre de l'ENSPM Hub",
          avatarInitials: getAvatarFallback(profil.nom_complet),
          posts: isLoading ? "..." : stats?.posts_count_display,
          views: isLoading ? "..." : stats?.views_count_display,
          likes: isLoading ? "..." : stats?.likes_received_count_display,
          comments: isLoading ? "..." : stats?.comments_received_count_display,
        }}
      />
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
