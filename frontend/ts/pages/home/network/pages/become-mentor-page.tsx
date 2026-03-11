import React, { useEffect, useState } from "react";
import {
  GraduationCap,
  Award,
  BookOpen,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import SearchField from "@/components/search-field";
import { useInternalNav } from "@/contexts/internal-nav-context";
import { type FiliereOut } from "@/types/base";
import axios from "@/lib/axios";
import { useMentoringActions } from "@/api/network/mentoring";
import { AvailabilitySlider } from "../../components/network/availability-step";
import { toast } from "sonner";

const BecomeMentorPage: React.FC = () => {
  const { pop } = useInternalNav();
  const [filieres, setFilieres] = useState<FiliereOut[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>();
  const { createMentorProfil } = useMentoringActions();
  const [selectedFilieres, setSelectedFilieres] = useState<
    {
      label: string;
      value: string;
    }[]
  >([]);

  const filiereItems = React.useMemo(
    () =>
      filieres.map((el) => ({
        value: el.id,
        label: el.nom,
      })),
    [filieres],
  );
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    bio: "",
    disponibilite: 50,
  });
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    async function getFilieres() {
      setIsLoading(true);
      try {
        const response = await axios.get("/references/filieres");
        if (response.status === 200) {
          const data = response.data as FiliereOut[];
          setFilieres([...data]);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    }

    getFilieres();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      biographie: formData.bio,
      disponibilite: formData.disponibilite,
      filieres_expertise: selectedFilieres.map((f) => f.value),
      domaines_expertise: null,
    };
    if (data.filieres_expertise.length === 0) {
      setErrorMsg("Veuillez choisir au moins une specialite");
      return;
    }
    if (data.biographie.length === 0) {
      setErrorMsg("Veuillez ajouter une biographie");
      return;
    }
    
    setIsLoading(true);
    createMentorProfil
      .mutateAsync(data)
      .then(() => {
        setSubmitted(true);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
        setIsLoading(false);
        toast.error(error.message);
      });
  };

  if (submitted) {
    return (
      <div className="max-w-md mx-auto py-12 text-center space-y-6">
        <div className="h-20 w-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
          <CheckCircle2 className="h-10 w-10 text-green-600 dark:text-green-400" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold">Candidature Reçue !</h1>
          <p className="text-muted-foreground">
            Merci de vouloir partager votre expérience. Notre équipe examine
            votre profil et vous contactera très prochainement.
          </p>
        </div>
        <Button onClick={pop} className="w-full">
          Retour au réseau
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit}>
            <Card>
              <CardHeader className="p-4 md:p-6">
                <CardTitle className="text-lg md:text-xl">
                  Profil de Mentorat
                </CardTitle>
                <CardDescription>
                  Aidez les étudiants et jeunes diplômés à naviguer dans leur
                  début de carrière.
                </CardDescription>
                {errorMsg && <p className="text-red-500 text-sm">{errorMsg}</p>}
              </CardHeader>
              <CardContent className="space-y-6 p-4 md:p-6 pt-0">
                <div className="space-y-2">
                  <Label htmlFor="bio">Biographie professionnelle</Label>
                  <Textarea
                    id="bio"
                    placeholder="Résumez votre parcours et ce que vous souhaitez apporter en tant que mentor..."
                    className="min-h-32"
                    value={formData.bio}
                    onChange={(e) =>
                      setFormData({ ...formData, bio: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="skills">
                    Domaines d'expertise (au moins 1)
                  </Label>
                  <SearchField
                    selectedItems={selectedFilieres}
                    onItemsChange={(newFilieres) => {
                      setSelectedFilieres(newFilieres);
                    }}
                    items={filiereItems}
                  />
                </div>

                <div className="space-y-4">
                  <Label>Disponibilité {formData.disponibilite} %</Label>
                  <AvailabilitySlider
                    value={formData.disponibilite}
                    onChange={(v) =>
                      setFormData({ ...formData, disponibilite: v })
                    }
                  />
                </div>
              </CardContent>
              <CardFooter className="p-4 md:p-6 border-t">
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? "Traitement..." : "Valider mon profil mentor"}
                </Button>
              </CardFooter>
            </Card>
          </form>
        </div>

        <div className="space-y-6">
          <Card className="bg-primary/5 border-primary/20">
            <CardHeader className="p-4 md:p-6">
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-primary">
                Pourquoi être mentor ?
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 md:p-6 pt-0 space-y-4">
              <div className="flex gap-3">
                <GraduationCap className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Transmettre</h4>
                  <p className="text-xs text-muted-foreground">
                    Partagez votre expérience avec la nouvelle génération.
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Award className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Inspirer</h4>
                  <p className="text-xs text-muted-foreground">
                    Guidez des talents prometteurs vers la réussite.
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <BookOpen className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Apprendre</h4>
                  <p className="text-xs text-muted-foreground">
                    Le mentorat est aussi une opportunité d'auto-réflexion.
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Clock className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Flexible</h4>
                  <p className="text-xs text-muted-foreground">
                    Vous déterminez le temps que vous souhaitez y consacrer.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default BecomeMentorPage;
