import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Briefcase, GraduationCap, BookOpen } from "lucide-react";
import type { OpportuniteAny } from "@/types/opportunities";

interface SimilarOpportunitiesProps {
  currentOpportunityId: string;
  type: "stage" | "emploi" | "formation";
  sector?: string;
  location?: string;
}

// Données factices pour la démo - à remplacer par un appel API en production
const mockOpportunities: OpportuniteAny[] = [
  {
    id: "1",
    titre: "Ingénieur Process Junior",
    nom_structure: "TotalEnergies",
    ville: "Paris",
    pays_nom: "France",
    date_publication: "2024-01-15T10:30:00Z",
    statut: "active",
    est_valide: true,
    type_emploi: "temps_plein_terrain",
    slug: "ingenieur-process-junior",
  } as unknown as OpportuniteAny,
  {
    id: "2",
    titre: "Stage en Data Science",
    nom_structure: "Schlumberger",
    ville: "Pau",
    pays_nom: "France",
    date_publication: "2024-01-12T14:20:00Z",
    statut: "active",
    est_valide: true,
    type_stage: "professionnel",
    slug: "stage-data-science",
  } as unknown as OpportuniteAny,
  {
    id: "3",
    titre: "Formation Management de Projet",
    nom_structure: "IFP School",
    ville: "Rueil-Malmaison",
    pays_nom: "France",
    date_publication: "2024-01-10T09:15:00Z",
    statut: "active",
    est_valide: true,
    type_formation: "hybride",
    slug: "formation-management-projet",
  } as unknown as OpportuniteAny,
];

export function SimilarOpportunities({
  currentOpportunityId,
}: SimilarOpportunitiesProps) {
  // Filtrer les opportunités similaires (dans la vraie app, cela viendrait de l'API)
  const similarOpportunities = mockOpportunities
    .filter((opp) => opp.id !== currentOpportunityId)
    .slice(0, 3);

  if (similarOpportunities.length === 0) return null;

  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Opportunités similaires
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {similarOpportunities.map((opp) => {
            const isStage = "type_stage" in opp;
            const isEmploi = "type_emploi" in opp;

            const Icon = isEmploi
              ? Briefcase
              : isStage
              ? GraduationCap
              : BookOpen;

            return (
              <a
                key={opp.id}
                href={`/${
                  isStage ? "stages" : isEmploi ? "emplois" : "formations"
                }/${opp.slug}`}
                className="block group"
              >
                <div className="flex gap-3 pb-3 border-b last:border-0 last:pb-0">
                  <div className="w-10 h-10 rounded bg-muted flex-shrink-0 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold group-hover:text-primary transition-colors">
                      {opp.titre}
                    </h4>
                    <p className="text-xs text-muted-foreground">
                      {opp.nom_structure} • {opp.ville}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-muted-foreground">
                        Publié il y a 3 jours
                      </span>
                    </div>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
        <Button
          variant="link"
          className="w-full mt-4 justify-center text-sm font-medium p-0 h-auto"
        >
          Voir toutes les opportunités
        </Button>
      </CardContent>
    </Card>
  );
}
