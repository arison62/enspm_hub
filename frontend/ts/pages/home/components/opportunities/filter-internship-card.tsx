import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import SearchField from "@/components/search-field";

type TypeStage = "ouvrier" | "professionnel" | "academique";

type FilterContentProps = {
  isLoading: boolean;
  typeStage: TypeStage[];
  domaines: {
    label: string;
    value: string;
  }[];
  selectedDomaines: { label: string; value: string }[];
  secteurs: {
    label: string;
    value: string;
  }[];
  selectedSecteurs: { label: string; value: string }[];
  filieres: {
    label: string;
    value: string;
  }[];
  selectedFilieres: { label: string; value: string }[];
  onChangeFiliere: (items: { label: string; value: string }[]) => void;
  onChangeDomaine: (items: { label: string; value: string }[]) => void;
  onChangeSecteur: (items: { label: string; value: string }[]) => void;
  onChangeTypeStage: (typeStage: TypeStage[]) => void;
  setClearFilters: () => void;
};

const FilterContent = ({
  isLoading,
  typeStage,
  domaines,
  selectedDomaines,
  secteurs,
  selectedSecteurs,
  filieres,
  selectedFilieres,
  onChangeDomaine,
  onChangeSecteur,
  onChangeFiliere,
  onChangeTypeStage,
  setClearFilters,
}: FilterContentProps) => (
  <div className="space-y-6 py-4 lg:py-0">
    {/* Département */}
    <div className="space-y-3">
      {isLoading ? (
        <Skeleton className="h-3 w-32" />
      ) : (
        <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
          Département
        </Label>
      )}
      <div className="space-y-2">
        {isLoading ? (
          <Skeleton className="h-10 w-full" />
        ) : (
          <SearchField
            selectedItems={selectedDomaines}
            items={domaines}
            onItemsChange={onChangeDomaine}
          />
        )}
      </div>
    </div>
    <Separator />
    {/* Secteurs avec ScrollArea */}
    <div className="space-y-3">
      {isLoading ? (
        <Skeleton className="h-3 w-48" />
      ) : (
        <ScrollArea className="h-[180px] pr-4">
          <div>
            {isLoading ? (
              <>
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Secteurs
                  </Label>
                  <SearchField
                    selectedItems={selectedSecteurs}
                    items={secteurs}
                    onItemsChange={onChangeSecteur}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Filieres
                  </Label>
                  <SearchField
                    selectedItems={selectedFilieres}
                    items={filieres}
                    onItemsChange={onChangeFiliere}
                  />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
    <Separator />
    {/* Niveau d'études */}
    <div className="space-y-3">
      {isLoading ? (
        <Skeleton className="h-3 w-32" />
      ) : (
        <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
          Type de stage
        </Label>
      )}
      <div className="grid grid-cols-1 gap-2">
        {isLoading ? (
          <>
            <div className="flex items-center space-x-2">
              <Skeleton className="h-5 w-5" />
              <Skeleton className="h-4 w-24" />
            </div>
            <div className="flex items-center space-x-2">
              <Skeleton className="h-5 w-5" />
              <Skeleton className="h-4 w-24" />
            </div>
            <div className="flex items-center space-x-2">
              <Skeleton className="h-5 w-5" />
              <Skeleton className="h-4 w-24" />
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="ouvrier"
                checked={typeStage.includes("ouvrier")}
                onCheckedChange={(checked) => {
                  if (checked) {
                    onChangeTypeStage([...typeStage, "ouvrier"]);
                  } else {
                    onChangeTypeStage(
                      typeStage.filter((type) => type !== "ouvrier"),
                    );
                  }
                }}
              />
              <Label htmlFor="ouvrier">Ouvrier</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="academique"
                checked={typeStage.includes("academique")}
                onCheckedChange={(checked) => {
                  if (checked) {
                    onChangeTypeStage([...typeStage, "academique"]);
                  } else {
                    onChangeTypeStage(
                      typeStage.filter((type) => type !== "academique"),
                    );
                  }
                }}
              />
              <Label htmlFor="academique">Academique</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="professionnel"
                checked={typeStage.includes("professionnel")}
                onCheckedChange={(checked) => {
                  if (checked) {
                    onChangeTypeStage([...typeStage, "professionnel"]);
                  } else {
                    onChangeTypeStage(
                      typeStage.filter((type) => type !== "professionnel"),
                    );
                  }
                }}
              />
              <Label htmlFor="professionnel">Professionnel</Label>
            </div>
          </>
        )}
      </div>
    </div>
    <Separator />
    {isLoading ? (
      <Skeleton className="h-10 w-full" />
    ) : (
      <Button
        className="w-full mt-4"
        variant="secondary"
        onClick={setClearFilters}
      >
        Réinitialiser
      </Button>
    )}
  </div>
);

export default FilterContent;
