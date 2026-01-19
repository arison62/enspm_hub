import { Badge } from "@/components/ui/badge";
import type { OpportuniteAny } from "@/types/opportunities";
export interface OpportunityCommonProps {
  opportunity?: OpportuniteAny;
}

export const OpportunityTypeBadge = ({
  opportunity,
}: OpportunityCommonProps) => {
  // Détermine le type d'opportunité

  if (!opportunity) {
    return null;
  }
 
  const isStage = "type_stage" in opportunity;
  const isEmploi = "type_emploi" in opportunity;

  const opportunityType = isStage ? "stage" : isEmploi ? "emploi" : "formation";

  const configs = {
    stage: { label: "Stage", variant: "default" as const },
    emploi: { label: "Emploi", variant: "secondary" as const },
    formation: { label: "Formation", variant: "outline" as const },
  };

  const config = configs[opportunityType];
  return <Badge variant={config.variant}>{config.label}</Badge>;
};
