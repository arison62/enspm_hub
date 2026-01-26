import { useGetPosts, usePostAction } from "@/api/feeds";
import { InfiniteScroll, InfiniteScrollCell } from "./posts-infinity-list";
import { LinkedInPost, LinkedInPostSkeleton } from "./post-card";
import { useSessionStorage } from "@uidotdev/usehooks";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "sonner";

export function PostContent() {
  const authState = useAuthStore((state) => state);
  const { data, fetchNextPage, isFetchingNextPage, status } = useGetPosts(5);

  const allPosts = data?.pages.flatMap((page) => page.posts) || [];

  const [hiddenPosts, setHiddenPost] = useSessionStorage<string[]>(
    "hiddenPosts",
    [],
  );
  const visiblePosts = allPosts.filter(
    (post) => !hiddenPosts.includes(post.id),
  );
  const {
    recordPostView: { mutate: recordPostView },
    deletePost: { mutate: deletePost },
    toggleLikePost: { mutate: toggleLikePost },
  } = usePostAction();

  const handleHidePost = (postId: string) => {
    setHiddenPost((prev) => [...prev, postId]);
    toast.info("Post masqué", {
      description: "Vous ne verrez plus ce post",
      action: {
        label: "Annuler",
        onClick: () => {
          setHiddenPost((prev) => prev.filter((id) => id !== postId));
        },
      },
    });
  };
  const canDelete = (author_id: string) => {
    return author_id === authState.user?.profil?.id || authState.isAdmin;
  };

  return (
    <InfiniteScroll
      isPending={isFetchingNextPage}
      currentItemsLength={visiblePosts.length}
      allItemsCount={data?.pages[0].total_items}
      loadMore={() => !isFetchingNextPage && fetchNextPage()}
      className="space-y-2 sm:space-y-4"
    >
      {status === "pending" &&
        [0, 1, 2].map((i) => <LinkedInPostSkeleton key={i} />)}
      {visiblePosts.map((post) => (
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
              handleHidePost(post.id);
            }}
            onReport={() => {}}
            onLike={() => toggleLikePost(post.id)}
            onDelete={() => deletePost(post.id)}
          />
        </InfiniteScrollCell>
      ))}
    </InfiniteScroll>
  );
}
