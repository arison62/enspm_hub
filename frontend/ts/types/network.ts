/**
 * TypeScript types for Chat API
 * Matches Django Ninja schemas
 */

import type { ProfilOut } from "./user";

// ============================================
// BASE TYPES
// ============================================

export interface PaginationMeta {
  total_items: number;
  total_pages: number;
  page: number;
  page_size: number;
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
  createur?: ProfilOut;
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
  demandeur: ProfilOut;
  groupe_id: string;
  traite_par?: ProfilOut;
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
  profil: ProfilOut;
  groupe: GroupOut;
}

export interface MembreGroupeCreate {
  groupe_id: string;
  profil_id: string;
  role?: "membre" | "admin";
}

export interface MembreGroupeUpdate {
  role: "membre" | "admin";
}

export interface MembreGroupeListResponse {
  items: MembreGroupeOut[];
  meta: PaginationMeta;
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
  expediteur: ProfilOut;
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
// MESSAGE DM TYPES
// ============================================

export interface MessageDMOut {
  id: string;
  contenu: string;
  est_lu: boolean;
  created_at: string;
  updated_at: string;
  expediteur: ProfilOut;
  piece_jointe_url?: string;
}

export interface MessageDMCreate {
  contenu: string;
  piece_jointe_base64?: string;
}

export interface MessageDMListResponse {
  items: MessageDMOut[];
  meta: PaginationMeta;
}

// ============================================
// CONVERSATION TYPES
// ============================================

export interface ConversationOut {
  id: string;
  created_at: string;
  updated_at: string;
  participants: ProfilOut[];
}

export interface ConversationRecentOut {
  conversation_id: string;
  contact: ProfilOut;
  dernier_message?: MessageDMOut;
  messages_non_lus: number;
  updated_at: string;
}

export interface ConversationListResponse {
  items: ConversationRecentOut[];
  meta: PaginationMeta;
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

// ============================================
// Gestion des chats
// ============================================

export type MessageStatus = "sent" | "delivered" | "read";
export type MessageType = "text" | "image" | "file";

export interface ChatMessage {
  id: string;
  senderId: string;
  isOwn: boolean;
  content?: string;
  type?: MessageType;
  images?: string[];
  time: string;
  status?: MessageStatus;
  author?: string;
  avatarUrl?: string;
  avatarFallback?: string;
}

export interface ChatConversation {
  id: string;
  type: "dm" | "group";
  name: string;
  avatar?: string | null;
  initials?: string;
  lastMessage: string;
  time: string;
  unread: number;
  online: boolean;
}