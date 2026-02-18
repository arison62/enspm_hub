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
// CHAT TYPES (UNIFIED)
// ============================================

export interface ProfilMinimal {
  id: string;
  nom_complet: string;
  photo_url?: string;
  is_online: boolean;
}

export interface Media {
  url: string;
  type: string; // MIME type
  nom: string;
  taille: number;
}

export interface Message {
  id: string;
  client_id?: string; // Généré par frontend pour optimistic UI
  type: "user" | "system";
  conversation_id: string;
  expediteur?: ProfilMinimal; // Undefined pour messages système
  contenu: string;
  media_url?: string;
  media_info?: Media;
  reponse_a?: Message;
  nombre_reponses: number;
  est_lu_par_moi: boolean;
  created_at: string;
  updated_at: string;
  edited_at?: string;
}

export interface Conversation {
  id: string;
  type: "dm" | "group";
  groupe?: {
    id: string;
    nom: string;
    slug: string;
    image_url?: string;
  };
  contact?: {
    id: string;
    nom_complet: string;
    photo_profil: string;
  };
  dernier_message?: Message;
  messages_non_lus: number;
  role?: string;
  created_at: string;
  updated_at: string;
}

export interface MessageCreateIn {
  contenu: string;
  client_id?: string;
  media_base64?: string;
  reponse_a_id?: string;
}

export interface MessageListResponse {
  items: Message[];
  meta: PaginationMeta;
}

export interface ConversationListResponse {
  items: Conversation[];
  meta: PaginationMeta;
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
  is_member: boolean;
  is_admin: boolean;
  pending_request: number;
  has_user_pending_request: boolean;
  est_actif: boolean;
  conversation_id?: string;
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
  est_ferme?: boolean;
}

export interface GroupListResponse {
  items: GroupOut[];
  meta: PaginationMeta;
}

export interface MembreGroupeOut {
  id: string;
  profil: ProfilOut;
  role: "membre" | "admin";
  date_membre: string;
  created_at: string;
  est_admin: boolean;
}

export interface MembreGroupeCreate {
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

export interface MembreGroupeRequest {
  id: string;
  message?: string;
  demandeur: ProfilOut;
  status: string;
  created_at: string;
}

export interface DemandeAccesListResponse {
  items: MembreGroupeRequest[];
  meta: PaginationMeta;
}

// ============================================
// WEB SOCKET EVENTS
// ============================================

export interface WebSocketEvent<T = any> {
  type: string;
  payload: T;
  timestamp: string;
}

// ============================================
// UI Type
// ============================================
export type ChatMessageUI = {
  id: string;
  clientId: string;
  conversationId: string;
  isOwn: boolean;
  author: string;
  time: string;
  avatar?: string;
  content?: string;
  type: "user" | "system";
  media?: string;
  mediaType?: string;
  mediaSize?: string;
  status?: string;
  canDelete?: boolean; 
};

export type ChatConversationUI = {
  id: string;
  type: "group" | "dm";
  name: string;
  avatar?: string;
  lastMessage: string;
  unread: number;
  time: string;
  online: false;
  role: "admin" | "membre";
};
