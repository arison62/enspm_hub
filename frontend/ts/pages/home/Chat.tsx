import { useState, useEffect } from "react";
import { ChatSidebar } from "./components/network/chat/chat-sidebar";
import { ChatMessageList } from "./components/network/chat/chat-message-list";
import AppLayout from "@/components/layouts/app-layout";
import { Button } from "@/components/ui/button";
import { AvatarImage, AvatarFallback, Avatar } from "@/components/ui/avatar";
import { ArrowLeft, Video, Phone, MoreVertical } from "lucide-react";
import { ChatInput } from "./components/network/chat/chat-input";
import { getMessagesForConversation } from "./components/network/chat/mock";
import { useGetConversations, useGetMessages } from "@/api/network/chat";
import { formatLinkedInDuration, getAvatarFallback } from "@/lib/utils";
import type { ChatConversationUI, ChatMessageUI } from "@/types/network";




export default function ChatPage() {
  const { data } = useGetConversations({
    pagination: { pageSize: 10, pageIndex: 0 },
  });

  const [selectedChat, setSelectedChat] = useState<ChatConversationUI | null>(
    null,
  );
  const { data } = useGetMessages({
    conversationId: selectedChat?.id,
    pagination: {
      pageSize: 10,
      pageIndex: 0,
    },
  });
  const [conversations, setConversations] = useState<ChatConversationUI[]>([]);
  const [messages, setMessages] = useState<ChatMessageUI[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [isPending, setIsPending] = useState(false);

  const conversationId = selectedChat?.id.toString() || "";
  const {
    getInitialMessages,
    loadMore: loadMoreFn,
    hasMore: hasMoreFn,
  } = getMessagesForConversation(conversationId);

  useEffect(() => {
    const transfConv = data.items.map((conv) => {
      const chat = {} as ChatConversationUI;
      chat.id = conv.id;
      chat.type = conv.type;
      chat.lastMessage = conv.dernier_message?.contenu;
      chat.unread = conv.messages_non_lus;
      chat.time = formatLinkedInDuration(conv.dernier_message?.created_at);
      if (conv.type == "dm") {
        chat.avatar = conv.contact?.photo_profil;
        chat.name = conv.contact?.nom_complet;
      } else if (conv.type == "group") {
        chat.avatar = conv.groupe?.image_url;
        chat.name = conv.groupe?.nom;
      }
      return chat;
    });
    setConversations([...transfConv]);
  }, [data.meta.page]);

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
          chats={conversations}
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
                  <AvatarFallback>
                    {getAvatarFallback(selectedChat.name)}
                  </AvatarFallback>
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
