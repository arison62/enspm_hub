import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Link } from "@inertiajs/react";
import { Briefcase, MapPin, MessageSquare, MoreVertical } from "lucide-react";

export interface MemberCardProps {
  data: {
    id: string;
    name: string;
    title?: string;
    bio?: string;
    avatar?: string;
    promo?: string;
    isMentor?: boolean;
    status_global: string;
    position?: string;
    company?: string;
    city?: string;
    country?: string;
    slug: string;
  };
  className?: string;
}
const formatStatus = (status: string) => {
  switch (status) {
    case "etudiant":
      return <Badge className="bg-blue-100 text-blue-800">Étudiant</Badge>;
    case "alumni":
      return <Badge className="bg-green-100 text-green-800">Alumni</Badge>;
    case "enseignant":
      return (
        <Badge className="bg-purple-100 text-purple-800">Enseignant</Badge>
      );
    case "personnel_admin":
      return (
        <Badge className="bg-orange-100 text-orange-800">Personnel Admin</Badge>
      );
    case "partenaire":
      return (
        <Badge className="bg-yellow-100 text-yellow-800">Partenaire</Badge>
      );
    default:
      return <Badge className="bg-gray-100 text-gray-800">Inconnu</Badge>;
  }
};
export const MemberCard = ({ data, className }: MemberCardProps) => {
  const member = data;
  return (
    <Card
      key={member.id}
      className={cn(className, "hover:border-primary/50 transition-all overflow-hidden")}
    >
      <CardContent className="p-4 md:p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 md:gap-4">
            <Avatar className="h-12 w-12 md:h-16 md:w-16 border">
              <AvatarImage src={member.avatar} alt={member.name} />
              <AvatarFallback>
                {member.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <h3 className="font-semibold text-base md:text-lg mb-1 truncate">
                {member.title} {member.name}
              </h3>
              <div className="flex flex-wrap gap-1 mb-2">
                {formatStatus(member.status_global)}
                {member.promo && (
                  <Badge variant="outline" className="text-xs px-1.5 py-0">
                    {member.promo}
                  </Badge>
                )}
              </div>
              {member.position && member.company && (
                <p className="text-sm text-muted-foreground flex items-center gap-1 truncate">
                  <Briefcase className="h-3 w-3 shrink-0" />
                  {member.position} @ {member.company}
                </p>
              )}
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>

        {member.bio && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2 italic">
            "{member.bio}"
          </p>
        )}

        {member.city && member.country && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
            <MapPin className="h-3 w-3 shrink-0" />
            {member.city}, {member.country}
          </div>
        )}
        {member.city && !member.country && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
            <MapPin className="h-3 w-3 shrink-0" />
            {member.city}
          </div>
        )}
        {!member.city && member.country && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
            <MapPin className="h-3 w-3 shrink-0" />
            {member.country}
          </div>
        )}

        <div className="flex gap-2 w-full">
          <Button className="gap-2 h-9 md:h-10 w-fit">
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline">Message</span>
            <span className="sm:hidden text-xs">Message</span>
          </Button>
          <Link href={`/profile/${member.slug}`}>
            <Button variant="outline" className="h-9 w-fit md:h-10">
              Voir Profile
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};

export const MemberCardSkeleton = () => (
  <Card className="hover:border-primary/50 transition-all overflow-hidden">
    <CardContent className="p-4 md:p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3 md:gap-4 w-full">
          <Skeleton className="h-12 w-12 md:h-16 md:w-16 rounded-full shrink-0" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-32" />
            <div className="flex flex-wrap gap-1">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-20" />
            </div>
            <Skeleton className="h-4 w-40" />
          </div>
        </div>
        <Skeleton className="h-8 w-8 shrink-0 rounded-md" />
      </div>

      <div className="space-y-2 mb-4">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Skeleton className="h-3 w-3" />
        <Skeleton className="h-3 w-28" />
      </div>

      <div className="flex gap-2">
        <Skeleton className="h-9 md:h-10 w-28" />
        <Skeleton className="h-9 md:h-10 w-28" />
      </div>
    </CardContent>
  </Card>
);
