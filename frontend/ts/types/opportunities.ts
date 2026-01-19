import type { UUID, DateString, DateTimeString, DeviseSimple } from "./base";
import type { ProfilOut } from "@/types/user";
import type { OrganisationOut } from "@/types/organisation";

// --- Types & Enums ---

export type TypeStage = "ouvrier" | "academique" | "professionnel";

export type StatutOpportunite =
  | "en_attente"
  | "active"
  | "expiree"
  | "pourvue"
  | "rejetee"
  | "annulee";

export type TypeEmploi =
  | "temps_plein_terrain"
  | "temps_partiel_terrain"
  | "temps_plein_ligne"
  | "temps_partiel_ligne"
  | "freelance"
  | "contrat";

export type TypeFormation = "en_ligne" | "presentiel" | "hybride";

// --- Interfaces de Base (Réutilisables) ---

interface BaseOpportunityOut {
  id: UUID;
  createur_profil: ProfilOut| null;
  organisation: OrganisationOut | null;
  titre: string;
  slug: string;
  nom_structure: string;
  description: string;
  adresse: string;
  ville: string | null;
  pays: string | null; // Code ISO (ex: "CM")
  pays_nom: string | null; // Nom complet (ex: "Cameroun")
  email_contact: string | null;
  telephone_contact: string | null;
  date_publication: DateTimeString;
  statut: StatutOpportunite;
  est_valide: boolean;
  validateur_profil: ProfilOut| null;
  date_validation: DateTimeString | null;
  commentaire_validation: string | null;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

// --- Interfaces de Sortie (Out) ---

export interface StageOut extends BaseOpportunityOut {
  type_stage: TypeStage;
  date_debut: DateString | null;
  date_fin: DateString | null;
  lien_offre_original: string | null;
  lien_candidature: string | null;
}

export interface EmploiOut extends BaseOpportunityOut {
  type_emploi: TypeEmploi | null;
  date_expiration: DateString | null;
  salaire_min: number | null;
  salaire_max: number | null;
  devise: DeviseSimple | null;
  lien_offre_original: string | null;
  lien_candidature: string | null;
}

export interface FormationOut extends BaseOpportunityOut {
  type_formation: TypeFormation;
  lien_formation: string | null;
  lien_inscription: string | null;
  date_debut: DateString | null;
  date_fin: DateString | null;
  est_payante: boolean;
  prix: number | null;
  devise: DeviseSimple | null;
  duree_heures: number | null;
}

// --- Interfaces de Création (Create) ---

export interface StageCreate {
  titre: string;
  nom_structure: string;
  description: string;
  type_stage: TypeStage;
  adresse: string;
  ville?: string | null;
  pays?: string | null;
  email_contact?: string | null;
  telephone_contact?: string | null;
  lien_offre_original?: string | null;
  lien_candidature?: string | null;
  date_debut?: DateString | null;
  date_fin?: DateString | null;
  organisation_id?: UUID | null; // ID de l'organisation si posté au nom d'une entité
}

export interface EmploiCreate {
  titre: string;
  nom_structure: string;
  description: string;
  type_emploi: TypeEmploi;
  adresse: string;
  ville?: string | null;
  pays?: string | null;
  email_contact?: string | null;
  telephone_contact?: string | null;
  lien_offre_original?: string | null;
  lien_candidature?: string | null;
  date_expiration?: DateString | null;
  salaire_min?: number | null;
  salaire_max?: number | null;
  devise_id?: UUID | null;
  organisation_id?: UUID | null;
}

export interface FormationCreate {
  titre: string;
  nom_structure: string;
  description: string;
  type_formation: TypeFormation;
  adresse?: string | null;
  ville?: string | null;
  pays?: string | null;
  email_contact?: string | null;
  telephone_contact?: string | null;
  lien_formation?: string | null;
  lien_inscription?: string | null;
  date_debut?: DateString | null;
  date_fin?: DateString | null;
  est_payante: boolean;
  prix?: number | null;
  devise_id?: UUID | null;
  duree_heures?: number | null;
  organisation_id?: UUID | null;
}

// --- Types Utilitaires ---

/** Interface polyvalente pour les composants de liste génériques */
export type OpportuniteAny = StageOut | EmploiOut | FormationOut;

export interface OpportuniteValidation {
  approved: boolean;
  commentaire: string | null;
}

export interface OpportuniteStatusUpdate {
  statut: StatutOpportunite;
}


export interface StageResponse {
  items: StageOut[];
  meta: {
    total_items: number;
    total_pages: number;
    page: number;
    page_size: number;
  };
}

export interface EmploiResponse {
  items: EmploiOut[];
  meta: {
    total_items: number;
    total_pages: number;
    page: number;
    page_size: number;
  };
}

export interface FormationResponse {
  items: FormationOut[];
  meta: {
    total_items: number;
    total_pages: number;
    page: number;
    page_size: number;
  };
}