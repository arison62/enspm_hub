import type { ChatConversation, ChatMessage } from "@/types/network";
import { useState, useEffect } from "react";
import { ChatSidebar } from "./components/network/chat/chat-sidebar";
import { ChatMessageList } from "./components/network/chat/chat-message-list";
import AppLayout from "@/components/layouts/app-layout";
import { Button } from "@/components/ui/button";
import { AvatarImage, AvatarFallback, Avatar } from "@/components/ui/avatar";
import { ArrowLeft, Video, Phone, MoreVertical } from "lucide-react";
import { ChatInput } from "./components/network/chat/chat-input";
import {
  mockConversations,
  getMessagesForConversation,
} from "./components/network/chat/mock";
import { useGetConversations } from "@/api/network/chat";

export default function ChatPage() {
  const { data } = useGetConversations({
    pagination: { pageSize: 10, pageIndex: 0 },
  });
  const [selectedChat, setSelectedChat] = useState<ChatConversation | null>(
    null,
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [isPending, setIsPending] = useState(false);

  // Better structure: Define load functions based on selectedChat
  const conversationId = selectedChat?.id.toString() || "";
  const {
    getInitialMessages,
    loadMore: loadMoreFn,
    hasMore: hasMoreFn,
  } = getMessagesForConversation(conversationId);

  useEffect(() => {
    if (!conversationId) return;
    setMessages(getInitialMessages());
    setHasMore(hasMoreFn());
  }, [conversationId, getInitialMessages, hasMoreFn]);

  const handleLoadMore = () => {
    if (!conversationId || isPending || !hasMore) return;
    setIsPending(true);
    const newMessages = loadMoreFn();
    setMessages((prev) => [...newMessages, ...prev]);
    setHasMore(hasMoreFn());
    setIsPending(false);
  };
 console.log("conversation : ", data);
  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background border">
      {/* Sidebar : Scrollable indépendamment */}
      <div
        className={`${selectedChat ? "hidden lg:flex" : "flex"} w-full lg:w-80 flex-col`}
      >
        <ChatSidebar
          chats={mockConversations}
          selectedId={selectedChat?.id}
          onSelectChat={setSelectedChat}
        />
      </div>
      {/* Main Chat Window */}
      <div
        className={`${!selectedChat ? "hidden lg:flex" : "flex"} flex-1 flex-col overflow-hidden`}
      >
        {selectedChat ? (
          <>
            {/* Header Fixe */}
            <div className="h-16 flex items-center justify-between px-4 bg-background">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  onClick={() => setSelectedChat(null)}
                >
                  <ArrowLeft />
                </Button>
                <Avatar>
                  <AvatarImage src={selectedChat.avatar || ""} />
                  <AvatarFallback>{selectedChat.initials}</AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-sm font-bold">{selectedChat.name}</h2>
                  <span className="text-xs text-green-500">En ligne</span>
                </div>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon">
                  <Video className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon">
                  <Phone className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>
            </div>
            {/* Zone de messages : Scrollable indépendamment */}
            <ChatMessageList
              messages={messages}
              onLoadMore={handleLoadMore}
              isPending={isPending}
              allItemsCount={1000}
              currentChatId={conversationId}
            />
            {/* Input Fixe en bas */}
            <ChatInput onSendMessage={(txt) => console.log("Envoi de:", txt)} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            Sélectionnez une discussion pour commencer
          </div>
        )}
      </div>
    </div>
  );
}

ChatPage.layout = (page: React.ReactNode) => <AppLayout>{page}</AppLayout>;
