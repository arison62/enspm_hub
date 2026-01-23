import { useState, useEffect, useMemo, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Search, Sliders } from "lucide-react";

import { OpportuniteList } from "../../components/opportunities/opportunity-list";
import { MentorCTA } from "../../components/opportunities/mentor-cta";
import OpportunityCreatePage from "./opportunities-create";
import { useInternalNav } from "@/contexts/internal-nav-context";
import {
  useGetOpportunities,
  type Filters,
  type Pagination as PaginationType,
} from "@/api/opportunities";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useDebounce } from "@uidotdev/usehooks";
import FilterCard, {
  type OnChangePrev,
} from "../../components/opportunities/filter-opportunity-card";
import { ScrollArea } from "@/components/ui/scroll-area";

const initialFilters = [
  {
    id: "opportunity_type",
    value: "emploi",
  },
  {
    id: "lieu",
    value: "",
  },
  {
    id: "type_emploi",
    value: new Set<string>(),
  },
  {
    id: "type_formation",
    value: new Set<string>(),
  },
  {
    id: "est_payante",
    value: new Set<boolean>(),
  },
  {
    id: "search",
    value: "",
  },
];
const OpportunitesHome = () => {
  const { push } = useInternalNav();
  
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters[]>(initialFilters);
  const [filterSection, setFilterSection] = useState<"emploi" | "formation">(
    "emploi",
  );

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

  // Pour les checkboxes et sélecteurs (pas de debounce)
  const handleChangeFilter = useCallback((key: string, value: OnChangePrev) => {
    setFilters((prevFilters) => {
      return prevFilters.map((filter) => {
        if (filter.id === key) {
          if (typeof value === "function") {
            return { ...filter, value: value(filter) };
          }
          return { ...filter, value };
        }
        return filter;
      });
    });
  }, []);

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
  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-zinc-950">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* --- Header Section --- */}
        <div className="mb-8 space-y-4">
          <div className="flex flex-col items-start md:flex-row md:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                Opportunités du Réseau
              </h1>
              <p className="text-muted-foreground">
                Trouvez des emplois et formations partagés par la
                communauté.
              </p>
            </div>
            <Button
              onClick={() => {
                push(OpportunityCreatePage, "Publier opportunite");
              }}
              className="mt-4"
            >
              Publier une Opportunité
            </Button>
          </div>

          <div className="flex flex-col gap-4 md:flex-row md:items-center bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-slate-100 dark:border-zinc-800">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher par titre, entreprise..."
                value={search}
                onChange={(e) => handleSearchChange(e)}
                className="pl-10 border-slate-200 max-w-sm"
              />
            </div>
            <Sheet>
              <SheetTrigger className="lg:hidden" asChild>
                <Button variant={"outline"} size={"icon-sm"}>
                  <Sliders className="size-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="lg:hidden">
                <SheetHeader>
                  <SheetTitle>Recherche avancée</SheetTitle>
                </SheetHeader>
                <ScrollArea className="h-[calc(100vh-100px)] mt-4 p-2">
                  <FilterCard
                    filters={filters}
                    clearFilters={clearFilters}
                    currentFilterOpen={filterSection}
                    onCurrentFilterChange={setFilterSection}
                    setFilters={handleChangeFilter}
                  />
                </ScrollArea>
              </SheetContent>
            </Sheet>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 items-start">
          {/* --- Sidebar (Filtres & Pubs) --- */}
          <aside className="hidden lg:flex lg:col-span-3 flex-col gap-6 sticky top-24">
            <FilterCard
              filters={filters}
              clearFilters={clearFilters}
              currentFilterOpen={filterSection}
              onCurrentFilterChange={setFilterSection}
              setFilters={handleChangeFilter}
            />
            <MentorCTA />
          </aside>

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
        </div>
      </div>
    </div>
  );
};

export default OpportunitesHome;
