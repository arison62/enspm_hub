import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Building, Globe, ExternalLink } from "lucide-react";
import type { OrganisationOut } from "@/types/organisation";

export interface CompanyCardProps {
  company: OrganisationOut;
}
export const CompanyCard = ({ company }: CompanyCardProps) => {
  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground">
          À propos de l'entreprise
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center border p-1 flex-shrink-0">
            {company.logo ? (
              <img
                src={company.logo ?? ""}
                alt={company.nom_organisation}
                className="w-full h-full object-contain"
              />
            ) : (
              <Building className="h-6 w-6 text-muted-foreground" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-bold truncate">{company.nom_organisation}</h4>
            {company && (
              <p className="text-xs text-muted-foreground">
                {company.nombre_membres &&
                  ` • ${company.nombre_membres} employés`}
              </p>
            )}
          </div>
        </div>

        {company.description && (
          <p className="text-sm text-muted-foreground line-clamp-3">
            {company.description}
          </p>
        )}

        {company.site_web && (
          <Button
            variant="ghost"
            className="w-full justify-between group"
            asChild
          >
            <a
              href={company.site_web}
              target="_blank"
              rel="noopener noreferrer"
            >
              <span className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Visiter le site
              </span>
              <ExternalLink className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
