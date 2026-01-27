import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton"; // Import du skeleton shadcn
import { Briefcase, GraduationCap, BookOpen, Info } from "lucide-react";
import { useGetRandomOpportunities } from "@/api/opportunities";
import { Link } from "@inertiajs/react";
import { formatLinkedInDuration, getOportunityUrl } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";



export function LatestOpportunities() {
  const {
    data,
    isLoading,
    error,
  } = useGetRandomOpportunities();
  const opportunities = data?.data;
  const type = data?.type;

  // 1. GESTION DU LOADING (SKELETON)
  if (isLoading) {
    return (
      <Card className="border shadow-sm">
        <CardHeader>
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3 pb-3 border-b last:border-0">
              <Skeleton className="h-10 w-10 rounded flex-shrink-0" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  // 2. GESTION ERREUR OU VIDE
  const hasNoData =
    !opportunities || opportunities.length === 0 || error;

  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Opportunités du réseau { type && <Badge className="bg-primary">{type.toUpperCase()}</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasNoData ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Info className="h-8 w-8 text-muted-foreground/50 mb-2" />
            <p className="text-sm text-muted-foreground">
              Pas d'offre disponible.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {opportunities.map((opp) => {
                const isStage = "type_stage" in opp;
                const isEmploi = "type_emploi" in opp;

                const Icon = isEmploi
                  ? Briefcase
                  : isStage
                    ? GraduationCap
                    : BookOpen;

                return (
                  <Link
                    key={opp.id}
                    href={getOportunityUrl(opp.slug, type!)}
                    className="block group"
                  >
                    <div className="flex gap-3 pb-3 border-b last:border-0 last:pb-0">
                      <div className="w-10 h-10 rounded bg-muted flex-shrink-0 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                        <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                          {opp.titre}
                        </h4>
                        <p className="text-xs text-muted-foreground truncate">
                          {opp.nom_structure} • {opp.ville}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] text-muted-foreground">
                           Publié il y a {formatLinkedInDuration(opp.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
            <Button
              variant="link"
              className="w-full mt-4 justify-center text-sm font-medium p-0 h-auto"
              asChild
            >
              <Link
                href={`/${type == "stage" ? "internships" : "opportunities" }`}
              >
                Voir toutes les opportunités
              </Link>
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
