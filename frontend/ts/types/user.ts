import type {
  UUID,
  DateTimeString,
  ReseauSocialOut,
  DomaineOut,
  TitreHonorifiqueOut,
  AnneePromotionOut,
} from "./base";

export type Profil = {
  id: string;
  nom_complet: string;
  matricule: string | null;
  titre: string | null;
  slug: string | null;
  statut_global: string | null;
  annee_sortie: number | null;
  telephone: string | null;
  domaine: string | null;
  bio: string | null;
  photo_profil: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  email: string;
  role_systeme: string;
  est_actif: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
  profil: Profil;
};

export type RoleSysteme = "user" | "admin_site" | "super_admin";

export type StatutGlobal =
  | "etudiant"
  | "alumni"
  | "enseignant"
  | "personnel_admin"
  | "partenaire";

// ============================================================================
// UTILISATEURS
// ============================================================================

export interface UserOut {
  id: UUID;
  email: string;
  role_systeme: string;
  est_actif: boolean;
  last_login: DateTimeString | null;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}


export interface ProfilOut {
  id: UUID;
  nom_complet: string;
  matricule: string | null;
  titre: TitreHonorifiqueOut | null;
  statut_global: StatutGlobal;
  annee_sortie: AnneePromotionOut | null;
  telephone: string | null;
  domaine: DomaineOut | null;
  bio: string | null;
  adresse: string | null;
  pays_nom: string | null;
  pays: string | null;
  ville: string | null;
  photo_profil: string | null;
  est_en_poste: boolean;
  slug: string;
}

export interface ProfilCreate {
  nom_complet: string;
  matricule: string | null;
  titre: string | null;
  statut_global: string;
  annee_sortie: number | null;
  telephone: string | null;
  domaine: string | null;
  bio: string | null;
  adresse: string | null;
}


export interface UserCreateAdmin {
  email: string;
  telephone: string | null;
  role_systeme: string;
  profil: ProfilCreate;
}


export interface PhotoUploadResponse {
  message: string;
  photo_profil: string | null;
}

export interface PhotoDeleteResponse {
  message: string;
}

export interface ChangePassword {
  old_password: string;
  new_password: string;
}

export interface ResetPassword {
  new_password: string | null;
}



export interface ExperienceProfessionnelleOut {
  id: UUID;
  nom_entreprise: string;
  duree_texte: string | null;
  titre_poste: string;
  lieu: string | null;
  date_debut: DateTimeString;
  date_fin: DateTimeString | null;
  est_poste_actuel: boolean;
  description: string | null;
} 

export interface ExperienceProfessionnelleCreateOrUpdate {
  id?: UUID;
  nom_entreprise: string;
  lieu: string | null;
  titre_poste: string;
  date_debut: DateTimeString;
  date_fin: DateTimeString | null;
  est_poste_actuel: boolean;
  description: string | null;
}

export interface ProfilComplete {
  id: UUID;
  nom_complet: string;
  matricule: string | null;
  titre: TitreHonorifiqueOut | null;
  statut_global: StatutGlobal;
  annee_sortie: AnneePromotionOut | null;
  telephone: string | null;
  domaine: DomaineOut | null;
  bio: string | null;
  adresse: string | null;
  pays_nom: string | null;
  pays: string | null;
  ville: string | null;
  photo_profil: string | null;
  est_en_poste: boolean;
  poste_actuel: ExperienceProfessionnelleOut | null;
  slug: string;
  created_at: DateTimeString;
  updated_at: DateTimeString;
  liens_reseaux: LienReseauSocialOut[];
  experiences: ExperienceProfessionnelleOut[];
}


export interface LienReseauSocialOut {
  reseau: ReseauSocialOut;
  id: UUID | null;
  url: string;
}

export interface UserComplete {
  id: UUID;
  email: string;
  role_systeme: string;
  est_actif: boolean;
  last_login: DateTimeString | null;
  created_at: DateTimeString;
  updated_at: DateTimeString;
  profil: ProfilComplete;
}

export interface UserResponse {
  items: UserComplete[];
  meta: {
    total_items: number;
    total_pages: number;
    page: number;
    page_size: number;
  };
}
