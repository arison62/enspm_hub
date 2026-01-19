import { CardContent } from "@/components/ui/card";
import type { OpportuniteAny } from "@/types/opportunities";
import { Briefcase, Euro, Calendar, Building, GraduationCap } from "lucide-react";


export type OpportunityMetadataProps = {
    opportunity: OpportuniteAny;
};


export const OpportunityMetadataGrid = ({
  opportunity,
}: OpportunityMetadataProps) => {
  // Type de contrat/format selon le type d'opportunité
  const getContractType = () => {
    if ("type_stage" in opportunity) {
      const types = {
        ouvrier: "Stage ouvrier",
        academique: "Stage académique",
        professionnel: "Stage professionnel",
      };
      return types[opportunity.type_stage];
    }

    if ("type_emploi" in opportunity && opportunity.type_emploi) {
      const types = {
        temps_plein_terrain: "Temps plein - Sur site",
        temps_partiel_terrain: "Temps partiel - Sur site",
        temps_plein_ligne: "Temps plein - Remote",
        temps_partiel_ligne: "Temps partiel - Remote",
        freelance: "Freelance",
        contrat: "Contrat",
      };
      return types[opportunity.type_emploi];
    }

    if ("type_formation" in opportunity && opportunity.type_formation) {
      const types = {
        en_ligne: "En ligne",
        presentiel: "Présentiel",
        hybride: "Hybride",
      };
      return types[opportunity.type_formation];
    }

    return "Type non spécifié";
  };

  // Salaire ou prix selon le type d'opportunité
  const getCompensation = () => {
    if (
      "type_emploi" in opportunity &&
      (opportunity.salaire_min || opportunity.salaire_max) &&
      opportunity.devise
    ) {
      const min = opportunity.salaire_min
        ? `${opportunity.salaire_min.toLocaleString("fr-FR")}`
        : "?";
      const max = opportunity.salaire_max
        ? `${opportunity.salaire_max.toLocaleString("fr-FR")}`
        : "?";
      return `${min} - ${max} ${opportunity.devise.nom || "CFA"}`;
    }

    if ("type_formation" in opportunity) {
      if (opportunity.est_payante && opportunity.prix && opportunity.devise) {
        return `${opportunity.prix.toLocaleString("fr-FR")} ${
          opportunity.devise.code || "CFA"
        }`;
      }
      return "Gratuit";
    }

    return null;
  };

  // Durée selon le type d'opportunité
  const getDuration = () => {
    if (
      ("type_stage" in opportunity || "type_formation" in opportunity) &&
      (opportunity.date_debut || opportunity.date_fin)
    ) {
      const startDate = opportunity.date_debut
        ? new Date(opportunity.date_debut)
        : null;
      const endDate = opportunity.date_fin
        ? new Date(opportunity.date_fin)
        : null;

      if (startDate && endDate) {
        const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const months = Math.floor(diffDays / 30);

        if (months > 0) {
          return `${months} mois`;
        }
        return `${diffDays} jours`;
      }

      if (startDate) {
        return `À partir du ${formatDate(opportunity.date_debut)}`;
      }

      if (endDate) {
        return `Jusqu'au ${formatDate(opportunity.date_fin)}`;
      }
    }

    if ("type_formation" in opportunity && opportunity.duree_heures) {
      return `${opportunity.duree_heures}h`;
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

  return (
    <CardContent className="pt-0">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 border">
          <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
            <Briefcase className="h-4 w-4" />
            Type
          </div>
          <span className="text-sm font-semibold">{getContractType()}</span>
        </div>

        {getCompensation() && (
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 border">
            <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
              {"type_formation" in opportunity ? (
                <GraduationCap className="h-4 w-4" />
              ) : (
                <Euro className="h-4 w-4" />
              )}
              {"type_formation" in opportunity ? "Prix" : "Salaire"}
            </div>
            <span className="text-sm font-semibold">{getCompensation()}</span>
          </div>
        )}

        {getDuration() && (
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 border">
            <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
              <Calendar className="h-4 w-4" />
              Durée
            </div>
            <span className="text-sm font-semibold">{getDuration()}</span>
          </div>
        )}

        {opportunity.organisation?.nombre_membres && (
          <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50 border">
            <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
              <Building className="h-4 w-4" />
              Taille
            </div>
            <span className="text-sm font-semibold">
              {opportunity.organisation.nombre_membres} employés
            </span>
          </div>
        )}
      </div>
    </CardContent>
  );
};
