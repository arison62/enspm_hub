import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MapPin, Link as LinkIcon, Info, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

// Types communs
export type CountryOption = {
  code: string;
  name: string;
};

export type DeviseOption = {
  id: string;
  code: string;
  symbol: string;
  nom: string;
};

// Props de base pour tous les formulaires
export interface BaseFormProps {
  countries: CountryOption[];
  devises: DeviseOption[];
  onDescriptionChange?: (html: string) => void;
  className?: string;
}

// Section de localisation réutilisable
export const LocationSection = ({
  countries,
  values,
  onChange,
  errors = {},
}: {
  countries: CountryOption[];
  values: {
    adresse: string;
    ville: string;
    pays: string;
  };
  onChange: (field: string, value: string) => void;
  errors?: Record<string, string>;
}) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div className="space-y-2 relative">
      <Label htmlFor="adresse">
        Adresse <span className="text-destructive">*</span>
      </Label>
      <div className="relative">
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          id="adresse"
          name="adresse"
          value={values.adresse}
          onChange={(e) => onChange("adresse", e.target.value)}
          placeholder="ex: Immeuble Technopole, 3ème étage"
          className={cn("pl-10 h-12", errors.adresse && "border-destructive")}
        />
        {errors.adresse && (
          <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
            <AlertCircle className="h-3 w-3" /> {errors.adresse}
          </p>
        )}
      </div>
    </div>

    <div className="space-y-2">
      <Label htmlFor="ville">Ville</Label>
      <Input
        id="ville"
        name="ville"
        value={values.ville}
        onChange={(e) => onChange("ville", e.target.value)}
        placeholder="ex: Yaoundé"
        className="h-12"
      />
    </div>

    <div className="space-y-2">
      <Label htmlFor="pays">
        Pays <span className="text-destructive">*</span>
      </Label>
      <Select
        name="pays"
        value={values.pays}
        onValueChange={(value) => onChange("pays", value)}
      >
        <SelectTrigger
          className={cn("h-12", errors.pays && "border-destructive")}
        >
          <SelectValue placeholder="Sélectionner un pays" />
        </SelectTrigger>
        <SelectContent>
          {countries.map((country) => (
            <SelectItem key={country.code} value={country.code}>
              {country.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {errors.pays && (
        <p className="text-[0.75rem] text-destructive flex items-center gap-1 mt-1">
          <AlertCircle className="h-3 w-3" /> {errors.pays}
        </p>
      )}
    </div>
  </div>
);

// Section de contact réutilisable
export const ContactSection = ({
  values,
  onChange,
}: {
  values: {
    email_contact: string;
    telephone_contact: string;
  };
  onChange: (field: string, value: string) => void;
}) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div className="space-y-2">
      <Label htmlFor="email_contact">Email de contact</Label>
      <Input
        id="email_contact"
        type="email"
        name="email_contact"
        value={values.email_contact}
        onChange={(e) => onChange("email_contact", e.target.value)}
        placeholder="contact@organisation.com"
        className="h-12"
      />
    </div>

    <div className="space-y-2">
      <Label htmlFor="telephone_contact">Téléphone</Label>
      <Input
        id="telephone_contact"
        type="tel"
        name="telephone_contact"
        pattern="^\\+\\d+"
        value={values.telephone_contact}
        onChange={(e) => onChange("telephone_contact", e.target.value)}
        placeholder="+237 6XX XXX XXX"
        className="h-12"
      />
    </div>
  </div>
);

// Section de liens réutilisable
export const LinksSection = ({
  values,
  onChange,
  labels = {
    lien_offre_original: "Lien offre originale",
    lien_candidature: "Lien candidature",
  },
}: {
  values: {
    lien_offre_original: string;
    lien_candidature: string;
  };
  onChange: (field: string, value: string) => void;
  labels?: {
    lien_offre_original?: string;
    lien_candidature?: string;
  };
}) => (
  <div className="space-y-4">
    <div className="space-y-2">
      <Label htmlFor="lien_offre_original">{labels.lien_offre_original}</Label>
      <div className="relative">
        <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          id="lien_offre_original"
          name="lien_offre_original"
          value={values.lien_offre_original}
          onChange={(e) => onChange("lien_offre_original", e.target.value)}
          placeholder="https://example.com/offre"
          className="pl-10 h-12"
        />
      </div>
    </div>

    <div className="space-y-2">
      <Label htmlFor="lien_candidature">{labels.lien_candidature}</Label>
      <div className="relative">
        <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          id="lien_candidature"
          name="lien_candidature"
          value={values.lien_candidature}
          onChange={(e) => onChange("lien_candidature", e.target.value)}
          placeholder="https://example.com/candidature"
          className="pl-10 h-12"
        />
      </div>
    </div>
  </div>
);

// Section de dates réutilisable
export const DatesSection = ({
  values,
  onChange,
  showExpiration = true,
  showStart = true,
}: {
  values: {
    date_debut?: string;
    date_fin?: string;
    date_expiration?: string;
  };
  onChange: (field: string, value: string) => void;
  showExpiration?: boolean;
  showStart?: boolean;
}) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    {showStart && (
      <div className="space-y-2">
        <Label htmlFor="date_debut">Date de début</Label>
        <Input
          name="date_debut"
          id="date_debut"
          type="date"
          value={values.date_debut || ""}
          onChange={(e) => onChange("date_debut", e.target.value)}
          className="h-12"
        />
      </div>
    )}

    {showExpiration && (
      <div className="space-y-2">
        <Label className="flex items-center gap-2" htmlFor="date_expiration">
          Date d'expiration <span className="text-destructive">*</span>
          <Info className="h-3 w-3 text-amber-500" />
        </Label>
        <Input
          id="date_expiration"
          type="date"
          name="date_expiration"
          value={values.date_expiration || ""}
          onChange={(e) => onChange("date_expiration", e.target.value)}
          required
          className="h-12 border-primary/50 focus-visible:ring-primary"
        />
        <p className="text-[11px] text-muted-foreground">
          L'offre sera archivée après cette date.
        </p>
      </div>
    )}
  </div>
);
