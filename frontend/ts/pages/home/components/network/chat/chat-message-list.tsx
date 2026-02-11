import type { ChatMessage } from "@/types/network";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { InfiniteScroll } from "./message-infinite-list";
import { InfiniteScrollCell } from "./message-infinite-list";

interface ChatMessageListProps {
  messages: ChatMessage[];
  onLoadMore: () => void;
  isPending?: boolean;
  hasMore?: boolean;
  allItemsCount?: number;
  isFirstLoad?: boolean;
  currentChatId?: string;
}

export function ChatMessageList({
  messages,
  onLoadMore,
  isPending = false,
  allItemsCount,
  currentChatId,
}: ChatMessageListProps) {
  return (
    <InfiniteScroll
      key={currentChatId}
      reverse={true}
      isPending={isPending}
      currentItemsLength={messages.length}
      allItemsCount={allItemsCount}
      loadMore={onLoadMore}
      className="gap-4 p-4"
    >
      {/* 
         Affichage des Skeletons uniquement en haut quand on charge l'historique 
         On les place à l'intérieur du InfiniteScroll pour qu'ils poussent le contenu
      */}
      {isPending && true && (
        <div className="space-y-4 mb-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-3/4 rounded-2xl opacity-50" />
          ))}
        </div>
      )}

      {messages.map((message) => (
        <InfiniteScrollCell key={message.id} className="mb-4">
          <div
            className={cn(
              "flex gap-3",
              message.isOwn ? "justify-end" : "justify-start",
            )}
          >
            <div
              className={cn(
                "flex gap-3 max-w-[80%]",
                message.isOwn ? "flex-row-reverse" : "flex-row",
              )}
            >
              <Avatar className="h-8 w-8 self-end">
                <AvatarImage src={message.avatarUrl} />
                <AvatarFallback className="text-[10px]">
                  {message.avatarFallback}
                </AvatarFallback>
              </Avatar>

              <div
                className={cn(
                  "flex flex-col",
                  message.isOwn ? "items-end" : "items-start",
                )}
              >
                {message.author && !message.isOwn && (
                  <span className="text-[10px] font-medium mb-1 ml-1 text-muted-foreground">
                    {message.author}
                  </span>
                )}

                <div
                  className={cn(
                    "rounded-2xl px-4 py-2 shadow-sm",
                    message.isOwn
                      ? "bg-primary text-primary-foreground rounded-br-none"
                      : "bg-muted rounded-bl-none",
                  )}
                >
                  {message.type === "image" ? (
                    <img
                      src={message.images?.[0]}
                      alt=""
                      className="rounded-lg max-w-full"
                    />
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-1 mt-1 px-1">
                  <span className="text-[9px] opacity-60">
                    {new Date(message.time).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  {message.isOwn && (
                    <span className="text-[9px] opacity-60">
                      · {message.status}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </InfiniteScrollCell>
      ))}
    </InfiniteScroll>
  );
}
