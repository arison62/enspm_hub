import React, { useState } from "react";
import { ChevronLeft, Image as ImageIcon, Info, Lock, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useInternalNav } from "@/contexts/internal-nav-context";
import { toast } from "sonner";

const GroupFormPage: React.FC = () => {
  const { pop } = useInternalNav();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      toast.success("Demande de création de groupe envoyée !");
      pop();
    }, 1500);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={pop} className="h-8 w-8">
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-xl md:text-2xl font-bold tracking-tight">Créer un nouveau groupe</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader className="p-4 md:p-6">
            <CardTitle className="text-lg md:text-xl">Informations du Groupe</CardTitle>
            <CardDescription>
              Créez un espace de discussion pour votre promotion, ville ou centre d'intérêt.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 p-4 md:p-6 pt-0">
            <div className="space-y-2">
              <Label htmlFor="name">Nom du groupe</Label>
              <Input id="name" placeholder="ex: Alumni Paris / Club Robotique" required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Décrivez l'objectif et les activités de ce groupe..."
                className="min-h-24"
                required
              />
            </div>

            <div className="space-y-3">
              <Label>Type de visibilité</Label>
              <RadioGroup defaultValue="public" className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <RadioGroupItem value="public" id="public" className="peer sr-only" />
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
                  <RadioGroupItem value="private" id="private" className="peer sr-only" />
                  <Label
                    htmlFor="private"
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
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer">
                <ImageIcon className="mx-auto h-10 w-10 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">Cliquez pour télécharger une image</p>
                <p className="text-xs text-muted-foreground mt-1">PNG, JPG jusqu'à 5 Mo</p>
              </div>
            </div>

            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-lg p-4 flex gap-3">
              <Info className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800 dark:text-amber-200">
                La création d'un groupe est soumise à validation par l'équipe administrative de l'ENSPM Hub.
              </p>
            </div>
          </CardContent>
          <CardFooter className="p-4 md:p-6 border-t bg-muted/30">
            <div className="flex flex-col sm:flex-row gap-3 w-full">
              <Button type="button" variant="outline" className="flex-1" onClick={pop}>
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
