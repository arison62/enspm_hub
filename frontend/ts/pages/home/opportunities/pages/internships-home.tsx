import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Filter, SlidersHorizontal, SearchIcon } from "lucide-react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useInternalNav } from "@/contexts/internal-nav-context";
import InternshipCreatePage from "./internship-create";
import FilterContent from "../../components/opportunities/filter-internship-card";
import axios from "@/lib/axios";
import {
  useGetOpportunities,
  type Filters,
  type Pagination as PaginationType,
} from "@/api/opportunities";
import type { TypeStage } from "@/types/opportunities";
import { useDebounce } from "@uidotdev/usehooks";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { OpportuniteList } from "../../components/opportunities/opportunity-list";
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group";

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

const initialFilters = [
  {
    id: "opportunity_type",
    value: "stage",
  },
  {
    id: "domaines",
    value: new Set<string>(),
  },
  {
    id: "secteurs",
    value: new Set<string>(),
  },
  {
    id: "filieres",
    value: new Set<string>(),
  },
  {
    id: "type_stage",
    value: new Set<TypeStage>(),
  },
  {
    id: "search",
    value: "",
  },
];

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

  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters[]>(initialFilters);

  // État unique pour la pagination - commence à 1
  const [pagination, setPagination] = useState<PaginationType>({
    pageIndex: 1, // Commence à 1 comme demandé
    pageSize: 12,
    totalItems: 0,
  });

  // Utilisation du hook useDebounce pour la recherche
  const debouncedSearch = useDebounce(search, 300);

  // Mettre à jour les filtres avec les valeurs débouncées
  useEffect(() => {
    setFilters((prev) =>
      prev.map((f) =>
        f.id === "search" ? { ...f, value: debouncedSearch } : f,
      ),
    );
  }, [debouncedSearch]);

  // Récupérer les données avec les filtres et la pagination actuels
  const { data, isLoading } = useGetOpportunities({
    filters,
    pagination,
  });

  // Mettre à jour l'état de pagination quand les données changent
  useEffect(() => {
    if (data) {
      setPagination((prev) => ({
        ...prev,
        totalItems: data.meta.total_items || 0,
      }));
    }
  }, [data]);

  useEffect(() => {
    setFilters(
      (prev) =>
        prev.map((f) =>
          f.id === "secteurs"
            ? { ...f, value: new Set(selectedSecteurs.map((s) => s.value)) }
            : f,
        ),
    )
  },[selectedSecteurs])
  useEffect(() => {
    setFilters(
      (prev) =>
        prev.map((f) =>
          f.id === "filieres"
            ? { ...f, value: new Set(selectedFilieres.map((f) => f.value)) }
            : f,
        ),
    )
  },[selectedFilieres])
  useEffect(() => {
    setFilters(
      (prev) =>
        prev.map((f) =>
          f.id === "domaines"
            ? { ...f, value: new Set(selectedDomaines.map((d) => d.value)) }
            : f,
        ),
    )
  }, [selectedDomaines])
  useEffect(() => {
    setFilters(
      (prev) =>
        prev.map((f) =>
          f.id === "type_stage"
            ? { ...f, value: new Set(types.map((t) => t)) }
            : f,
        ),
    )
  }, [types])
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value);
    },
    [],
  );
  // Réinitialiser les filtres
  const clearFilters = useCallback(() => {
    setFilters(initialFilters);
    setSearch("");
  }, []);

  // Gérer le changement de page - commence à 1
  const handlePageChange = useCallback((newPage: number) => {
    setPagination((prev) => ({
      ...prev,
      pageIndex: newPage,
    }));
  }, []);

  // Nombre total de pages
  const pageCount = useMemo(() => {
    return Math.ceil(pagination.totalItems / pagination.pageSize);
  }, [pagination.totalItems, pagination.pageSize]);

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
        <div className="grid grid-cols-1 lg:grid-cols-18 gap-8 items-start">
          {/* SIDEBAR DESKTOP (Masquée sur mobile) */}
          <aside className="hidden lg:block lg:col-span-5 space-y-6 filter-panel sticky top-24">
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
                  setClearFilters={clearFilters}
                />
              </CardContent>
            </Card>
          </aside>

          {/* CONTENU PRINCIPAL */}
          <main className="lg:col-span-13 space-y-6">
            {/* SEARCH + MOBILE FILTERS TRIGGER */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1 group w-full">
                <InputGroup className="w-fit mx-auto">
                  <InputGroupAddon>
                    <SearchIcon aria-hidden="true" />
                  </InputGroupAddon>
                  <InputGroupInput
                    aria-label="Recherche"
                    placeholder="Recherche..."
                    type="search"
                    onChange={(e) => handleSearchChange(e)}
                  />
                </InputGroup>
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
                  <ScrollArea
                    className="h-[calc(100vh-100px)] mt-4 p-2"
                    scrollFade
                    scrollbarGutter
                  >
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
                      setClearFilters={clearFilters}
                    />
                  </ScrollArea>
                </SheetContent>
              </Sheet>
            </div>

            {/* --- Main Content --- */}
            <main className="lg:col-span-9 space-y-6">
              {/* Liste isolée avec sa propre logique d'animation */}
              <OpportuniteList items={data.items} loading={isLoading} />

              {/* Pagination */}
              {!isLoading && pagination.totalItems > 0 && (
                <div className="pt-4">
                  <Pagination>
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious
                          className={`cursor-pointer ${
                            pagination.pageIndex === 1
                              ? "pointer-events-none opacity-50"
                              : ""
                          }`}
                          onClick={() =>
                            handlePageChange(pagination.pageIndex - 1)
                          }
                        />
                      </PaginationItem>

                      {[...Array(Math.min(5, pageCount))].map((_, index) => {
                        const page = index + 1; // Commence à 1
                        if (page >= 1 && page <= pageCount) {
                          return (
                            <PaginationItem key={page}>
                              <Button
                                variant={
                                  pagination.pageIndex === page
                                    ? "default"
                                    : "outline"
                                }
                                size="sm"
                                onClick={() => handlePageChange(page)}
                                className="w-8 h-8 p-0"
                              >
                                {page}
                              </Button>
                            </PaginationItem>
                          );
                        }
                        return null;
                      })}

                      {pageCount > 5 && (
                        <>
                          {pagination.pageIndex < pageCount - 3 && (
                            <PaginationItem>
                              <PaginationEllipsis />
                            </PaginationItem>
                          )}
                          {pagination.pageIndex < pageCount - 2 && (
                            <PaginationItem>
                              <Button
                                variant={
                                  pagination.pageIndex === pageCount
                                    ? "default"
                                    : "outline"
                                }
                                size="sm"
                                onClick={() => handlePageChange(pageCount)}
                                className="w-8 h-8 p-0"
                              >
                                {pageCount}
                              </Button>
                            </PaginationItem>
                          )}
                        </>
                      )}

                      <PaginationItem>
                        <PaginationNext
                          className={`cursor-pointer ${
                            pagination.pageIndex >= pageCount
                              ? "pointer-events-none opacity-50"
                              : ""
                          }`}
                          onClick={() =>
                            handlePageChange(pagination.pageIndex + 1)
                          }
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>

                  <div className="mt-2 text-sm text-muted-foreground text-center">
                    Page {pagination.pageIndex} sur {pageCount} (
                    {pagination.totalItems} résultats)
                  </div>
                </div>
              )}
            </main>
          </main>
        </div>
      </div>
    </div>
  );
}

export default InternshipsHome;
