/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Save, Send } from "lucide-react";
import type {
  CountryOption,
  DeviseOption,
} from "../../components/opportunities/forms/base-opportunity-form";
import { toast } from "sonner";
import axios from "@/lib/axios";
import { AxiosError } from "axios";
import { Spinner } from "@/components/ui/spinner";
import { StageForm } from "../../components/opportunities/forms/stage-form";

type FiliereType = {
  domaine_id: string;
  domaine_nom: string;
  domaine_code: string;
  id: string;
  nom: string;
  code: string;
};

type SecteurType = {
  id: string;
  nom: string;
  code: string;
};

const InternshipCreatePage = () => {
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [devises, setDevises] = useState<DeviseOption[]>([]);
  const [secteurs, setSecteurs] = useState<SecteurType[]>([]);
  const [filieres, setFilieres] = useState<FiliereType[]>([]);
  const secteursData = useMemo(() => {
    return secteurs.map((secteur) => ({
      label: secteur.nom,
      value: secteur.id,
    }));
  }, [secteurs]);
  const filieresData = useMemo(() => {
    return filieres.map((filiere) => ({
      label: filiere.nom,
      value: filiere.id,
    }));
  }, [filieres]);
  const [selectedFilieres, setSelectedFilieres] = useState<
    {
      label: string;
      value: string;
    }[]
  >([]);
  const [selectedSecteurs, setSelectedSecteurs] = useState<
    {
      label: string;
      value: string;
    }[]
  >([]);

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function getReferences() {
      setIsLoading(true);
      try {
        const paysResponse = axios.get("/references/pays");
        const devisesResponse = axios.get("/references/devises");
        const secteursResponse = axios.get("/references/secteurs");
        const filieresResponse = axios.get("/references/filieres");

        const [paysData, devisesData, secteursData, filieresData] =
          await Promise.all([
            paysResponse,
            devisesResponse,
            secteursResponse,
            filieresResponse,
          ]);

        if (paysData.status === 200) {
          const pays = paysData.data as CountryOption[];
          setCountries(pays);
        }

        if (devisesData.status === 200) {
          const devises = devisesData.data as DeviseOption[];
          setDevises(devises);
        }

        if (secteursData.status === 200) {
          const secteurs = secteursData.data as SecteurType[];
          setSecteurs(secteurs);
        }

        if (filieresData.status === 200) {
          const filieres = filieresData.data as FiliereType[];
          setFilieres(filieres);
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

  async function postStage(data: any) {
    const filiereIds = selectedFilieres.map((filiere) => filiere.value);
    const secteurIds = selectedSecteurs.map((secteur) => secteur.value);
    const domaineIds = filieres
      .filter((filiere) => filiereIds.includes(filiere.id))
      .map((filiere) => filiere.domaine_id)
      .filter(
        (domaineId, index, domaineIds) =>
          domaineIds.indexOf(domaineId) === index,
      );

    try {
      const response = await axios.post("/internships/", {
        description,
        ...data,
        domaines: domaineIds,
        filieres: filiereIds,
        secteurs: secteurIds,
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    console.log("Selcted filieres : ", selectedFilieres);
    console.log("Selcted secteurs : ", selectedSecteurs);
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
    formData.delete("type");
    formData.delete("is_valid");
    // remove empty
    const data = Object.fromEntries(
      Array.from(formData).filter(([, value]) => value !== ""),
    );

    try {
      await postStage(data);
      toast.success("Emploi ajouté avec succès !");
      setDescription("");
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
          <StageForm
            countries={countries}
            devises={devises}
            filieres={filieresData}
            secteurs={secteursData}
            selectedFilieres={selectedFilieres}
            selectedSecteurs={selectedSecteurs}
            onFilieresChange={setSelectedFilieres}
            onSecteursChange={setSelectedSecteurs}
            onDescriptionChange={setDescription}
          />

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

export default InternshipCreatePage;
