import type { ChatMessageUI } from "@/types/network";
import { Skeleton } from "@/components/ui/skeleton";
import { InfiniteScroll, InfiniteScrollCell } from "./message-infinite-list";
import { ChatMessage } from "./chat-message";

interface ChatMessageListProps {
  messages: ChatMessageUI[];
  onLoadMore: () => void;
  onDeleteMessage?: (messageId: string, conversationId: string) => void;
  onSelectMessageChange?: (message: ChatMessageUI | null) => void;
  isPending?: boolean;
  hasMore?: boolean;
  allItemsCount?: number;
  isFirstLoad?: boolean;
  currentChatId?: string;
}

export function ChatMessageList({
  messages,
  onLoadMore,
  onDeleteMessage,
  onSelectMessageChange,
  isPending,
  allItemsCount,
  currentChatId,
}: ChatMessageListProps) {
  return (
    <InfiniteScroll
      key={currentChatId}
      reverse={true}
      isPending={isPending || false}
      currentItemsLength={messages.length}
      allItemsCount={allItemsCount}
      loadMore={onLoadMore}
      className="gap-4 p-4"
    >
      {isPending && (
        <div className="space-y-4 mb-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-3/4 rounded-2xl opacity-50" />
          ))}
        </div>
      )}

      {messages.map((message) => (
        <InfiniteScrollCell key={message.clientId} className="mb-4">
          <ChatMessage
            message={message}
            onDeleteMessage={onDeleteMessage}
            onSelectMessageChange={onSelectMessageChange}
          />
        </InfiniteScrollCell>
      ))}
    </InfiniteScroll>
  );
}
