import { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSeparator,
  FieldSet,
} from "@/components/ui/field";

import { useDebounce } from "@uidotdev/usehooks";
import type { Filters } from "@/api/opportunities";

export type OnChangePrev =
  | string
  | boolean
  | number
  | Set<string | number | boolean>
  | ((
      prev: Filters
    ) => string | boolean | number | Set<string | number | boolean>);

export type FilterCardProps = {
  currentFilterOpen: "emploi" | "formation";
  filters: Filters[];
  onFilterChange?: (filters: Filters[]) => void;
  onCurrentFilterChange?: (filter: "emploi" | "formation") => void;
  clearFilters?: () => void;
  setFilters: (key: string, value: OnChangePrev) => void;
  className?: string;
};

const type_emploi = [
  {
    value: "temps_plein_terrain",
    label: "Temps plein sur site",
  },
  {
    value: "temps_partiel_terrain",
    label: "Temps partiel sur site",
  },
  {
    value: "temps_plein_ligne",
    label: "Temps plein ligne",
  },
  {
    value: "temps_partiel_ligne",
    label: "Temps partiel ligne",
  },
  {
    value: "freelance",
    label: "Freelance",
  },
  {
    value: "contrat",
    label: "Contrat",
  },
];
const type_formation = [
  {
    value: "en_ligne",
    label: "En ligne",
  },
  {
    value: "presentiel",
    label: "Présentiel",
  },
  {
    value: "hybride",
    label: "Hybride",
  },
];

