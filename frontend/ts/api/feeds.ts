/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  useMutation,
  useQuery,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";
import type { Post, UserStats } from "@/types/feeds";
import { toast } from "sonner";

export type Pagination = {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
};

export const useGetPosts = (pageSize: number = 4) => {
  return useInfiniteQuery({
    queryKey: ["posts"],
    queryFn: async ({ pageParam = 1 }) => {
      const res = await axios.get("/posts/", {
        params: {
          page: pageParam,
          page_size: pageSize,
        },
      });
      return res.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
      const totalLoaded = allPages.length * pageSize;
      return totalLoaded < lastPage.total_items
        ? allPages.length + 1
        : undefined;
    },
  });
};


export const useGetProfilStats = (id: string) => {
  const { data, isLoading, isPending, error, refetch } = useQuery<
    UserStats,
    AxiosError
  >({
    queryKey: ["profil-stats", id],
    queryFn: async () => {
      const res = await axios.get(`/posts/profil/${id}/stats`);
      return res.data;
    },
  });

  return { data, isLoading, isPending, error, refetch };
};

export const usePostAction = () => {
  const queryClient = useQueryClient();

  const createPost = useMutation({
    mutationFn: (content: string) => createPostFn(content),
    onSuccess: () => {
      // Invalide le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (error: any) => {
      throw error;
    },
  });

  const deletePostMutation = useMutation({
    mutationFn: (postId: string) => axios.delete(`/posts/${postId}/`),

    // Étape 1 : Avant l'appel API
    onMutate: async (postId) => {
      // Annuler toute requête sortante pour ne pas écraser notre mise à jour optimiste
      await queryClient.cancelQueries({ queryKey: ["posts"] });

      // Sauvegarder l'état actuel du cache (pour le rollback)
      const previousPosts = queryClient.getQueryData(["posts"]);

      // Mettre à jour le cache de manière optimiste
      queryClient.setQueryData(["posts"], (old: any) => {
        // Si vous utilisez useInfiniteQuery, structurez selon old.pages
        if (!old) return old;
        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            posts: page.posts.filter((p: any) => p.id !== postId),
          })),
        };
      });

      // Retourner le contexte avec l'ancienne valeur
      return { previousPosts };
    },

    // Étape 2 : Si l'API échoue
    onError: (_err, _postId, context) => {
      // On restaure les données précédentes
      if (context?.previousPosts) {
        queryClient.setQueryData(["posts"], context.previousPosts);
      }
      toast.error("Erreur lors de la suppression..");
    },

    // Étape 3 : Une fois terminé (succès ou erreur)
    onSettled: () => {
      // On force une synchronisation avec le serveur pour être sûr
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
  });

  const toggleLikePostMutation = useMutation({
    onMutate: async (postId) => {
      await queryClient.cancelQueries({ queryKey: ["posts"] });
      const previousPosts = queryClient.getQueryData(["posts"]);

      queryClient.setQueryData(["posts"], (old: any) => {
        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            posts: page.posts.map((p: any) =>
              p.id === postId
                ? {
                    ...p,
                    user_has_liked: !p.user_has_liked,
                    likes_count: p.user_has_liked
                      ? p.likes_count - 1
                      : p.likes_count + 1,
                  }
                : p,
            ),
          })),
        };
      });

      return { previousPosts };
    },
  });

  const recordPostViewMutation = useMutation({
    onMutate: async (postId) => {
      await queryClient.cancelQueries({ queryKey: ["posts"] });
      const previousPosts = queryClient.getQueryData(["posts"]);

      queryClient.setQueryData(["posts"], (old: any) => {
        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            posts: page.posts.map((p: any) =>
              p.id === postId ? { ...p, views_count: p.views_count + 1 } : p,
            ),
          })),
        };
      });

      return { previousPosts };
    }
  });



  return {
    createPost,
    deletePost: deletePostMutation,
    recordPostView: recordPostViewMutation,
    toggleLikePost: toggleLikePostMutation,
  };
};

const createPostFn = async (content: string) => {
  const res = await axios.post("/posts/", { content });
  return res.data as Post;
};
