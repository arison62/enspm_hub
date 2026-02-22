// ============================================================================
// TYPES DE BASE
// ============================================================================

export type UUID = string;
export type DateString = string; // Format ISO 8601
export type DateTimeString = string; // Format ISO 8601

// ============================================================================
// RÉFÉRENCES
// ============================================================================

export interface AnneePromotionOut {
  id: UUID;
  annee: number;
  libelle: string;
  description: string | null;
  est_active: boolean;
  ordre_affichage: number;
}

export interface DeviseSimple {
  id: UUID;
  code: string;
  nom: string;
  symbole: string;}

export interface DomaineOut {
  id: UUID;
  nom: string;
  code: string;
  description: string | null;
  categorie: string;
  est_actif: boolean;
  ordre_affichage: number;
}

export interface FiliereOut {
  id: UUID;
  domaine: UUID;
  nom: string;
  code: string;
  description: string | null;
  niveau: string;
  duree_annees: number | null;
  est_active: boolean;
  ordre_affichage: number;
}

export interface DomaineComplete {
  id: UUID;
  nom: string;
  code: string;
  description: string | null;
  categorie: string;
  est_actif: boolean;
  ordre_affichage: number;
  created_at: DateTimeString;
  updated_at: DateTimeString;
  filieres: FiliereOut[];
}

export interface SecteurActiviteOut {
  id: UUID;
  nom: string;
  code: string;
  description: string | null;
  est_actif: boolean;
  ordre_affichage: number;
}

export interface PosteOut {
  id: UUID;
  nom: string;
  description: string | null;
}

export interface DeviseOut {
  code: string;
  nom: string;
  symbole: string;
}

export interface ReseauSocialOut {
  id: UUID | null;
  nom: string;
  code: string;
  url_base: string;
  type_reseau: string;
  pattern_validation?: string | null;
  placeholder_exemple?: string | null;
  est_actif: boolean;
  ordre_affichage: number;
}


export interface TitreHonorifiqueOut {
  id: UUID;
  titre: string;
  nom_complet: string;
}

// Reference groupe
export interface ReferencesAcademiquesOut {
  annees_promotion: AnneePromotionOut[];
  domaines: DomaineOut[];
  titres: TitreHonorifiqueOut[];
}

export interface ReferencesProfessionnellesOut {
  secteurs: SecteurActiviteOut[];
  postes: PosteOut[];
}

export interface ReferencesFinancieresOut {
  devises: DeviseOut[];
}

export interface ReferencesReseauxOut {
  reseaux: ReseauSocialOut[];
}

export interface PaysOut {
  code: string;
  name: string;
}

export interface AllReferencesOut {
  annees_promotion: AnneePromotionOut[];
  domaines: DomaineOut[];
  filieres: FiliereOut[];
  secteurs: SecteurActiviteOut[];
  postes: PosteOut[];
  devises: DeviseOut[];
  titres: TitreHonorifiqueOut[];
  reseaux: ReseauSocialOut[];
  pays: PaysOut[];
}

export type ReferencePreviewOut = {
  id: string;
  type: string;
  titre?: string;
  sous_titre?: string;
  apercu?: string;
  url?: string;
  media_url?: string;
  media_type?: string;
  media_name?: number;
  created_at?: string;
  updated_at?: string;
};

export interface PaginationMetaSchema {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}