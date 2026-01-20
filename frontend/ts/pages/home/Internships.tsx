import AppLayout from "@/components/layouts/app-layout";
import type { ReactNode } from "react";
import { useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Search,
  MapPin,
  Clock,
  GraduationCap,
  Building2,
  Filter,
  ArrowUpRight,
  SlidersHorizontal,
} from "lucide-react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";

// --- Types ---
interface Stage {
  id: string;
  titre: string;
  entreprise: string;
  secteur: string;
  departement: string;
  niveau: "Bac+2" | "Bac+3" | "Bac+4" | "Bac+5";
  typeStage: "PFE" | "Technique" | "Ouvrier" | "Académique";
  lieu: string;
  duree: string;
  dateDebut: string;
  remunere: boolean;
}

const MOCK_STAGES: Stage[] = [
  {
    id: "1",
    titre: "Optimisation des procédés de raffinage",
    entreprise: "SONARA",
    secteur: "Pétrole & Gaz",
    departement: "Production",
    niveau: "Bac+5",
    typeStage: "PFE",
    lieu: "Limbe",
    duree: "6 mois",
    dateDebut: "Février 2026",
    remunere: true,
  },
  {
    id: "2",
    titre: "Maintenance préventive des turbines",
    entreprise: "Eneo Cameroon",
    secteur: "Énergie",
    departement: "Maintenance",
    niveau: "Bac+3",
    typeStage: "Technique",
    lieu: "Edéa",
    duree: "3 mois",
    dateDebut: "Juillet 2026",
    remunere: true,
  },
  {
    id: "3",
    titre: "Analyse de données géophysiques",
    entreprise: "SNH",
    secteur: "Mines & Géologie",
    departement: "Exploration",
    niveau: "Bac+5",
    typeStage: "PFE",
    lieu: "Yaoundé",
    duree: "6 mois",
    dateDebut: "Mars 2026",
    remunere: false,
  },
];

