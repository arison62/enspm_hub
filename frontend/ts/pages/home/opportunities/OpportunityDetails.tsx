import { Card } from "@/components/ui/card";
import type { OpportuniteAny } from "@/types/opportunities";
import { CompanyCard } from "../components/opportunities/company-card";
import { OpportunityActionsCard } from "../components/opportunities/opportunity-action-card";
import { OpportunityDescriptionTabs } from "../components/opportunities/opportunity-description-tabs";
import { OpportunityExpirationAlert } from "../components/opportunities/opportunity-expiration-alert";
import { OpportunityHeader } from "../components/opportunities/opportunity-header";
import { OpportunityMetadataGrid } from "../components/opportunities/opportunity-metadata-grid";
import { RecruiterCard } from "../components/opportunities/recruiter-card";
import { SimilarOpportunities } from "../components/opportunities/similar-opportunities";
import { Deferred, usePage } from "@inertiajs/react";
import { useAuthStore } from "@/stores/authStore";
import OpportunityDetailContentSkeleton from "../components/opportunities/opportunity-detail-content-skeleton";
import type { ReactNode } from "react";
import AppLayout from "@/components/layouts/app-layout";

export type OpportunityDetailPageProps = {
  opportunity: OpportuniteAny;
  isOwner?: boolean;
};

function OpportunityDetailPage() {
  return (
    <Deferred
      data="opportunity"
      fallback={<OpportunityDetailContentSkeleton />}
    >
      <PageWrapper />
    </Deferred>
  );
}

OpportunityDetailPage.layout = (page: ReactNode) => (
  <AppLayout>{page}</AppLayout>
);

export default OpportunityDetailPage;

function DetailsContent({
  opportunity,
  isOwner = false,
}: OpportunityDetailPageProps) {
  const opportunityType =
    "type_stage" in opportunity
      ? "stage"
      : "type_emploi" in opportunity
        ? "emploi"
        : "formation";

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Colonne principale (8/12) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Hero Section */}
          <OpportunityHeader opportunity={opportunity} isOwner={isOwner} />

          {/* Métadonnées et expiration */}
          <Card className="border shadow-sm">
            <OpportunityMetadataGrid opportunity={opportunity} />
            <OpportunityExpirationAlert opportunity={opportunity} />
          </Card>

          {/* Description avec onglets */}
          <OpportunityDescriptionTabs opportunity={opportunity} />
        </div>

        {/* Sidebar (4/12) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Carte du recruteur */}
          {opportunity.createur_profil && (
            <RecruiterCard recruiter={opportunity.createur_profil} />
          )}

          {/* Carte de l'entreprise */}
          {opportunity.organisation && (
            <CompanyCard company={opportunity.organisation} />
          )}

          {/* Actions */}
          <OpportunityActionsCard 
          opportunity={opportunity} 
          isOwner={isOwner} 
          type={opportunityType}
          />

          {/* Opportunités similaires */}
          <SimilarOpportunities
            opportunityId={opportunity.id}
            type={opportunityType}
            location={opportunity.ville || ""}
          />
        </div>
      </div>
    </div>
  );
}
function PageWrapper() {
  const { opportunity } = usePage().props as unknown as {
    opportunity: OpportuniteAny;
  };
  const user = useAuthStore((state) => state.user);
  const isOwner = user?.profil?.id === opportunity.createur_profil?.id;
  return <DetailsContent opportunity={opportunity} isOwner={isOwner} />;
}
