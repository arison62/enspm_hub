import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MapPin, Clock, DollarSign } from "lucide-react";
import type { OpportuniteAny } from "@/types/opportunities";
import { Link } from "@inertiajs/react";
import { getOportunityUrl } from "@/lib/utils";

interface OpportuniteCardProps {
  data: OpportuniteAny;
}

export const OpportuniteCard = ({ data }: OpportuniteCardProps) => {
  const opportunityType =
    "type_stage" in data
      ? "stage"
      : "type_emploi" in data
        ? "emploi"
        : "formation";

  const getBadge = () => {
    if ("type_stage" in data)
      return (
        <Badge
          variant="secondary"
          className="bg-blue-100 text-blue-700 hover:bg-blue-200"
        >
          Stage {data.type_stage}
        </Badge>
      );
    if ("type_emploi" in data)
      return (
        <Badge
          variant="secondary"
          className="bg-green-100 text-green-700 hover:bg-green-200"
        >
          Emploi
        </Badge>
      );
    if ("type_formation" in data)
      return (
        <Badge
          variant="secondary"
          className="bg-purple-100 text-purple-700 hover:bg-purple-200"
        >
          Formation
        </Badge>
      );
    return null;
  };

  const getSpecificDetails = () => {
    // Logique spécifique pour afficher salaire ou durée
    if ("salaire_min" in data && data.salaire_min) {
      return (
        <div className="flex items-center text-[11px] text-muted-foreground">
          <DollarSign className="h-3 w-3 mr-1 text-primary" />
          {(data.salaire_min / 1000).toFixed(0)}k –{" "}
          {(data.salaire_max! / 1000).toFixed(0)}k {data.devise?.code || "XAF"}
        </div>
      );
    }
    if ("duree_heures" in data && data.duree_heures) {
      return (
        <div className="flex items-center text-[11px] text-muted-foreground">
          <Clock className="h-3 w-3 mr-1 text-primary" /> {data.duree_heures}h
        </div>
      );
    }
    // Fallback simple pour stage si on avait la durée en mois dans le type (à adapter selon ton modèle exact)
    return null;
  };

  return (
    <Card className="opp-card flex flex-col h-full border-none shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-zinc-900 group translate-y-8">
      {/* Note: opacity-0 par défaut pour GSAP */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-sm font-bold group-hover:text-primary transition-colors line-clamp-1">
              {data.titre}
            </CardTitle>
            <CardDescription className="text-xs font-medium line-clamp-1">
              {data.nom_structure}
            </CardDescription>
          </div>
          {getBadge()}
        </div>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center text-[11px] text-muted-foreground">
            <MapPin className="h-3 w-3 mr-1 text-primary" />{" "}
            {data.ville || data.adresse}
          </div>
          {getSpecificDetails()}
        </div>
        <div
          className="text-xs text-muted-foreground line-clamp-3 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: data.description }}
        ></div>
      </CardContent>

      <CardFooter className="pt-4 border-t border-slate-100 dark:border-zinc-800 flex justify-between items-center">
        <span className="text-[10px] text-muted-foreground">
          {new Date(data.date_publication).toLocaleDateString()}
        </span>
        <Link href={getOportunityUrl(data.slug, opportunityType)}>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs font-bold text-primary hover:text-primary hover:bg-primary/5"
          >
            Détails
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
};