// --- Sous-composant pour le contenu des filtres (Réutilisable) ---
const FilterContent = () => (
  <div className="space-y-6 py-4 lg:py-0">
    {/* Département */}
    <div className="space-y-3">
      <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Département
      </Label>
      <div className="space-y-2">
        {["Génie Civil", "Mines & Pétrole", "Électricité", "Production"].map(
          (dep) => (
            <div key={dep} className="flex items-center space-x-2">
              <Checkbox id={`dep-${dep}`} />
              <label
                htmlFor={`dep-${dep}`}
                className="text-sm font-medium leading-none cursor-pointer"
              >
                {dep}
              </label>
            </div>
          )
        )}
      </div>
    </div>

    <Separator />

    {/* Secteurs avec ScrollArea */}
    <div className="space-y-3">
      <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Spécialités & Secteurs
      </Label>
      <ScrollArea className="h-[180px] pr-4">
        <div className="space-y-3">
          {[
            "Énergies Renouvelables",
            "Génie Logiciel",
            "Hydraulique",
            "Intelligence Artificielle",
            "Logistique",
            "Matériaux",
            "Réseaux & Télécoms",
            "Sécurité Industrielle",
            "Traitement des Eaux",
          ].map((sect) => (
            <div key={sect} className="flex items-center space-x-2">
              <Checkbox id={`sect-${sect}`} />
              <label
                htmlFor={`sect-${sect}`}
                className="text-sm font-medium leading-none cursor-pointer"
              >
                {sect}
              </label>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>

    <Separator />

    {/* Niveau d'études */}
    <div className="space-y-3">
      <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Niveau d'études
      </Label>
      <div className="grid grid-cols-2 gap-2">
        {["Bac+2", "Bac+3", "Bac+4", "Bac+5"].map((niv) => (
          <Button key={niv} variant="outline" size="sm" className="text-xs h-8">
            {niv}
          </Button>
        ))}
      </div>
    </div>

    <Separator />

    {/* Type de stage */}
    <div className="space-y-3">
      <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Type de stage
      </Label>
      <div className="space-y-2">
        {["PFE (Fin d'études)", "Stage Technique", "Stage Ouvrier"].map(
          (type) => (
            <div key={type} className="flex items-center space-x-2">
              <Checkbox id={`type-${type}`} />
              <label
                htmlFor={`type-${type}`}
                className="text-sm font-medium leading-none cursor-pointer"
              >
                {type}
              </label>
            </div>
          )
        )}
      </div>
    </div>

    <Button className="w-full mt-4" variant="secondary">
      Réinitialiser
    </Button>
  </div>
);

function InternshipsPage() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      gsap.from(".filter-panel", {
        x: -30,
        opacity: 0,
        duration: 0.8,
        ease: "power3.out",
      });
      gsap.from(".stage-card", {
        y: 20,
        opacity: 0,
        stagger: 0.1,
        duration: 0.5,
        delay: 0.2,
        ease: "power2.out",
      });
    },
    { scope: containerRef }
  );

  return (
    <div
      className="min-h-screen bg-slate-50/50 dark:bg-zinc-950"
      ref={containerRef}
    >
      {/* HEADER */}
      <div className="bg-white dark:bg-zinc-900 border-b">
        <div className="container mx-auto px-4 py-6 md:py-10 max-w-7xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border-none">
                Espace Étudiants & Entreprises
              </Badge>
              <h1 className="text-2xl md:text-4xl font-bold tracking-tight">
                Portail des Stages ENSPM
              </h1>
              <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
                Trouvez le stage idéal parmi les offres de nos entreprises
                partenaires.
              </p>
            </div>
            <Button
              size="lg"
              className="w-full md:w-auto shadow-lg shadow-blue-500/20"
            >
              Déposer une offre
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 md:py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* SIDEBAR DESKTOP (Masquée sur mobile) */}
          <aside className="hidden lg:block lg:col-span-3 space-y-6 filter-panel sticky top-24">
            <Card className="border-none shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Filter className="h-4 w-4" /> Filtres
                </CardTitle>
              </CardHeader>
              <CardContent>
                <FilterContent />
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white border-none shadow-md">
              <CardContent className="p-5 space-y-3">
                <h4 className="font-bold text-sm">Guide du CV</h4>
                <p className="text-[11px] text-blue-100">
                  Réussissez votre candidature d'ingénieur.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs font-bold"
                >
                  Consulter
                </Button>
              </CardContent>
            </Card>
          </aside>

          {/* CONTENU PRINCIPAL */}
          <main className="lg:col-span-9 space-y-6">
            {/* SEARCH + MOBILE FILTERS TRIGGER */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1 group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground group-focus-within:text-blue-500 transition-colors" />
                <Input
                  placeholder="Rechercher un stage..."
                  className="pl-12 h-12 bg-white dark:bg-zinc-900 border-none shadow-sm rounded-xl"
                />
              </div>

              {/* TRIGGER MOBILE SHEET */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button
                    variant="outline"
                    className="lg:hidden h-12 gap-2 rounded-xl bg-white dark:bg-zinc-900"
                  >
                    <SlidersHorizontal className="h-4 w-4" />
                    Filtres
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-[300px] sm:w-[400px]">
                  <SheetHeader className="text-left">
                    <SheetTitle>Filtres de recherche</SheetTitle>
                  </SheetHeader>
                  <ScrollArea className="h-[calc(100vh-100px)] mt-4 p-2">
                    <FilterContent />
                  </ScrollArea>
                </SheetContent>
              </Sheet>
            </div>

            {/* LISTE DES OFFRES */}
            <div className="grid grid-cols-1 gap-4">
              {MOCK_STAGES.map((stage) => (
                <Card
                  key={stage.id}
                  className="stage-card border-none shadow-sm hover:shadow-md transition-all group bg-white dark:bg-zinc-900 overflow-hidden"
                >
                  <div className="flex flex-col sm:flex-row">
                    {/* Logo/Initiale */}
                    <div className="w-full sm:w-24 md:w-32 bg-slate-50 dark:bg-zinc-800 flex items-center justify-center py-6 sm:py-0">
                      <div className="size-12 md:size-16 rounded-xl bg-white dark:bg-zinc-700 shadow-sm flex items-center justify-center text-xl font-bold text-blue-600">
                        {stage.entreprise[0]}
                      </div>
                    </div>

                    <div className="flex-1 p-5 md:p-6">
                      <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-base md:text-lg font-bold group-hover:text-blue-600 transition-colors">
                              {stage.titre}
                            </h3>
                            {stage.typeStage === "PFE" && (
                              <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 border-none text-[10px]">
                                PFE
                              </Badge>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs md:text-sm text-muted-foreground">
                            <span className="flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                              <Building2 className="h-3.5 w-3.5" />{" "}
                              {stage.entreprise}
                            </span>
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3.5 w-3.5" /> {stage.lieu}
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="hidden md:flex gap-2 text-xs font-bold border-blue-100 text-blue-600"
                        >
                          Détails <ArrowUpRight className="h-3.5 w-3.5" />
                        </Button>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-slate-50 dark:border-zinc-800">
                        <Badge
                          variant="secondary"
                          className="text-[9px] md:text-[10px] bg-slate-100 dark:bg-zinc-800 font-normal"
                        >
                          {stage.departement}
                        </Badge>
                        <div className="hidden sm:block flex-1" />
                        <div className="flex items-center gap-3 text-[10px] md:text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" /> {stage.duree}
                          </span>
                          <span className="flex items-center gap-1">
                            <GraduationCap className="h-3 w-3" /> {stage.niveau}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            <div className="flex justify-center pt-4">
              <Button variant="ghost" className="text-muted-foreground text-sm">
                Voir plus d'offres
              </Button>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

InternshipsPage.layout = (page: ReactNode) => <AppLayout>{page}</AppLayout>;
export default InternshipsPage;
