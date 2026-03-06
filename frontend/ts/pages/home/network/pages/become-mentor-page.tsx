import React, { useState } from "react";
import { GraduationCap, Award, BookOpen, Clock, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { useInternalNav } from "@/contexts/internal-nav-context";
import { toast } from "sonner";

const BecomeMentorPage: React.FC = () => {
  const { pop } = useInternalNav();
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setSubmitted(true);
      toast.success("Candidature de mentorat enregistrée !");
    }, 1500);
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
            Merci de vouloir partager votre expérience. Notre équipe examine votre profil et vous contactera très prochainement.
          </p>
        </div>
        <Button onClick={pop} className="w-full">Retour au réseau</Button>
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
                <CardTitle className="text-lg md:text-xl">Profil de Mentorat</CardTitle>
                <CardDescription>
                  Aidez les étudiants et jeunes diplômés à naviguer dans leur début de carrière.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 p-4 md:p-6 pt-0">
                <div className="space-y-2">
                  <Label htmlFor="bio">Biographie professionnelle</Label>
                  <Textarea
                    id="bio"
                    placeholder="Résumez votre parcours et ce que vous souhaitez apporter en tant que mentor..."
                    className="min-h-32"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="skills">Domaines d'expertise (séparés par des virgules)</Label>
                  <Input id="skills" placeholder="ex: Gestion de projet, Génie Civil, Data Analysis" required />
                </div>

                <div className="space-y-4">
                  <Label>Disponibilité</Label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      "1 heure par mois",
                      "1 heure par quinzaine",
                      "1 heure par semaine",
                      "Sur demande uniquement"
                    ].map((time) => (
                      <div key={time} className="flex items-center space-x-2 border rounded-md p-3">
                        <Checkbox id={time} />
                        <label htmlFor={time} className="text-sm leading-none cursor-pointer">
                          {time}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <Label>Accompagnement souhaité</Label>
                  <div className="space-y-3">
                    {[
                      { id: "cv", label: "Revue de CV et préparation d'entretien" },
                      { id: "orient", label: "Orientation de carrière et choix de spécialité" },
                      { id: "tech", label: "Partage d'expertise technique" },
                      { id: "soft", label: "Développement des soft skills" }
                    ].map((item) => (
                      <div key={item.id} className="flex items-start space-x-2">
                        <Checkbox id={item.id} />
                        <label htmlFor={item.id} className="text-sm leading-tight cursor-pointer">
                          {item.label}
                        </label>
                      </div>
                    ))}
                  </div>
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
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-primary">Pourquoi être mentor ?</CardTitle>
            </CardHeader>
            <CardContent className="p-4 md:p-6 pt-0 space-y-4">
              <div className="flex gap-3">
                <GraduationCap className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Transmettre</h4>
                  <p className="text-xs text-muted-foreground">Partagez votre expérience avec la nouvelle génération.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Award className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Inspirer</h4>
                  <p className="text-xs text-muted-foreground">Guidez des talents prometteurs vers la réussite.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <BookOpen className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Apprendre</h4>
                  <p className="text-xs text-muted-foreground">Le mentorat est aussi une opportunité d'auto-réflexion.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Clock className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold">Flexible</h4>
                  <p className="text-xs text-muted-foreground">Vous déterminez le temps que vous souhaitez y consacrer.</p>
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
