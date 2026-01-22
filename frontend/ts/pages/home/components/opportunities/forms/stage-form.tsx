import { useState, useCallback, useEffect } from "react";
import { FormSection } from "../form-section";
import RichTextEditor from "@/components/rich-text-editor/rich-text-editor";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  MapPin,
  Building2,
  FileText,
  CalendarClock,
  Link as LinkIcon,
  Info,
  AlertCircle,
  Telescope,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ContactSection,
  DatesSection,
  LinksSection,
  LocationSection,
  type BaseFormProps,
} from "./base-opportunity-form";
import SearchField from "./search-field";

export interface StageFormData {
  titre: string;
  organisation: string;
  nom_structure: string;
  description: string;
  type_stage: "ouvrier" | "academique" | "professionnel";
  adresse: string;
  ville: string;
  pays: string;
  email_contact: string;
  telephone_contact: string;
  lien_offre_original: string;
  lien_candidature: string;
  date_debut: string;
  date_fin: string;
}

type StageFormProps = BaseFormProps & {
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
  onSecteursChange: (items: { label: string; value: string }[]) => void;
  onFilieresChange: (items: { label: string; value: string }[]) => void;
};
export const StageForm = ({
  countries,
  filieres,
  selectedFilieres,
  secteurs,
  selectedSecteurs,
  onFilieresChange,
  onSecteursChange,
  onDescriptionChange,
  className,
}: StageFormProps) => {
  const [formData, setFormData] = useState<StageFormData>({
    titre: "",
    organisation: "",
    nom_structure: "",
    description: "",
    type_stage: "professionnel",
    adresse: "",
    ville: "",
    pays: "",
    email_contact: "",
    telephone_contact: "",
    lien_offre_original: "",
    lien_candidature: "",
    date_debut: "",
    date_fin: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const [isValid, setIsValid] = useState(false);

  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {};
    if (!formData.titre.trim()) newErrors.titre = "Ce champ est requis";
    if (!formData.adresse.trim()) newErrors.adresse = "Ce champ est requis";
    if (!formData.pays) newErrors.pays = "Sélectionner un pays";
    if (!formData.date_fin) newErrors.date_fin = "La date de fin est requise";

    // Validation de la description
    if (
      new DOMParser()
        .parseFromString(formData.description, "text/html")
        .body.textContent?.trim().length <= 10
    ) {
      newErrors.description = "Ce champ doit contenir au moins 10 caractères";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  useEffect(() => {
    setIsValid(validate());
  }, [validate]);
  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error on change
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className={cn("space-y-8", className)}>
      {/* Section informations principales */}
      <FormSection
        title="Informations du stage"
        icon={<FileText className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="titre">
              Titre du stage <span className="text-destructive">*</span>
            </Label>
            <Input
              id="titre"
              name="titre"
              value={formData.titre}
              onChange={(e) => handleChange("titre", e.target.value)}
              placeholder="ex: Stage Développement Fullstack"
              className={cn("h-12", errors.titre && "border-destructive")}
            />
            {errors.titre && (
              <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" /> {errors.titre}
              </p>
            )}
          </div>

          <div className="space-y-2 relative">
            <Label htmlFor="organisation">
              Organisation <span className="text-destructive">*</span>
            </Label>
            <div className="relative">
              <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="organisation"
                name="organisation"
                value={formData.organisation}
                onChange={(e) => handleChange("organisation", e.target.value)}
                placeholder="Rechercher une organisation..."
                className="pl-10 h-12"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="nom_structure">
              Nom de la structure <span className="text-destructive">*</span>
            </Label>
            <Input
              id="nom_structure"
              name="nom_structure"
              value={formData.nom_structure}
              onChange={(e) => handleChange("nom_structure", e.target.value)}
              placeholder="ex: Tech Innovations SARL"
              className="h-12"
            />
          </div>
        </div>
      </FormSection>

      {/* Section localisation */}
      <FormSection
        title="Localisation"
        icon={<MapPin className="h-5 w-5" />}
        className="bg-muted/30"
      >
        <LocationSection
          countries={countries}
          values={{
            adresse: formData.adresse,
            ville: formData.ville,
            pays: formData.pays,
          }}
          onChange={handleChange}
          errors={errors}
        />
      </FormSection>

      {/* Section type de stage */}
      <FormSection
        title="Type de stage"
        icon={<FileText className="h-5 w-5" />}
      >
        <div className="space-y-2">
          <Label htmlFor="type_stage">Type de stage</Label>
          <Select
            name="type_stage"
            value={formData.type_stage}
            onValueChange={(value) =>
              handleChange("type_stage", value as StageFormData["type_stage"])
            }
          >
            <SelectTrigger className="h-12">
              <SelectValue placeholder="Sélectionner un type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ouvrier">Ouvrier</SelectItem>
              <SelectItem value="academique">Académique</SelectItem>
              <SelectItem value="professionnel">Professionnel</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </FormSection>
      <FormSection
        title="Secteur & Domaine"
        icon={<Telescope className="h-5 w-5" />}
      >
        <div>
          <Label htmlFor="filieres">Filieres</Label>
          <SearchField
            items={filieres}
            selectedItems={selectedFilieres}
            onItemsChange={onFilieresChange}
          />
        </div>
        <div>
          <Label htmlFor="secteurs">Secteurs</Label>
          <SearchField
            items={secteurs}
            selectedItems={selectedSecteurs}
            onItemsChange={onSecteursChange}
          />
        </div>
      </FormSection>
      {/* Section description */}
      <FormSection
        title="Description détaillée"
        icon={<FileText className="h-5 w-5" />}
      >
        <div className="space-y-2">
          <Label>
            Description <span className="text-destructive">*</span>
          </Label>
          <RichTextEditor
            value={formData.description}
            onChange={(html) => {
              handleChange("description", html);
              onDescriptionChange?.(html);
            }}
            placeholder="Décrivez les missions, le profil recherché, les compétences requises..."
          />
        </div>
        {errors.description && (
          <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
            <AlertCircle className="h-3 w-3" /> {errors.description}
          </p>
        )}
      </FormSection>

      {/* Section dates */}
      <FormSection
        title="Période du stage"
        icon={<CalendarClock className="h-5 w-5" />}
        className="bg-muted/30"
      >
        <DatesSection
          values={{
            date_debut: formData.date_debut,
            date_fin: formData.date_fin,
          }}
          onChange={handleChange}
          showExpiration={true}
          showStart={true}
        />
      </FormSection>

      {/* Section liens */}
      <FormSection title="Liens utiles" icon={<LinkIcon className="h-5 w-5" />}>
        <LinksSection
          values={{
            lien_offre_original: formData.lien_offre_original,
            lien_candidature: formData.lien_candidature,
          }}
          onChange={handleChange}
          labels={{
            lien_offre_original: "Lien de l'offre originale",
            lien_candidature: "Lien pour candidater",
          }}
        />
      </FormSection>

      {/* Section contact */}
      <FormSection title="Contact" icon={<Info className="h-5 w-5" />}>
        <ContactSection
          values={{
            email_contact: formData.email_contact,
            telephone_contact: formData.telephone_contact,
          }}
          onChange={handleChange}
        />
      </FormSection>

      {/* Validation avant soumission */}
      <input type="hidden" name="type" value="stage" />
      <input type="hidden" name="is_valid" value={isValid.toString()} />
    </div>
  );
};
