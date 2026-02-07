/**
 * TypeScript types for Chat API
 * Matches Django Ninja schemas
 */

// ============================================
// BASE TYPES
// ============================================

export interface PaginationMeta {
  total_items: number;
  total_pages: number;
  page: number;
  page_size: number;
}

export interface ProfilBaseOut {
  id: string;
  user_id: string;
  nom_complet: string;
  avatar_url?: string;
  slug: string;
  
}

// ============================================
// GROUPE TYPES
// ============================================

export interface GroupOut {
  id: string;
  nom: string;
  slug: string;
  description: string;
  type_acces: "public" | "prive";
  status: "actif" | "inactif";
  est_ferme: boolean;
  created_at: string;
  updated_at: string;
  createur?: ProfilBaseOut;
  nombre_membres: number;
  image_url?: string;
  is_member?: boolean;
  is_admin?: boolean;
  pending_request?: number;
  has_user_pending_request?: boolean;
  est_actif?: boolean;
}

export interface GroupCreate {
  nom: string;
  description?: string;
  type_acces?: "public" | "prive";
  image_base64?: string;
}

export interface GroupUpdate {
  nom?: string;
  description?: string;
  type_acces?: "public" | "prive";
  status?: "actif" | "inactif";
  image_base64?: string;
}

export interface GroupFilter {
  query?: string;
  type_acces?: "public" | "prive";
}

export interface GroupListResponse {
  items: GroupOut[];
  meta: PaginationMeta;
}

// ============================================
// DEMANDE D'ACCÈS TYPES
// ============================================

export interface DemandeAccesGroupeOut {
  id: string;
  message: string;
  status: "en_attente" | "approuve" | "refuse";
  status_display: string;
  date_traitement?: string;
  created_at: string;
  updated_at: string;
  demandeur: ProfilBaseOut;
  groupe_id: string;
  traite_par?: ProfilBaseOut;
}

export interface DemandeAccesGroupeCreate {
  message?: string;
}

export interface DemandeAccesListResponse {
  items: DemandeAccesGroupeOut[];
  meta: PaginationMeta;
}

// ============================================
// MEMBRE GROUPE TYPES
// ============================================

export interface MembreGroupeOut {
  id: string;
  role: "membre" | "admin";
  date_membre: string;
  created_at: string;
  updated_at: string;
  profil: ProfilBaseOut;
  groupe: GroupOut;
  est_admin: boolean;
}

export interface MembreGroupeCreate {
  groupe_id: string;
  profil_id: string;
  role?: "membre" | "admin";
}

export interface MembreGroupeUpdate {
  role: "membre" | "admin";
}

// ============================================
// MESSAGE GROUPE TYPES
// ============================================

export interface MessageGroupeOut {
  id: string;
  contenu: string;
  est_lu: boolean;
  created_at: string;
  updated_at: string;
  expediteur: ProfilBaseOut;
  groupe: GroupOut;
  reponse_a?: MessageGroupeOut;
  piece_jointe_url?: string;
  nombre_reponses: number;
}

export interface MessageGroupeCreate {
  contenu: string;
  reponse_a_id?: string;
  piece_jointe_base64?: string;
}

export interface MessageGroupeUpdate {
  contenu?: string;
  est_lu?: boolean;
}

export interface MessageListResponse {
  items: MessageGroupeOut[];
  meta: PaginationMeta;
}

// ============================================
// MESSAGE DIRECT TYPES
// ============================================

export interface MessageDirectOut {
  id: string;
  contenu: string;
  est_lu: boolean;
  created_at: string;
  updated_at: string;
  expediteur: ProfilBaseOut;
  destinataire: ProfilBaseOut;
  piece_jointe_url?: string;
}

export interface MessageDirectCreate {
  destinataire_id: string;
  contenu: string;
  piece_jointe_base64?: string;
}

export interface MessageDirectUpdate {
  contenu?: string;
  est_lu?: boolean;
}

// ============================================
// CONVERSATION TYPES
// ============================================

export interface ConversationOut {
  contact: ProfilBaseOut;
  dernier_message?: MessageDirectOut;
  messages_non_lus: number;
}

// ============================================
// STATISTIQUES TYPES
// ============================================

export interface MessagesDirectsStatsOut {
  envoyes: number;
  recus: number;
  non_lus: number;
}

export interface GroupesStatsOut {
  total: number;
  admin: number;
  membre: number;
}

export interface StatsMessagesOut {
  messages_directs: MessagesDirectsStatsOut;
  groupes: GroupesStatsOut;
}

// ============================================
// ERROR TYPES
// ============================================

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  status?: number;
}

// ============================================
// UTILITY TYPES
// ============================================

export type GroupTypeAcces = "public" | "prive";
export type GroupStatus = "actif" | "inactif";
export type MemberRole = "membre" | "admin";
export type DemandeStatus = "en_attente" | "approuve" | "refuse";
