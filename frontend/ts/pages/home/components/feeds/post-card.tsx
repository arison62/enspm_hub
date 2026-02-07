"use client";

import {
  Heart,
  MessageCircle,
  Send,
  MoreHorizontal,
  ThumbsUp,
  Flag,
  EyeOff,
  Link,
  Trash,
} from "lucide-react";
import { Link as LinkInertia } from "@inertiajs/react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { getAvatarFallback } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { useSessionStorage } from "@uidotdev/usehooks";
import { Dialog, DialogTitle, DialogContent } from "@/components/ui/dialog";

import PostReportForm from "./post-report-form";
import RichTextExpandable from "./rich-text-expandable";

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * LinkedInPostProps
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Props for the LinkedInPost component, which displays a LinkedIn-style
 * post with professional author info and engagement metrics.
 */
export interface LinkedInPostProps {
  data?: {
    /** Unique identifier for the post. */
    id: string;
    /** Author's display name. */
    author?: string;
    /** Author's professional headline or title. */
    headline?: string;
    /** Avatar letter fallback or image URL for the profile picture. */
    avatar?: string;
    /** Post text content (supports line breaks and hashtags). */
    content: string;
    /** Formatted like count (e.g., "1,234"). */
    likes?: string;
    /** Number of comments on the post. */
    comments: string;
    /** Time since posted (e.g., "2h"). */
    time: string;
    /** Numbers of views */
    views?: string;
    urlProfile: string;
    hasLiked?: boolean;
  };
  isLiked?: boolean;
  canDelete?: boolean;
  onView?: () => void;
  onLike?: () => void;
  onHidden?: () => void;
  onComment?: () => void;
  onDelete?: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onReport: (data: any) => void;
}

/**
 * A LinkedIn post embed component with professional styling.
 * Displays author info, content, and engagement metrics.
 *
 * Features:
 * - Author avatar with headline
 * - Multi-line content with hashtag support
 * - Reaction indicators (like, love)
 * - Engagement counts (likes, comments, reposts)
 * - Action buttons (like, comment, repost, send)
 * - Dropdown menu (save, copy link, hide, unfollow, report)
 *
 * @component
 * @example
 * ```tsx
 * <LinkedInPost
 *   data={{
 *     author: "Manifest",
 *     headline: "Building the future of AI",
 *     avatar: "M",
 *     content: "Excited to share our latest update!",
 *     likes: "1,234",
 *     comments: "89",
 *     reposts: "45",
 *     time: "2h"
 *   }}
 * />
 * ```
 */
export function LinkedInPost({
  data,
  canDelete,
  isLiked,
  onView,
  onHidden,
  onReport,
  onDelete,
  onLike,
}: LinkedInPostProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isDialogOpen, setDialogOpen] = useState(false);
  const isInView = useInView(ref, {
    once: true,
    initial: false,
    amount: 0.2,
  });
  const [isViewed, setIsViewed] = useSessionStorage(
    `viewed-${data?.id}`,
    false,
  );
  const {
    author,
    headline,
    avatar,
    content,
    likes,
    comments,
    time,
    urlProfile,
    views,
  } = data || {};
  useEffect(() => {
    if (isInView && !isViewed) {
      onView?.();
      setIsViewed(true);
      console.log("Incremented");
    }
  }, [isInView, isViewed, onView, setIsViewed]);
  if (isDialogOpen) {
    return (
      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[425px] mx-auto">
          <DialogTitle className="sr-only">Signaler</DialogTitle>

          <PostReportForm
            onSubmit={onReport}
            onCancel={() => {
              setDialogOpen(false);
            }}
          />
        </DialogContent>
      </Dialog>
    );
  }
  return (
    <div className="rounded-xl border bg-card" ref={ref}>
      <div className="p-4">
        <div className="flex gap-3">
          <LinkInertia href={urlProfile}>
            <Avatar>
              <AvatarImage src={avatar} className="object-cover" />
              <AvatarFallback className="bg-primary text-white">
                {getAvatarFallback(author)}
              </AvatarFallback>
            </Avatar>
          </LinkInertia>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-sm">{author}</p>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {headline}
                </p>
                <p className="text-xs text-muted-foreground">{time} · </p>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                    <MoreHorizontal className="h-5 w-5" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>
                    <Link className="mr-2 h-4 w-4" />
                    Copy link
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={onHidden}>
                    <EyeOff className="mr-2 h-4 w-4" />
                    Cacher
                  </DropdownMenuItem>
                  {canDelete && (
                    <DropdownMenuItem onClick={onDelete}>
                      <Trash className="mr-2 h-4 w-4" />
                      Supprimer
                    </DropdownMenuItem>
                  )}

                  <DropdownMenuItem
                    onClick={() => {
                      setDialogOpen(!isDialogOpen);
                    }}
                  >
                    <Flag className="mr-2 h-4 w-4" />
                    Signaler
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
        <RichTextExpandable content={content!} />
      </div>

      <div className="px-4 py-2 border-t flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="flex -space-x-1">
            <div className="h-4 w-4 rounded-full bg-blue-500 flex items-center justify-center">
              <ThumbsUp className="h-2.5 w-2.5 text-white" />
            </div>
            <div className="h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
              <Heart className="h-2.5 w-2.5 text-white fill-white" />
            </div>
          </div>
          <span>{likes}</span>
        </div>
        <span>
          {comments} commentaires • {views} vues
        </span>
      </div>
      <div className="px-2 py-1 border-t flex items-center justify-around">
        <button
          onClick={onLike}
          className="flex items-center gap-2 px-4 py-2 hover:bg-muted rounded-md transition-colors text-sm text-muted-foreground cursor-pointer"
        >
          <ThumbsUp
            className={`h-5 w-5 ${isLiked ? "text-primary fill-primary" : ""}`}
          />
          <span>Like</span>
        </button>
        <button className="flex items-center gap-2 px-4 py-2 hover:bg-muted rounded-md transition-colors text-sm text-muted-foreground cursor-pointer">
          <MessageCircle className="h-5 w-5" />
          <span>Comment</span>
        </button>
        <button className="flex items-center gap-2 px-4 py-2 hover:bg-muted rounded-md transition-colors text-sm text-muted-foreground cursor-pointer">
          <Send className="h-5 w-5" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
}

export function LinkedInPostSkeleton() {
  return (
    <div className="rounded-xl border bg-card">
      <div className="p-4">
        <div className="flex gap-3">
          <Skeleton className="h-12 w-12 rounded-full shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
                <Skeleton className="h-3 w-16" />
              </div>
              <Skeleton className="h-5 w-5" />
            </div>
          </div>
        </div>
        <div className="space-y-2 mt-3">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      </div>
      <div className="px-4 py-2 border-t flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="flex -space-x-1">
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-4 rounded-full" />
          </div>
          <Skeleton className="h-3 w-12" />
        </div>
        <Skeleton className="h-3 w-32" />
      </div>
      <div className="px-2 py-1 border-t flex items-center justify-around">
        <Skeleton className="h-9 w-20 rounded-md" />
        <Skeleton className="h-9 w-24 rounded-md" />
        <Skeleton className="h-9 w-20 rounded-md" />
        <Skeleton className="h-9 w-20 rounded-md" />
      </div>
    </div>
  );
}
