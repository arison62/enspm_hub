import { Button } from "@/components/ui/button";
import type { OpportuniteAny } from "@/types/opportunities";
import { ExternalLink } from "lucide-react";

export interface OpportunityCommonProps {
  opportunity: OpportuniteAny;
}


export const ApplyButton = ({ opportunity }: OpportunityCommonProps) => {
  const getApplyLink = () => {
    if ("lien_candidature" in opportunity && opportunity.lien_candidature) {
      return opportunity.lien_candidature;
    }
    if ("lien_inscription" in opportunity && opportunity.lien_inscription) {
      return opportunity.lien_inscription;
    }
    return null;
  };

  const applyLink = getApplyLink();

  if (!applyLink) return null;

  return (
    <Button asChild size="lg" className="gap-2">
      <a href={applyLink} target="_blank" rel="noopener noreferrer">
        <ExternalLink className="h-4 w-4" />
        Postuler maintenant
      </a>
    </Button>
  );
};
