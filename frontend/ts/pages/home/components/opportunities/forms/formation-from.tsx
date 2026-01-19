import { useState, useEffect, useCallback } from "react";
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
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ContactSection,
  DatesSection,
  LocationSection,
  type BaseFormProps,
} from "./base-opportunity-form";

export interface FormationFormData {
  titre: string;
  organisation: string;
  nom_structure: string;
  description: string;
  type_formation: "en_ligne" | "presentiel" | "hybride";
  adresse: string;
  ville: string;
  pays: string;
  email_contact: string;
  telephone_contact: string;
  lien_formation: string;
  lien_inscription: string;
  date_debut: string;
  date_fin: string;
  est_payante: boolean;
  prix: string;
  devise: string;
  duree_heures: string;
}



export const FormationForm = ({
  countries,
  devises,
  onDescriptionChange,
  className,
}: BaseFormProps) => {
  const [formData, setFormData] = useState<FormationFormData>({
    titre: "",
    organisation: "",
    nom_structure: "",
    description: "",
    type_formation: "en_ligne",
    adresse: "",
    ville: "",
    pays: "",
    email_contact: "",
    telephone_contact: "",
    lien_formation: "",
    lien_inscription: "",
    date_debut: "",
    date_fin: "",
    est_payante: false,
    prix: "",
    devise: devises[0]?.code || "XAF",
    duree_heures: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValid, setIsValid] = useState(false);

  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {};
    if (!formData.titre.trim()) newErrors.titre = "Ce champ est requis";
    if (!formData.pays) newErrors.pays = "Sélectionner un pays";

    // Validation spécifique pour formations présentielles
    if (formData.type_formation !== "en_ligne" && !formData.adresse.trim()) {
      newErrors.adresse =
        "Ce champ est requis pour les formations présentielles";
    }

    // Validation des prix
    if (formData.est_payante && !formData.prix) {
      newErrors.prix = "Le prix est requis pour une formation payante";
    }
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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Mise à jour automatique de l'adresse pour les formations en ligne
  useEffect(() => {
    if (formData.type_formation === "en_ligne") {
      setFormData((prev) => ({
        ...prev,
        adresse: "Formation entièrement en ligne",
        ville: "",
      }));
    }
  }, [formData.type_formation]);

  return (
    <div className={cn("space-y-8", className)}>
      {/* Section informations principales */}
      <FormSection
        title="Détails de la formation"
        icon={<GraduationCap className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="titre">
              Titre de la formation <span className="text-destructive">*</span>
            </Label>
            <Input
              id="titre"
              name="titre"
              value={formData.titre}
              onChange={(e) => handleChange("titre", e.target.value)}
              placeholder="ex: Certification Cloud AWS"
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
              placeholder="ex: Tech Innovations Academy"
              className="h-12"
            />
          </div>
        </div>
      </FormSection>

      {/* Section format de formation */}
      <FormSection
        title="Modalités de la formation"
        icon={<GraduationCap className="h-5 w-5" />}
        className="bg-muted/30"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label>
              Format <span className="text-destructive">*</span>
            </Label>
            <Select
              value={formData.type_formation}
              name="type_formation"
              onValueChange={(value) =>
                handleChange(
                  "type_formation",
                  value as FormationFormData["type_formation"]
                )
              }
            >
              <SelectTrigger className="h-12">
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en_ligne">En ligne</SelectItem>
                <SelectItem value="presentiel">Présentiel</SelectItem>
                <SelectItem value="hybride">Hybride</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Volume horaire (heures)</Label>
            <Input
              type="number"
              name="duree_heures"
              value={formData.duree_heures}
              onChange={(e) => handleChange("duree_heures", e.target.value)}
              placeholder="ex: 80"
              className="h-12"
            />
          </div>

          <div className="md:col-span-2 space-y-2">
            <Label>Coût de la formation</Label>
            <div className="flex items-center gap-4">
              <Select
                defaultValue="false"
                value={formData.est_payante.toString()}
                name="est_payante"
                onValueChange={(value) =>
                  handleChange("est_payante", value === "true")
                }
              >
                <SelectTrigger className="w-[150px] h-12">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Payante</SelectItem>
                  <SelectItem value="false">Gratuite</SelectItem>
                </SelectContent>
              </Select>

              <Input
                type="number"
                name="prix"
                value={formData.prix}
                onChange={(e) => handleChange("prix", e.target.value)}
                placeholder={formData.est_payante ? "Montant" : "Gratuit"}
                disabled={!formData.est_payante}
                className={cn(
                  "h-12 flex-1",
                  !formData.est_payante && "opacity-50 cursor-not-allowed",
                  errors.prix && "border-destructive"
                )}
              />

              <Select
                value={formData.devise}
                name="devise"
                onValueChange={(value) => handleChange("devise", value)}
                disabled={!formData.est_payante}
              >
                <SelectTrigger
                  className={cn(
                    "w-[100px] h-12",
                    !formData.est_payante && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {devises.map((devise) => (
                    <SelectItem key={devise.id} value={devise.code}>
                      {devise.nom}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {errors.prix && (
              <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" /> {errors.prix}
              </p>
            )}
          </div>
        </div>
      </FormSection>

      {/* Section localisation (conditionnelle) */}
      {formData.type_formation !== "en_ligne" && (
        <FormSection title="Localisation" icon={<MapPin className="h-5 w-5" />}>
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
      )}

      {/* Section description */}
      <FormSection
        title="Description pédagogique"
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
            placeholder="Décrivez le programme, les objectifs pédagogiques, les prérequis..."
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
        title="Calendrier"
        icon={<CalendarClock className="h-5 w-5" />}
        className="bg-muted/30"
      >
        <DatesSection
          values={{
            date_debut: formData.date_debut,
            date_fin: formData.date_fin,
          }}
          onChange={handleChange}
          showExpiration={false}
          showStart={true}
        />
      </FormSection>

      {/* Section liens */}
      <FormSection
        title="Accès à la formation"
        icon={<LinkIcon className="h-5 w-5" />}
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="lien_formation">Lien de la formation</Label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="lien_formation"
                name="lien_formation"
                value={formData.lien_formation}
                onChange={(e) => handleChange("lien_formation", e.target.value)}
                placeholder="https://platforme-formation.com/cours"
                className="pl-10 h-12"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="lien_inscription">Lien d'inscription</Label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="lien_inscription"
                name="lien_inscription"
                value={formData.lien_inscription}
                onChange={(e) =>
                  handleChange("lien_inscription", e.target.value)
                }
                placeholder="https://platforme-formation.com/inscription"
                className="pl-10 h-12"
              />
            </div>
          </div>
        </div>
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

      <input type="hidden" name="type" value="formation" />
      <input type="hidden" name="is_valid" value={isValid.toString()} />
    </div>
  );
};
