import React, { useEffect, useState } from "react";
import { Image as ImageIcon, Info, Lock, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useInternalNav } from "@/contexts/internal-nav-context";
import { toast } from "sonner";
import axios from "@/lib/axios";
import { convertFileToBase64 } from "@/lib/utils";


const GroupFormPage: React.FC = () => {
  const { pop } = useInternalNav();
  const [isLoading, setIsLoading] = useState(false);
  const [base64Image, setBase64Image] = useState<string | null>(null);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [typeAcces, setTypeAcces] = useState("public");
  const [errMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (name.length < 3 || description.length < 10) {
      setErrorMessage(
        "Le nom doit contenir au moins 3 caractères et la description au moins 10 caractères.",
      );
    } else {
      setErrorMessage(null);
    }
  }, [name, description]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const payload = {
        nom: name,
        description: description,
        type_acces: typeAcces,
        image_base64: base64Image,
      };
      await axios.post("network/chat/groupes/", payload);
      setTimeout(() => {
        setIsLoading(false);
        toast.success("Demande de création de groupe envoyée !");
        pop();
      }, 1500);
    } catch (error) {
      toast.error("Une erreur est survenue lors de la création du groupe.");
      console.error("Erreur lors de la création du groupe : ", error);
      setIsLoading(false);
      return;
    }
  };



  const handleFile = () => {
    fileRef.current?.click();
    fileRef.current!.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        const file = target.files[0];
        convertFileToBase64(file)
          .then((base64) => {
            setBase64Image(base64);
          })
          .catch((error) => {
            toast.error(error.message);
            console.error("Erreur de conversion du fichier en base64:", error);
          });
      }
    };
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 mt-2 md:mt-6">
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader className="p-4 md:p-6">
            <CardTitle className="text-lg md:text-xl">
              Informations du Groupe
            </CardTitle>
            <CardDescription>
              Créez un espace de discussion pour votre promotion, ville ou
              centre d'intérêt.
              {errMessage && (
                <div className="bg-destructive/10 border border-destructive dark:border-destructive rounded-lg p-4 mt-2 flex gap-3">
                  <Info className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-800 dark:text-amber-200">
                    {errMessage}
                  </p>
                </div>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 p-4 md:p-6 pt-0">
            <div className="space-y-2">
              <Label htmlFor="name">Nom du groupe</Label>
              <Input
                id="name"
                value={name}
                minLength={3}
                onChange={(e) => setName(e.target.value)}
                placeholder="ex: INFOTEL / Club Robotique"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                minLength={10}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Décrivez l'objectif et les activités de ce groupe..."
                className="min-h-24"
                required
              />
            </div>

            <div className="space-y-3">
              <Label>Type de visibilité</Label>
              <RadioGroup
                value={typeAcces}
                onValueChange={setTypeAcces}
                className="grid grid-cols-1 sm:grid-cols-2 gap-4"
              >
                <div>
                  <RadioGroupItem
                    value="public"
                    id="public"
                    className="peer sr-only"
                   
                  />
                  <Label
                    htmlFor="public"
                    className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                  >
                    <Globe className="mb-2 h-6 w-6" />
                    <span className="font-semibold">Public</span>
                    <span className="text-xs text-muted-foreground text-center mt-1">
                      Tout le monde peut voir et rejoindre le groupe.
                    </span>
                  </Label>
                </div>
                <div>
                  <RadioGroupItem
                    value="prive"
                    id="prive"
                    className="peer sr-only"
                  />
                  <Label
                    htmlFor="prive"
                    className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                  >
                    <Lock className="mb-2 h-6 w-6" />
                    <span className="font-semibold">Privé</span>
                    <span className="text-xs text-muted-foreground text-center mt-1">
                      L'accès nécessite une approbation des administrateurs.
                    </span>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            <div className="space-y-2">
              <Label>Image de couverture (Optionnel)</Label>
              <div
                onClick={handleFile}
                className="border-2 border-dashed rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
              >
                {base64Image ? (
                  <img
                    src={base64Image}
                    alt="Aperçu de l'image de couverture"
                    className="mx-auto max-h-48 object-contain"
                    onError={(e) => {
                      console.log("Invalid image : ", e);
                    }}
                  />
                ) : (
                  <>
                    <ImageIcon className="mx-auto h-10 w-10 text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">
                      Cliquez pour télécharger une image
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      PNG, JPG jusqu'à 5 Mo
                    </p>
                  </>
                )}

                <input
                  type="file"
                  className="hidden"
                  ref={fileRef}
                  accept="image/*"
                />
              </div>
            </div>

            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-lg p-4 flex gap-3">
              <Info className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800 dark:text-amber-200">
                La création d'un groupe est soumise à validation par l'équipe
                administrative de l'ENSPM Hub.
              </p>
            </div>
          </CardContent>
          <CardFooter className="p-4 md:p-6 border-t bg-muted/30">
            <div className="flex flex-col sm:flex-row gap-3 w-full">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={pop}
              >
                Annuler
              </Button>
              <Button type="submit" className="flex-1" disabled={isLoading}>
                {isLoading ? "Envoi en cours..." : "Soumettre la création"}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
};

export default GroupFormPage;
