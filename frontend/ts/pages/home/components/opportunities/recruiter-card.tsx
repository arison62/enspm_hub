import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Phone, MessageSquare } from "lucide-react";
import type { ProfilOut } from "@/types/user";
import { Link } from "@inertiajs/react";

export interface RecruiterCardProps {
  recruiter: ProfilOut;
}

export const RecruiterCard = ({
  recruiter,
}: RecruiterCardProps) => {
  const contactPhone = recruiter.telephone
  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
          Publié par
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-14 w-14">
            <AvatarImage
              src={recruiter.photo_profil ?? ""}
              alt={recruiter.nom_complet}
            />
            <AvatarFallback>
              {recruiter.nom_complet
                ?.split(" ")
                .map((n: string) => n[0])
                .join("") || "?"}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-bold">{recruiter.nom_complet}</p>
            {recruiter.annee_sortie && (
              <p className="text-sm text-primary font-medium">
                {recruiter.annee_sortie.libelle}
              </p>
            )}
            {recruiter.bio && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {recruiter.bio}
              </p>
            )}
          </div>
        </div>

        {contactPhone && (
          <div className="pt-3 border-t">
            {contactPhone && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">{contactPhone}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center max-w-xs gap-2 pt-2">
          <Link
            href={`/profile/${recruiter.slug}`}
            className="flex-1 gap-2 w-fit"
          >
            <Button variant="outline" className="flex-1 gap-2 w-fit" size="sm">
              <MessageSquare className="h-4 w-4" />
              Voir le profil
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};
