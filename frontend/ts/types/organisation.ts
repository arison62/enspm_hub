
import type { DateString, DateTimeString, SecteurActiviteOut, UUID } from "./base";

export type StatutOrganisation = "en_attente" | "active" | "inactive";

export type TypeOrganisation =
  | "entreprise"
  | "ong"
  | "institution_publique"
  | "startup"
  | "association";

export type RoleOrganisation = "employe" | "administrateur_page";


export interface OrganisationOut {
  id: UUID;
  nom_organisation: string;
  slug: string;
  type_organisation: TypeOrganisation;
  secteur_activite: SecteurActiviteOut | null;
  adresse: string | null;
  ville: string | null;
  pays: string | null;
  pays_nom: string | null;
  site_web: string | null;
  email_general: string | null;
  telephone_general: string | null;
  logo: string | null;
  description: string | null;
  date_creation: DateString | null;
  statut: StatutOrganisation;
  est_suivi: boolean;
  nombre_abonnes: number;
  nombre_membres: number;
}


export interface MembreOrganisationOut {
  id: UUID;
  profil: UUID;
  organisation: UUID;
  role_organisation: RoleOrganisation;
  poste: UUID | null;
  est_actif: boolean;
  date_joindre: DateString;
}


export interface AbonnementOrganisationOut {
  profil: UUID;
  organisation: UUID;
  date_abonnement: DateTimeString;
}

export interface OrganisationCreate {
  nom_organisation: string;
  type_organisation: TypeOrganisation;
  secteur_activite: UUID | null;
  adresse: string | null;
  ville: string | null;
  pays: string | null;
  email_general: string | null;
  telephone_general: string | null;
  description: string | null;
  date_creation: DateString | null;
}

export interface OrganisationUpdate {
  nom_organisation?: string | null;
  type_organisation?: TypeOrganisation | null;
  secteur_activite?: UUID | null;
  adresse?: string | null;
  ville?: string | null;
  pays?: string | null;
  email_general?: string | null;
  telephone_general?: string | null;
  description?: string | null;
  date_creation?: DateString | null;
  statut?: StatutOrganisation | null;
}

export interface MembreAdd {
  profil_id: UUID;
  role_organisation: RoleOrganisation;
  poste?: UUID | null;
}

export interface MembreUpdate {
  role_organisation?: RoleOrganisation | null;
  poste?: UUID | null;
}


