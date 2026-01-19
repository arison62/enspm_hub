import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { OpportuniteAny } from "@/types/opportunities";
import { AlertCircle } from "lucide-react";

export type OpportunityCommonProps = {
    opportunity: OpportuniteAny;
}

export const OpportunityExpirationAlert = ({
  opportunity,
}: OpportunityCommonProps) => {
  const getExpirationInfo = () => {
    if ("type_emploi" in opportunity && opportunity.date_expiration) {
      const expDate = new Date(opportunity.date_expiration);
      const today = new Date();
      const daysLeft = Math.ceil(
        (expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysLeft < 0) {
        return {
          text: "Cette offre a expiré",
          variant: "destructive" as const,
        };
      }

      if (daysLeft <= 3) {
        return {
          text: `Cette offre expire dans ${daysLeft} jour${
            daysLeft > 1 ? "s" : ""
          }`,
          variant: "default" as const,
        };
      }

      return {
        text: `Date limite de candidature : ${formatDate(
          opportunity.date_expiration
        )}`,
        variant: "default" as const,
      };
    }

    return null;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Non spécifié";
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  const expirationInfo = getExpirationInfo();

  if (!expirationInfo) return null;

  return (
    <Alert variant={expirationInfo.variant} className="mt-6 border-none">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Date limite</AlertTitle>
      <AlertDescription>{expirationInfo.text}</AlertDescription>
    </Alert>
  );
};
