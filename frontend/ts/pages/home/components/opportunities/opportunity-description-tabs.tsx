import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Mail, Phone, MapPin, Globe } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import type { OpportuniteAny } from "@/types/opportunities";

interface OpportunityCommonProps {
  opportunity: OpportuniteAny;
}

export const OpportunityDescriptionTabs = ({
  opportunity,
}: OpportunityCommonProps) => {
  return (
    <Card className="border shadow-sm">
      <CardHeader>
        <CardTitle>À propos de l'opportunité</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="details" className="w-full">
          <TabsList className="w-full md:w-fit">
            <TabsTrigger value="details">Détails</TabsTrigger>
            <TabsTrigger value="company">Entreprise</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="mt-6 space-y-4">
            <div
              className="prose dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{
                __html: opportunity.description,
              }}
            />

            {/* Informations de contact */}
            <Separator className="my-6" />
            <div className="space-y-3">
              <h3 className="text-lg font-bold">Informations de contact</h3>
              {opportunity.email_contact && (
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={`mailto:${opportunity.email_contact}`}
                    className="text-primary hover:underline"
                  >
                    {opportunity.email_contact}
                  </a>
                </div>
              )}
              {opportunity.telephone_contact && (
                <div className="flex items-center gap-3 text-sm">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {opportunity.telephone_contact}
                  </span>
                </div>
              )}
              {opportunity.adresse && (
                <div className="flex items-center gap-3 text-sm">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {opportunity.adresse}
                  </span>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="company" className="mt-6">
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-muted-foreground">
                {opportunity.organisation?.description ||
                  "Aucune description disponible pour cette entreprise."}
              </p>
            </div>
            {opportunity.organisation?.site_web && (
              <>
                {" "}
                <Separator className="my-6" />
                <div className="mt-4 flex items-baseline gap-2">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={opportunity.organisation?.site_web}
                    target="_blank"
                    className="text-primary hover:underline"
                  >
                    {opportunity.organisation?.site_web}
                  </a>
                </div>
              </>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
