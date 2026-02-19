import { useState, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
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
  chatKeys,
} from "@/api/network/chat";
import { formatLinkedInDuration, getAvatarFallback } from "@/lib/utils";
import type {
  ChatConversationUI,
  ChatMessageUI,
  Message,
  MessageListResponse,
} from "@/types/network";
import { useAuth } from "@/hooks/use-auth";
import { v4 as uuidv4 } from "uuid";

export default function ChatPage() {
  const { profil } = useAuth();
  const profilId = profil?.id;
  const queryClient = useQueryClient();

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
    conversationId: selectedChat?.id || null,
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
  const [selectedMessage, setSelectedMessage] = useState<ChatMessageUI | null>(
    null,
  )
  const conversationId = selectedChat?.id.toString() || "";

  const rebuildMessagesFromCache = useCallback(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    // Récupère TOUTES les pages en cache pour cette conversation
    const allCachedPages = queryClient.getQueriesData<MessageListResponse>({
      queryKey: chatKeys.messages(conversationId),
      exact: false,
    });

    let allMessages: Message[] = [];
    allCachedPages.forEach(([, pageData]) => {
      if (pageData?.items) allMessages = [...allMessages, ...pageData.items];
    });

    // Déduplication + tri chronologique
    const seen = new Set<string>();
    const unique = allMessages
      .filter((msg) => {
        const key = msg.client_id || msg.id;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      );

    // Transformation en UI type
    const transfMsg: ChatMessageUI[] = unique.map((msg) => ({
      id: msg.id,
      clientId: msg.client_id,
      conversationId: msg.conversation_id,
      content: msg.contenu,
      author: msg.expediteur?.nom_complet,
      time: msg.created_at,
      type: msg.type,
      isOwn: msg.expediteur?.id === profilId,
      media: msg.media_url,
      mediaInfo: msg.media_info,
      mediaSize: msg.media_info?.taille,
      mediaType: msg.media_info?.type,
      repliedTo: msg.reponse_a
        ? {
            id: msg.reponse_a.id,
            content: msg.reponse_a.contenu,
            author: msg.reponse_a.expediteur?.nom_complet,
            media: msg.reponse_a.media_url,
            mediaType: msg.reponse_a.media_info?.type,
          }
        : undefined,

      canDelete:
        msg.expediteur?.id === profilId || selectedChat?.role === "admin",
    }));

    setMessages(transfMsg);
  }, [conversationId, profilId, selectedChat?.role, queryClient, markRead]);

  useEffect(() => {
    rebuildMessagesFromCache();
  }, [rebuildMessagesFromCache, messagesData]); // messagesData change → rebuild

  useEffect(() => {
    if (!conversationId) return;

    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (
        (event.type === "updated" || event.type === "removed") &&
        event.query.queryKey[0] === "chat" &&
        event.query.queryKey[1] === "messages" &&
        event.query.queryKey[2] === conversationId
      ) {
        rebuildMessagesFromCache();
      }
    });

    return unsubscribe;
  }, [conversationId, rebuildMessagesFromCache, queryClient]);

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
    setMessagesPagination({ pageSize: 10, pageIndex: 0 });
  }, [conversationId]);

  useEffect(() => {
    if (selectedChat?.unread && selectedChat.unread > 0) {
      markRead(conversationId);
    }
  }, [conversationId]);

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
              onSelectMessageChange={setSelectedMessage}
              onLoadMore={loadMoreMessages}
              isPending={messagesPending}
              allItemsCount={messagesData.meta.total_items}
              onDeleteMessage={handleDeleteMessage}
              currentChatId={conversationId}
            />
            {/* Input Fixe en bas */}
            <ChatInput
              selectedMessage={selectedMessage}
              onSelectedMessageChange={setSelectedMessage}
              onSendMessage={(msg) => {
                sendMessage({
                  conversationId: selectedChat.id,
                  data: {
                    contenu: msg.text,
                    media_base64: msg.media,
                    client_id: uuidv4(),
                    reponse_a_id: selectedMessage?.id,
                  },
                });
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
