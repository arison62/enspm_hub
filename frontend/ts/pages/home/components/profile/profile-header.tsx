import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Edit, Briefcase, MapPin } from "lucide-react";

import { useInternalNav } from "@/contexts/internal-nav-context";
import ProfileEdit from "../../profile/pages/profile-edit";
import type { UserComplete } from "@/types/user";

export const ProfileHeader = ({
  profil,
  isOwner = false,
}: {
  profil: UserComplete["profil"];
  isOwner: boolean;
}) => {
  const { push } = useInternalNav();
  const handleNavigation = () => {
    if (isOwner) {
      push(ProfileEdit, "Modifier mon profil");
    }
  };
  return (
    <>
      <div className="relative">
        <div className="h-40 md:h-64 w-full bg-primary overflow-hidden">
          <div className="absolute inset-0 opacity-30 bg-[url('https://www.transparenttextures.com/patterns/black-thread.png')]" />
        </div>

        <div className="container mx-auto px-4">
          <div className="relative -mt-16 md:-mt-20 flex flex-col md:flex-row items-center lg:items-end gap-6 animate-fade">
            <Avatar className="size-32 md:size-44 border-4 border-background shadow-xl">
              <AvatarImage
                src={profil.photo_profil || ""}
                alt={profil.nom_complet}
                className="object-cover"
              />
              <AvatarFallback className="text-3xl">
                {profil.nom_complet?.[0]}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 text-center md:text-left mb-2 md:h-60 md:flex md:flex-col md:justify-end lg:block lg:h-auto">
              <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                <h1 className="text-2xl md:text-4xl font-extrabold text-foreground">
                  {profil.titre && (
                    <span className="text-primary">{profil.titre.titre} </span>
                  )}
                  {profil.nom_complet}
                </h1>
                <Badge className="w-fit mx-auto md:mx-0 bg-primary/10 text-primary border-primary/20">
                  {profil.statut_global?.toUpperCase()}
                </Badge>
              </div>

              <div className="flex flex-wrap justify-center md:justify-start gap-x-4 gap-y-1 mt-2 text-muted-foreground text-sm md:text-base">
                {profil.domaine && (
                  <span className="flex items-center gap-1">
                    <Briefcase className="size-4" /> {profil.domaine.nom}
                  </span>
                )}
                {profil.pays_nom && (
                  <span className="flex items-center gap-1">
                    <MapPin className="size-4" /> {profil.pays_nom}
                    {profil.ville && `, ${profil.ville}`}
                  </span>
                )}
              </div>
            </div>

            {isOwner && (
              <div className="flex pb-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-full shadow-sm"
                  asChild
                  onClick={handleNavigation}
                >
                  <span>
                    <Edit className="mr-2 size-4" /> Modifier le profil
                  </span>
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
