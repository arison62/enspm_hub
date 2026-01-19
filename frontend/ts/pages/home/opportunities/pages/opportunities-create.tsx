/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Briefcase, GraduationCap, Save, Send } from "lucide-react";
import type {
  CountryOption,
  DeviseOption,
} from "../../components/opportunities/forms/base-opportunity-form";
import { EmploiForm } from "../../components/opportunities/forms/emploi-form";
import { FormationForm } from "../../components/opportunities/forms/formation-from";
import { toast } from "sonner";
import axios from "@/lib/axios";
import { AxiosError } from "axios";
import { Spinner } from "@/components/ui/spinner";

const OpportunityCreatePage = () => {
  const [activeTab, setActiveTab] = useState<"emploi" | "formation">("emploi");

  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [devises, setDevises] = useState<DeviseOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    async function getReferences() {
      setIsLoading(true);
      try {
        const paysResponse = axios.get("/references/pays");
        const devisesResponse = axios.get("/references/devises");

        const [paysData, devisesData] = await Promise.all([
          paysResponse,
          devisesResponse,
        ]);

        if (paysData.status === 200) {
          const pays = paysData.data as CountryOption[];
          setCountries(pays);
        }

        if (devisesData.status === 200) {
          const devises = devisesData.data as DeviseOption[];
          setDevises(devises);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    }
    getReferences();
  }, []);
  const [description, setDescription] = useState("");

  async function postEmploi(data: any) {
    try {
      const response = await axios.post("/jobs/", {
        description,
        ...data,
      });
      if (response.status !== 201) {
        throw new Error("Échec de la création de l'emploi");
      }
      return response.data;
    } catch (error) {
      console.error("Erreur API emploi:", error);
      throw error;
    }
  }

  async function postFormation(data: any) {
    try {
      const response = await axios.post("/trainings/", {
        description,
        ...data,
      });
      if (response.status !== 201) {
        throw new Error("Échec de la création de la formation");
      }
      return response.data;
    } catch (error) {
      console.error("Erreur API formation:", error);
      throw error;
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.target as HTMLFormElement);

    // Traitement devise
    const deviseCode = formData.get("devise") as string;
    
    if (deviseCode) {
      const devise = devises.find((d) => d.code === deviseCode);

      if (!devise) {
        toast.error("Devise invalide sélectionnée");
        setIsLoading(false);
        return;
      }

      formData.set("devise_id", devise.id.toString());
      formData.delete("devise");
    }

    formData.set("description", description);

    // Validation
    if (formData.get("is_valid") === "false") {
      toast.error("Veuillez remplir tous les champs obligatoires.");
      setIsLoading(false);
      return;
    }

    const opportunityType = formData.get("type") as string;
    formData.delete("type");
    formData.delete("is_valid");
    // remove empty
    const data = Object.fromEntries(
      Array.from(formData).filter(([, value]) => value !== "")
    );

    try {
      if (opportunityType === "emploi") {
        await postEmploi(data);
        toast.success("Emploi ajouté avec succès !");
      } else if (opportunityType === "formation") {
        await postFormation(data);
        toast.success("Formation ajoutée avec succès !");

        setDescription("");
      }
    } catch (error) {
      let errorMessage = "Une erreur est survenue lors de la création";

      if (error instanceof AxiosError) {
        if (error.response) {
          // Le serveur a répondu avec un code d'erreur
          switch (error.response.status) {
            case 400:
              errorMessage =
                "Données invalides. Vérifiez les champs obligatoires.";
              break;
            case 401:
              errorMessage = "Session expirée. Veuillez vous reconnecter.";
              break;
            default:
              errorMessage = `Erreur serveur: ${error.response.status}`;
          }

          if (error.response.data && typeof error.response.data === "object") {
            console.error("Détails des erreurs:", error.response.data);
          }
        } else if (error.request) {
          errorMessage =
            "Impossible de joindre le serveur. Vérifiez votre connexion.";
        }
      }

      toast.error(errorMessage);
      console.error("Erreur détaillée:", error);
    } finally {
      setIsLoading(false);
    }
  };
  if (isLoading && countries.length === 0 && devises.length === 0) {
    return (
      <div className="max-w-4xl mx-auto sm:px-4 py-8 flex justify-center items-center min-h-[50vh]">
        <div className="text-center">
          <Spinner className="w-8 h-8 mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Chargement des références...</p>
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-4xl mx-auto sm:px-4 py-8 pb-24">
      <Card className="overflow-hidden border-border shadow-sm">
        <form onSubmit={handleSubmit}>
          <Tabs
            value={activeTab}
            onValueChange={(value) => setActiveTab(value as any)}
            className="w-full"
          >
            {/* En-tête des onglets */}
            <div className="bg-muted/30 px-6 pt-6">
              <TabsList className="grid w-full max-w-md grid-cols-2 mx-auto">
                <TabsTrigger value="emploi" className="gap-2">
                  <Briefcase className="h-4 w-4" /> Emploi
                </TabsTrigger>
                <TabsTrigger value="formation" className="gap-2">
                  <GraduationCap className="h-4 w-4" /> Formation
                </TabsTrigger>
              </TabsList>
            </div>
            <TabsContent value="emploi" className="mt-0">
              <EmploiForm
                countries={countries}
                devises={devises}
                onDescriptionChange={setDescription}
              />
            </TabsContent>

            <TabsContent value="formation" className="mt-0">
              <FormationForm
                countries={countries}
                devises={devises}
                onDescriptionChange={setDescription}
              />
            </TabsContent>

            {/* Barre d'action */}
            <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-4 p-6 md:p-8 border-t border-border bg-card">
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="w-full sm:w-auto font-medium gap-2"
              >
                <Save className="h-4 w-4" /> Enregistrer brouillon
              </Button>
              <Button
                type="submit"
                size="lg"
                disabled={isLoading}
                className="w-full sm:w-auto font-bold gap-2 shadow-md"
              >
                {isLoading ? (
                  <>
                    <Spinner />
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                  </>
                )}
                Publier l'opportunité
              </Button>
            </div>
          </Tabs>
        </form>
      </Card>

      <div className="mt-8 text-center text-sm text-muted-foreground">
        Besoin d'aide ?{" "}
        <a href="#" className="text-primary hover:underline">
          Consulter le guide de publication
        </a>
      </div>
    </div>
  );
};

export default OpportunityCreatePage;
