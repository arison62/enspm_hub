import type { Profil } from "./user";

export type Post = {
  id: string;
  author: Profil;
  content: string;
  content_text: string;
  is_pinned: boolean;
  likes_count: number;
  comments_count: number;
  views_count: number;
  duree_text: string;
  user_has_liked: boolean;
  content_type: string;
};
export type PostsResponse = {
  posts: Post[];
  total_items: number;
  page: number;
  page_size: number;
};
export type Comment = {
  id: string;
  post_id: string;
  content: string;
  content_text: string;
  author: Profil;

  likes_count: number;
  replies_count: number;

  duree_text: string;
};

export interface UserStats {
  // Valeurs brutes (utiles pour des graphiques ou calculs locaux)
  posts_count: number;
  comments_send_count: number;
  comments_received_count: number;
  likes_received_count: number;
  shares_count: number;
  views_count: number;
  engagement_rate: number;

  // Valeurs formatées (prêtes pour l'affichage UI)
  posts_count_display: string;
  comments_send_count_display: string;
  comments_received_count_display: string;
  likes_received_count_display: string;
  shares_count_display: string;
  views_count_display: string;
  engagement_rate_display: string;
}