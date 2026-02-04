import type { ProfilOut } from "./user";

export interface Groupe {
  id: string;
  nom: string;
  description: string;
  image_url?: string;

  type_acces: string;
  createur: ProfilOut;

  is_member: boolean;
  is_admin: boolean;
  est_actif: boolean;

  nombre_membres: number;

  created_at: string;
  updated_at: string;
}

export interface GroupListResponse{
    items: Groupe[];
    meta: {
        total_items: number;
        total_pages: number;
        page: number;
        page_size: number;
    };
}