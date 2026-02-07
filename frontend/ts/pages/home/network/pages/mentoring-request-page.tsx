import React, { useState } from "react";
import { ChevronLeft, Send, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useInternalNav } from "@/contexts/internal-nav-context";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const MentoringRequestPage: React.FC<{ mentor?: any }> = ({ mentor }) => {
  const { pop } = useInternalNav();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      toast.success(`Votre demande a été envoyée à ${mentor?.name || "votre mentor"} !`);
      pop();
    }, 1500);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={pop} className="h-8 w-8">
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-xl md:text-2xl font-bold tracking-tight">Demande de Mentorat</h1>
      </div>

      <div className="flex items-center gap-4 bg-muted/30 p-4 rounded-xl border">
        <Avatar className="h-12 w-12 md:h-16 md:w-16 border-2 border-background">
          <AvatarImage src={mentor?.avatar} />
          <AvatarFallback>{mentor?.name?.[0]}</AvatarFallback>
        </Avatar>
        <div>
          <p className="text-sm text-muted-foreground">Vous contactez</p>
          <h2 className="font-bold text-lg md:text-xl">{mentor?.name || "Mentor"}</h2>
          <p className="text-sm">{mentor?.position} @ {mentor?.company}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader className="p-4 md:p-6">
            <CardTitle className="text-lg md:text-xl">Votre Message</CardTitle>
            <CardDescription>
              Expliquez pourquoi vous souhaitez être accompagné par ce mentor et quels sont vos objectifs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 p-4 md:p-6 pt-0">
            <div className="space-y-2">
              <Label htmlFor="topic">Sujet principal de l'accompagnement</Label>
              <Select required>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionnez un sujet" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="career">Orientation de carrière</SelectItem>
                  <SelectItem value="technical">Expertise technique</SelectItem>
                  <SelectItem value="interview">Préparation d'entretien / CV</SelectItem>
                  <SelectItem value="networking">Networking et réseau</SelectItem>
                  <SelectItem value="other">Autre</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="message">Message d'introduction</Label>
              <Textarea
                id="message"
                placeholder="Bonjour, je suis actuellement étudiant en... et j'aimerais bénéficier de votre expérience sur..."
                className="min-h-40"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="duration">Fréquence souhaitée</Label>
              <Select required>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionnez une fréquence" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="once">Une seule fois (conseils ponctuels)</SelectItem>
                  <SelectItem value="monthly">Une fois par mois</SelectItem>
                  <SelectItem value="regular">Régulièrement (plus d'une fois par mois)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/50 rounded-lg p-4 flex gap-3">
              <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="text-xs font-semibold text-blue-800 dark:text-blue-200">Conseil :</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  Soyez précis dans votre demande. Un message personnalisé augmente considérablement vos chances de réponse positive.
                </p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="p-4 md:p-6 border-t flex flex-col sm:flex-row gap-3">
            <Button type="submit" className="w-full gap-2" disabled={isLoading}>
              {isLoading ? "Envoi..." : (
                <>
                  <Send className="h-4 w-4" />
                  Envoyer la demande
                </>
              )}
            </Button>
            <Button type="button" variant="outline" className="w-full" onClick={pop}>
              Annuler
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
};

export default MentoringRequestPage;
