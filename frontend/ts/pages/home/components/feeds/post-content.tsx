import { type Pagination, useGetPosts, usePostAction } from "@/api/feeds";
import { useEffect, useState } from "react";
import { InfiniteScroll, InfiniteScrollCell } from "./posts-infinity-list";
import { LinkedInPost, LinkedInPostSkeleton } from "./post-card";
import type { Post } from "@/types/feeds";
import { useSessionStorage } from "@uidotdev/usehooks";
import { useAuthStore } from "@/stores/authStore";

export function PostContent({
  posts,
  setPost,
  pagination,
  setPagination,
}: {
  posts: Post[];
  setPost: React.Dispatch<React.SetStateAction<Post[]>>;
  pagination: Pagination;
  setPagination: React.Dispatch<React.SetStateAction<Pagination>>;
}) {
  const authState = useAuthStore((state) => state);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const { data, isPending } = useGetPosts({
    pagination: pagination,
  });
  const [, setHiddenPost] = useSessionStorage<string[]>("hiddenPosts", []);
  const {
    recordPostView: { mutate: recordPostView },
    deletePost: { mutate: deletePost },
    toggleLikePost: { mutate: toggleLikePost },
  } = usePostAction();

  const fetchPost = () => {
    setPagination((prev) => ({
      ...prev,
      pageIndex: prev.pageIndex + 1,
    }));
  };
  useEffect(() => {
    if (data) {
      // Suppression des doublons
      const newPosts = data.posts.filter(
        (post) => !posts.find((p) => p.id === post.id),
      );
      setPost((prev) => [...prev, ...newPosts]);
    }
  }, [data]);

  useEffect(() => {
    if (data?.total_items) {
      setTotalCount(data.total_items);
    }
  }, [data?.total_items]);

  const handleLike = (id: string) => {
    toggleLikePost(id);
    setPost((prev) => {
      return prev.map((p) => {
        if (p.id === id) {
          return {
            ...p,
            user_has_liked: !p.user_has_liked,
            likes_count: p.user_has_liked
              ? p.likes_count - 1
              : p.likes_count + 1,
          };
        }
        return p;
      });
    });
  };
  const handleDelete = (id: string) => {
    deletePost(id);
    setPost((prev) => prev.filter((p) => p.id !== id));
  };
  const canDelete = (author_id: string) => {
    return author_id === authState.user?.profil?.id || authState.isAdmin;
  };
  console.log("Posts : ", posts)
  return (
    <InfiniteScroll
      isPending={isPending}
      currentItemsLength={posts.length || 0}
      allItemsCount={totalCount}
      loadMore={fetchPost}
      className="space-y-2 sm:space-y-4"
    >
      {posts.map((post) => (
        <InfiniteScrollCell
          key={post.id}
          amount={0.2}
          skelton={<LinkedInPostSkeleton />}
        >
          <LinkedInPost
            data={{
              id: post.id,
              author: post.author.nom_complet,
              headline: post.author.bio || undefined,
              avatar: post.author.photo_profil || undefined,
              urlProfile: `/profile/${post.author.slug}`,
              likes: post.likes_count.toString(),
              comments: post.comments_count.toString(),
              content: post.content,
              time: post.duree_text,
              views: post.views_count.toString(),
            }}
            isLiked={post.user_has_liked}
            canDelete={canDelete(post.author.id)}
            onView={() => {
              recordPostView(post.id);
            }}
            onHidden={() => {
              setHiddenPost((prev) => [...prev, post.id]);
            }}
            onLike={() => handleLike(post.id)}
            onReport={() => handleDelete(post.id)}
            onDelete={() => handleDelete(post.id)}
          />
        </InfiniteScrollCell>
      ))}
    </InfiniteScroll>
  );
}