const FilterCard = ({
  currentFilterOpen,
  filters,
  clearFilters,
  setFilters,
}: FilterCardProps) => {
  const [emploiOpen, setEmploiOpen] = useState(currentFilterOpen === "emploi");

  // État local pour gérer le debounce du lieu
  const initialLieuValue =
    (filters.find((filter) => filter.id === "lieu")?.value as string) || "";
  const [localLieuValue, setLocalLieuValue] = useState(initialLieuValue);

  // Valeur débouncée
  const debouncedLieuValue = useDebounce(localLieuValue, 300);

  // Synchroniser avec les props quand elles changent
  useEffect(() => {
    const currentLieu =
      (filters.find((filter) => filter.id === "lieu")?.value as string) || "";
    if (currentLieu !== localLieuValue) {
      setLocalLieuValue(currentLieu);
    }
  }, [filters, localLieuValue]);

  // Mettre à jour les filtres avec la valeur débouncée
  useEffect(() => {
    if (debouncedLieuValue !== initialLieuValue) {
      setFilters("lieu", debouncedLieuValue);
    }
  }, [debouncedLieuValue, initialLieuValue, setFilters]);

  return (
    <div className="mt-2">
      <FieldGroup>
        <FieldSet>
          <FieldLegend>Categorie d'opportunité</FieldLegend>
          <FieldDescription>Opportunities du réseau </FieldDescription>
          <FieldGroup>
            <Field>
              <Select
                value={currentFilterOpen}
                onValueChange={(value) => {
                  setEmploiOpen(value === "emploi");
                  setFilters("opportunity_type", value);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Sélectionner" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel>opportunité</SelectLabel>
                    <SelectItem value="emploi">Emplois</SelectItem>
                    <SelectItem value="formation">Formations</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
          </FieldGroup>
        </FieldSet>
        <FieldSeparator />
        <FieldSet>
          <FieldLegend>Localisation</FieldLegend>
          <FieldDescription>Informations de localisation</FieldDescription>
          <FieldGroup>
            <Field>
              <FieldLabel>Lieu</FieldLabel>
              <Input
                value={localLieuValue}
                placeholder="Adresse, ville, pays"
                onChange={(e) => {
                  setLocalLieuValue(e.target.value);
                  // Pas de setFilters ici, le debounce s'en chargera
                }}
              />
            </Field>
          </FieldGroup>
        </FieldSet>
        <FieldSeparator />
        {emploiOpen ? (
          <FieldSet>
            <FieldLegend>Emploi</FieldLegend>
            <FieldDescription>Filtrer les emplois</FieldDescription>
            <FieldGroup>
              <Field orientation={"vertical"}>
                {type_emploi.map((type) => (
                  <div className="flex  gap-2 items-center w-fit">
                    <Checkbox
                      key={type.value}
                      checked={(() => {
                        if (
                          filters.find((filter) => filter.id == "type_emploi")
                            ?.value instanceof Set
                        ) {
                          const currentValue = filters.find(
                            (filter) => filter.id == "type_emploi"
                          )?.value as Set<string>;
                          return currentValue.has(type.value);
                        }
                      })()}
                      onCheckedChange={(value) => {
                        if (typeof value === "boolean" && value === true) {
                          setFilters("type_emploi", (prev) => {
                            if (prev.value instanceof Set) {
                              return new Set([...prev.value, type.value]);
                            }
                            return prev.value;
                          });
                        }
                        if (typeof value === "boolean" && value === false) {
                          setFilters("type_emploi", (prev) => {
                            if (prev.value instanceof Set) {
                              prev.value.delete(type.value);
                              return new Set([...prev.value]);
                            }
                            return prev.value;
                          });
                        }
                      }}
                    />
                    <FieldLabel className="w-fit">{type.label}</FieldLabel>
                  </div>
                ))}
              </Field>
            </FieldGroup>
          </FieldSet>
        ) : (
          <FieldSet>
            <FieldLegend>Formation</FieldLegend>
            <FieldDescription>Filtrer les formations</FieldDescription>
            <FieldGroup>
              <Field orientation={"vertical"}>
                {type_formation.map((type) => (
                  <div className="flex  gap-2 items-center w-fit">
                    <Checkbox
                      key={type.value}
                      checked={(() => {
                        if (
                          filters.find(
                            (filter) => filter.id == "type_formation"
                          )?.value instanceof Set
                        ) {
                          const currentValue = filters.find(
                            (filter) => filter.id == "type_formation"
                          )?.value as Set<string>;
                          return currentValue.has(type.value);
                        }
                      })()}
                      onCheckedChange={(value) => {
                        if (typeof value === "boolean" && value === true) {
                          setFilters("type_formation", (prev) => {
                            if (prev.value instanceof Set) {
                              return new Set([...prev.value, type.value]);
                            }
                            return prev.value;
                          });
                        }
                        if (typeof value === "boolean" && value === false) {
                          setFilters("type_formation", (prev) => {
                            if (prev.value instanceof Set) {
                              prev.value.delete(type.value);
                              return new Set([...prev.value]);
                            }
                            return prev.value;
                          });
                        }
                      }}
                    />
                    <FieldLabel className="w-fit">{type.label}</FieldLabel>
                  </div>
                ))}
              </Field>
            </FieldGroup>
            <Field>
              <div className="flex gap-2 items-center">
                <Checkbox
                  checked={(() => {
                    const currentValue = filters.find(
                      (filter) => filter.id == "est_payante"
                    )?.value as Set<boolean>;
                    return currentValue.has(false);
                  })()}
                  onCheckedChange={(value) => {
                    if (typeof value === "boolean") {
                      setFilters("est_payante", (prev) => {
                        if (prev.value instanceof Set) {
                          if (value === true) {
                            return new Set([...prev.value, false]);
                          }
                          prev.value.delete(false);
                          return new Set([...prev.value]);
                        }
                        return prev.value;
                      });
                    }
                  }}
                />
                <FieldLabel className="w-fit">Gratuit</FieldLabel>
              </div>
              <div className="flex gap-2 items-center">
                <Checkbox
                  checked={(() => {
                    const currentValue = filters.find(
                      (filter) => filter.id == "est_payante"
                    )?.value as Set<boolean>;
                    return currentValue.has(true);
                  })()}
                  onCheckedChange={(value) => {
                    if (typeof value === "boolean") {
                      setFilters("est_payante", (prev) => {
                        if (prev.value instanceof Set) {
                          if (value === true) {
                            return new Set([...prev.value, true]);
                          }
                          prev.value.delete(true);
                          return new Set([...prev.value]);
                        }
                        return prev.value;
                      });
                    }
                  }}
                />
                <FieldLabel className="w-fit">Payante</FieldLabel>
              </div>
            </Field>
          </FieldSet>
        )}
        <FieldSeparator />
        <Button
          onClick={() => {
            clearFilters?.();
          }}
          variant={"outline"}
        >
          Reinitialiser
        </Button>
      </FieldGroup>
    </div>
  );
};

export default FilterCard;


