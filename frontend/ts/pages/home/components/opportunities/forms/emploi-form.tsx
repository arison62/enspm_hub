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
  Info,
  AlertCircle,
  Briefcase,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  type BaseFormProps,
  LocationSection,
  DatesSection,
  LinksSection,
  ContactSection,
} from "./base-opportunity-form";

export interface EmploiFormData {
  titre: string;
  organisation: string;
  nom_structure: string;
  description: string;
  type_emploi: string;
  adresse: string;
  ville: string;
  pays: string;
  email_contact: string;
  telephone_contact: string;
  lien_offre_original: string;
  lien_candidature: string;
  salaire_min: string;
  salaire_max: string;
  devise: string;
  date_expiration: string;
}

export const EmploiForm = ({
  countries,
  devises,
  onDescriptionChange,
  className,
}: BaseFormProps) => {
  const [formData, setFormData] = useState<EmploiFormData>({
    titre: "",
    organisation: "",
    nom_structure: "",
    description: "",
    type_emploi: "",
    adresse: "",
    ville: "",
    pays: "",
    email_contact: "",
    telephone_contact: "",
    lien_offre_original: "",
    lien_candidature: "",
    salaire_min: "",
    salaire_max: "",
    devise: devises[0]?.code || "XAF",
    date_expiration: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValid, setIsValid] = useState(false);
  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {};
    if (!formData.titre.trim()) newErrors.titre = "Ce champ est requis";
    if (!formData.adresse.trim()) newErrors.adresse = "Ce champ est requis";
    if (!formData.pays) newErrors.pays = "Sélectionner un pays";
    if (!formData.date_expiration)
      newErrors.date_expiration = "Ce champ est requis";

    // Validation de la description
    if (new DOMParser().parseFromString(formData.description, "text/html").body
      .textContent?.trim().length <= 10) {
      newErrors.description = "Ce champ doit contenir au moins 10 caractères";
    }

    // Validation des salaires
    const min = parseFloat(formData.salaire_min);
    const max = parseFloat(formData.salaire_max);
    if (!isNaN(min) && !isNaN(max) && min > max) {
      newErrors.salaire_max = "Doit être supérieur au salaire minimum";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  useEffect(() => {
    setIsValid(validate());
  }, [validate]);

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
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
        title="Informations du poste"
        icon={<FileText className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="titre">
              Intitulé du poste <span className="text-destructive">*</span>
            </Label>
            <Input
              id="titre"
              name="titre"
              value={formData.titre}
              onChange={(e) => handleChange("titre", e.target.value)}
              placeholder="ex: Développeur Backend Senior"
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

      {/* Section type d'emploi */}
      <FormSection
        title="Conditions de l'offre"
        icon={<Briefcase className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label>Type de contrat</Label>
            <Select
              value={formData.type_emploi}
              name="type_emploi"
              defaultValue="temps_plein_terrain"
              onValueChange={(value) => handleChange("type_emploi", value)}
            >
              <SelectTrigger className="h-12">
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="temps_plein_terrain">
                  Temps plein terrain
                </SelectItem>
                <SelectItem value="temps_partiel_terrain">
                  Temps partiel terrain
                </SelectItem>
                <SelectItem value="temps_plein_ligne">
                  Temps plein en ligne
                </SelectItem>
                <SelectItem value="temps_partiel_ligne">
                  Temps partiel en ligne
                </SelectItem>
                <SelectItem value="freelance">Freelance</SelectItem>
                <SelectItem value="contrat">Contrat</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Politique télétravail</Label>
            <Select defaultValue="hybrid">
              <SelectTrigger className="h-12">
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="onsite">Sur site</SelectItem>
                <SelectItem value="hybrid">Hybride</SelectItem>
                <SelectItem value="remote">Full Remote</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="md:col-span-2 space-y-2">
            <Label>Salaire (mensuel)</Label>
            <div className="flex items-center gap-4">
              <Input
                type="number"
                name="salaire_min"
                value={formData.salaire_min}
                onChange={(e) => handleChange("salaire_min", e.target.value)}
                placeholder="Min"
                className={cn(
                  "h-12 bg-background",
                  errors.salaire_min && "border-destructive"
                )}
              />
              <span className="text-muted-foreground font-medium">-</span>
              <Input
                type="number"
                name="salaire_max"
                value={formData.salaire_max}
                onChange={(e) => handleChange("salaire_max", e.target.value)}
                placeholder="Max"
                className={cn(
                  "h-12 bg-background",
                  errors.salaire_max && "border-destructive"
                )}
              />
              <Select
                value={formData.devise}
                defaultValue={"XAF"}
                name="devise"
                onValueChange={(value) => handleChange("devise", value)}
              >
                <SelectTrigger className="w-[100px] h-12">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {devises.map((devise) => (
                    <SelectItem key={devise.code} value={devise.code}>
                      {devise.nom}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {errors.salaire_max && (
              <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" /> {errors.salaire_max}
              </p>
            )}
          </div>
        </div>
      </FormSection>

      {/* Section description */}
      <FormSection
        title="Description détaillée"
        icon={<FileText className="h-5 w-5" />}
      >
        <div className="space-y-2">
          <Label>
            À propos <span className="text-destructive">*</span>
          </Label>
          <RichTextEditor
            value={formData.description}
            onChange={(html) => {
              handleChange("description", html);
              onDescriptionChange?.(html);
            }}
            placeholder="Décrivez les missions, le profil recherché, l'environnement de travail..."
          />
          {errors.description && (
            <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
              <AlertCircle className="h-3 w-3" /> {errors.description}
            </p>
          )}
        </div>
      </FormSection>

      {/* Section validité */}
      <FormSection
        title="Validité de l'offre"
        icon={<CalendarClock className="h-5 w-5" />}
        className="bg-muted/30"
      >
        <DatesSection
          values={{
            date_expiration: formData.date_expiration,
          }}
          onChange={handleChange}
          showStart={false}
          showExpiration={true}
        />
      </FormSection>

      {/* Section liens */}
      <FormSection title="Candidature" icon={<Send className="h-5 w-5" />}>
        <LinksSection
          values={{
            lien_offre_original: formData.lien_offre_original,
            lien_candidature: formData.lien_candidature,
          }}
          onChange={handleChange}
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

      <input type="hidden" name="type" value="emploi" />
      <input type="hidden" name="is_valid" value={isValid.toString()} />
    </div>
  );
};

