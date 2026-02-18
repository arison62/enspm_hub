import { useState, useEffect } from "react";
import { ChatSidebar } from "./components/network/chat/chat-sidebar";
import { ChatMessageList } from "./components/network/chat/chat-message-list";
import AppLayout from "@/components/layouts/app-layout";
import { Button } from "@/components/ui/button";
import { AvatarImage, AvatarFallback, Avatar } from "@/components/ui/avatar";
import { ArrowLeft, Video, Phone, MoreVertical } from "lucide-react";
import { ChatInput } from "./components/network/chat/chat-input";
import {
  useGetConversations,
  useGetMessages,
  useSendMessage,
  useMarkConversationRead,
  useDeleteMessage,
} from "@/api/network/chat";
import { formatLinkedInDuration, getAvatarFallback } from "@/lib/utils";
import type { ChatConversationUI, ChatMessageUI } from "@/types/network";
import { useAuth } from "@/hooks/use-auth";

export default function ChatPage() {
  const { profil } = useAuth();
  const profilId = profil?.id;
  const [messagesPagination, setMessagesPagination] = useState({
    pageSize: 10,
    pageIndex: 0,
  });
  const [conversationsPagination, setConversationsPagination] = useState({
    pageSize: 10,
    pageIndex: 0,
  });
  const { data: conversationsData, isPending: conversationsPending } =
    useGetConversations({
      pagination: { ...conversationsPagination },
    });

  const [selectedChat, setSelectedChat] = useState<ChatConversationUI | null>(
    null,
  );
  const { mutate: sendMessage } = useSendMessage();
  const { mutate: markRead } = useMarkConversationRead();
  const { mutate: deleteMessage } = useDeleteMessage();

  const { data: messagesData, isPending: messagesPending } = useGetMessages({
    conversationId: selectedChat?.id,
    pagination: {
      ...messagesPagination,
    },
  });
  const [conversations, setConversations] = useState<ChatConversationUI[]>([]);
  const [messages, setMessages] = useState<ChatMessageUI[]>([]);

  const [hasMoreMessage, setHasMoreMessage] = useState(
    messagesData.meta.page < messagesData.meta.total_pages,
  );
  const [hasMoreConversation, setHasMoreConversation] = useState(
    conversationsData.meta.page < conversationsData.meta.total_pages,
  );
  const conversationId = selectedChat?.id.toString() || "";

  useEffect(() => {
    const transfConv = conversationsData.items.map((conv) => {
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
        chat.role = conv.role;
        chat.name = conv.groupe?.nom;
      }
      return chat;
    });
    setConversations([...transfConv]);
  }, [conversationsData.items, conversationsData.meta.page]);

  useEffect(() => {
    const transfMsg = messagesData.items.map((msg) => {
      const message = {} as ChatMessageUI;
      message.id = msg.id;
      message.clientId = msg.client_id;
      message.conversationId = msg.conversation_id;
      message.content = msg.contenu;
      message.author = msg.expediteur?.nom_complet;
      message.time = msg.created_at;
      message.type = msg.type;
      message.isOwn = msg.expediteur?.id === profilId;
      message.canDelete = message.isOwn || selectedChat.role === "admin";
      return message;
    });

    setMessages((prev) => {
      // 1. Fusionner
      const allMessages = [...transfMsg, ...prev];

      // 2. Déduplication et filtrage par conversation
      const seenIds = new Set();
      const uniqueMessages = allMessages.filter((msg) => {
        if (msg.conversationId !== conversationId) return false;
        if (seenIds.has(msg.clientId)) return false;
        seenIds.add(msg.clientId);
        return true;
      });

      // 3. Tri chronologique (du plus ancien au plus récent)
      return uniqueMessages.sort(
        (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime(),
      );
    });
  }, [conversationId, messagesData.items, messagesData.meta.page]);

  useEffect(() => {
    setHasMoreMessage(messagesData.meta.page < messagesData.meta.total_pages);
    setHasMoreConversation(
      conversationsData.meta.page < conversationsData.meta.total_pages,
    );
  }, [messagesData.meta.page, conversationsData.meta.page]);

  const loadMoreMessages = () => {
    if (!conversationId || messagesPending || !hasMoreMessage) return;
    setMessagesPagination((prev) => ({
      ...prev,
      pageIndex: prev.pageIndex + 1,
    }));
  };

  const loadMoreConversations = () => {
    if (conversationsPending || !hasMoreConversation) return;
    setConversationsPagination((prev) => ({
      ...prev,
      pageIndex: prev.pageIndex + 1,
    }));
  };
  useEffect(() => {
    setMessagesPagination({
      pageSize: 10,
      pageIndex: 0,
    });
    if (selectedChat && selectedChat.unread > 0) {
      markRead(conversationId);
    }
  }, [conversationId]);

  const handleDeleteMessage = (messageId: string, conversationId: string) => {
    deleteMessage({
      messageId,
      conversationId,
    });
  };

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
              onLoadMore={loadMoreMessages}
              isPending={messagesPending}
              allItemsCount={messagesData.meta.total_items}
              onDeleteMessage={handleDeleteMessage}
              currentChatId={conversationId}
            />
            {/* Input Fixe en bas */}
            <ChatInput
              onSendMessage={(msg) => {
                sendMessage({
                  conversationId: selectedChat.id,
                  data: {
                    contenu: msg.text,
                    media_base64: msg.media,
                  },
                });
                console.log("Message envoyer", msg);
              }}
            />
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
