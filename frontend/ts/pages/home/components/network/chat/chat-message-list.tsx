import type { ChatMessageUI } from "@/types/network";
import { Skeleton } from "@/components/ui/skeleton";
import { InfiniteScroll } from "./message-infinite-list";
import { ChatMessage } from "./chat-message";
import type { JSX } from "react";

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

function formatMessageDate(dateString: string | Date): string {
  const date = new Date(dateString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  // Réinitialiser les heures pour comparaison
  const dateWithoutTime = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );
  const todayWithoutTime = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  );
  const yesterdayWithoutTime = new Date(
    yesterday.getFullYear(),
    yesterday.getMonth(),
    yesterday.getDate(),
  );

  if (dateWithoutTime.getTime() === todayWithoutTime.getTime()) {
    return "Aujourd'hui";
  } else if (dateWithoutTime.getTime() === yesterdayWithoutTime.getTime()) {
    return "Hier";
  }

  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: date.getFullYear() !== today.getFullYear() ? "numeric" : undefined,
  });
}

function renderMessages(
  messages: ChatMessageUI[],
  onDeleteMessage?: (messageId: string, conversationId: string) => void,
  onSelectMessageChange?: (message: ChatMessageUI | null) => void,
): JSX.Element[] {
  let lastDate: string | null = null;
  const elements: JSX.Element[] = [];

  messages.forEach((message, index) => {
    const msgDate = formatMessageDate(message.time);
    const messageKey = message.clientId || message.id || `msg-${index}`;

    // Afficher le séparateur de date si changement
    if (lastDate !== msgDate) {
      lastDate = msgDate;
      elements.push(
        <div
          key={`date-${messageKey}`}
          className="flex items-center justify-center my-4"
        >
          <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
            {msgDate}
          </span>
        </div>,
      );
    }

    elements.push(
      <ChatMessage
        key={messageKey}
        message={message}
        onDeleteMessage={onDeleteMessage}
        onSelectMessageChange={onSelectMessageChange}
      />,
    );
  });

  return elements;
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
      isPending={isPending ?? false}
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

      {renderMessages(messages, onDeleteMessage, onSelectMessageChange)}
    </InfiniteScroll>
  );
}
