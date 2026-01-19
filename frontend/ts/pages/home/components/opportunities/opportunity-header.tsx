import { Card, CardHeader } from "@/components/ui/card";
import { Building, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { Link } from "@inertiajs/react";
import { ApplyButton } from "./apply-button";
import { OpportunityTypeBadge } from "./opportunity-type-badge";
import type { OpportuniteAny } from "@/types/opportunities";

export interface OpportunityHeaderProps {
  isOwner?: boolean;
  opportunity: OpportuniteAny;
}

export const OpportunityHeader = ({
  opportunity,
}: OpportunityHeaderProps) => {
  const timeSincePublication = opportunity.date_publication
    ? formatDistanceToNow(new Date(opportunity.date_publication), {
        locale: fr,
        addSuffix: true,
      })
    : "";

  return (
    <Card className="border shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Logo */}
          <div className="bg-muted rounded-lg h-24 w-24 flex-shrink-0 flex items-center justify-center overflow-hidden border">
            {opportunity.organisation?.logo ? (
              <img
                src={opportunity.organisation.logo}
                alt={`${opportunity.nom_structure} logo`}
                className="w-16 h-16 object-contain"
              />
            ) : (
              <Building className="h-8 w-8 text-muted-foreground" />
            )}
          </div>

          {/* Titre et informations */}
          <div className="flex-1">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
                  {opportunity.titre}
                </h1>

                <div className="text-muted-foreground mt-2 flex flex-wrap items-center gap-2">
                  {opportunity.organisation ? (
                    <Link
                      href={`/organisations/${opportunity.organisation.slug}`}
                      className="font-medium hover:underline hover:text-primary"
                    >
                      {opportunity.nom_structure}
                    </Link>
                  ) : (
                    <p className="text-muted-foreground">
                      {opportunity.nom_structure}
                    </p>
                  )}
                  {(opportunity.ville || opportunity.pays_nom) && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {opportunity.ville}
                        {opportunity.ville && opportunity.pays_nom ? ", " : ""}
                        {opportunity.pays_nom}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-3">
                <ApplyButton opportunity={opportunity} />
                {/* <Button variant="outline" size="lg">
                  <Bookmark className="h-4 w-4" />
                </Button> */}
              </div>
            </div>

            {/* Métadonnées */}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground mt-4">
              <Badge variant="secondary" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Publié {timeSincePublication}
              </Badge>
              <OpportunityTypeBadge opportunity={opportunity} />
              
            </div>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
};
