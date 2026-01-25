/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import axios from "@/lib/axios";
import type { Post, PostsResponse, UserStats } from "@/types/feeds";

export type Pagination = {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
};

export const useGetPosts = ({ pagination }: { pagination: Pagination }) => {
  const { data, isLoading, isPending, isFetching, error, refetch } = useQuery<
    PostsResponse,
    AxiosError
  >({
    queryKey: ["posts", JSON.stringify({ pagination })],
    queryFn: async () => {
      const params = {
        page: pagination.pageIndex,
        page_size: pagination.pageSize,
      };
      const res = await axios.get("/posts/", {
        params: params,
      });
      return res.data;
    },
  });

  return { data, isLoading, isPending, isFetching, error, refetch };
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

  const deletePost = useMutation({
    mutationFn: (id: string) => deletePostFn(id),
    onSuccess: () => {
      // Invalide le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (error: any) => {
      throw error;
    },
  });

  const recordPostView = useMutation({
    mutationFn: (id: string) => recordPostViewFn(id),

    onError: (error: any) => {
      throw error;
    },
  });

  const toggleLikePost = useMutation({
    mutationFn: (id: string) => toggleLikePostFn(id),
    onError: (error: any) => {
      throw error;
    },
  });

  return {
    createPost,
    deletePost,
    recordPostView,
    toggleLikePost,
  };
};

const createPostFn = async (content: string) => {
  const res = await axios.post("/posts/", { content });
  return res.data as Post;
};

const deletePostFn = async (id: string) => {
  await axios.delete(`/posts/${id}`);
};

const recordPostViewFn = async (id: string) => {
  await axios.post(`/posts/${id}/views`);
};

const toggleLikePostFn = async (id: string) => {
  await axios.post(`/posts/${id}/like`);
};
