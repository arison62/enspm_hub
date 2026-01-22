import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Search, Filter, SlidersHorizontal } from "lucide-react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useInternalNav } from "@/contexts/internal-nav-context";
import InternshipCreatePage from "./internship-create";
import FilterContent from "../../components/opportunities/filter-internship-card";
import axios from "@/lib/axios";
import type { TypeStage } from "@/types/opportunities";

type OptionType = {
  label: string;
  value: string;
};

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

function InternshipsHome() {
  const { push } = useInternalNav();
  const containerRef = useRef<HTMLDivElement>(null);

  // États de base
  const [secteurs, setSecteurs] = useState<SecteurType[]>([]);
  const [filieres, setFilieres] = useState<FiliereType[]>([]);

  // Calculs dérivés optimisés avec useMemo
  const secteursData = useMemo<OptionType[]>(
    () =>
      secteurs.map((secteur) => ({
        label: secteur.nom,
        value: secteur.id,
      })),
    [secteurs],
  );

  const filieresData = useMemo<OptionType[]>(
    () =>
      filieres.map((filiere) => ({
        label: filiere.nom,
        value: filiere.id,
      })),
    [filieres],
  );

  const domaines = useMemo<OptionType[]>(() => {
    const uniqueDomaines = new Map<string, OptionType>();

    filieres.forEach((filiere) => {
      if (!uniqueDomaines.has(filiere.domaine_id)) {
        uniqueDomaines.set(filiere.domaine_id, {
          label: filiere.domaine_nom,
          value: filiere.domaine_id,
        });
      }
    });

    return Array.from(uniqueDomaines.values());
  }, [filieres]);

  // États des sélections avec type partagé
  const [selectedFilieres, setSelectedFilieres] = useState<OptionType[]>([]);
  const [selectedSecteurs, setSelectedSecteurs] = useState<OptionType[]>([]);
  const [selectedDomaines, setSelectedDomaines] = useState<OptionType[]>([]);
  const [isReferencesLoading, setIsReferencesLoading] = useState(true);
  const [types, setTypes] = useState<TypeStage[]>([]);
  console.log(selectedDomaines);
  useEffect(() => {
    async function getReferences() {
      setIsReferencesLoading(true);
      try {
        const secteursResponse = axios.get("/references/secteurs");
        const filieresResponse = axios.get("/references/filieres");

        const [secteursData, filieresData] = await Promise.all([
          secteursResponse,
          filieresResponse,
        ]);
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
        setIsReferencesLoading(false);
      }
    }
    getReferences();
  }, []);
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
    { scope: containerRef },
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
                Espace stage
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
              onClick={() => {
                push(InternshipCreatePage, "Creer stage");
              }}
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
          <aside className="hidden lg:block lg:col-span-4 space-y-6 filter-panel sticky top-24">
            <Card className="border-none shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Filter className="h-4 w-4" /> Filtres
                </CardTitle>
              </CardHeader>
              <CardContent>
                <FilterContent
                  isLoading={isReferencesLoading}
                  typeStage={types}
                  domaines={domaines}
                  secteurs={secteursData}
                  filieres={filieresData}
                  selectedDomaines={selectedDomaines}
                  selectedSecteurs={selectedSecteurs}
                  selectedFilieres={selectedFilieres}
                  onChangeDomaine={setSelectedDomaines}
                  onChangeSecteur={setSelectedSecteurs}
                  onChangeFiliere={setSelectedFilieres}
                  onChangeTypeStage={setTypes}
                  setClearFilters={() => {}}
                />
              </CardContent>
            </Card>
          </aside>

          {/* CONTENU PRINCIPAL */}
          <main className="lg:col-span-8 space-y-6">
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
                    <FilterContent
                      isLoading={isReferencesLoading}
                      typeStage={types}
                      domaines={domaines}
                      secteurs={secteursData}
                      filieres={filieresData}
                      selectedDomaines={selectedDomaines}
                      selectedSecteurs={selectedSecteurs}
                      selectedFilieres={selectedFilieres}
                      onChangeDomaine={setSelectedDomaines}
                      onChangeSecteur={setSelectedSecteurs}
                      onChangeFiliere={setSelectedFilieres}
                      onChangeTypeStage={setTypes}
                      setClearFilters={() => {}}
                    />
                  </ScrollArea>
                </SheetContent>
              </Sheet>
            </div>

            {/* LISTE DES OFFRES */}
            <div className="grid grid-cols-1 gap-4"></div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default InternshipsHome;
