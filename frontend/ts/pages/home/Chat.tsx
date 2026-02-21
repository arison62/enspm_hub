import { useState, useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ChatSidebar } from "./components/network/chat/chat-sidebar";
import { ChatMessageList } from "./components/network/chat/chat-message-list";
import AppLayout from "@/components/layouts/app-layout";
import { Button } from "@/components/ui/button";
import { AvatarImage, AvatarFallback, Avatar } from "@/components/ui/avatar";
import {
  ArrowLeft,
  MoreVertical,
} from "lucide-react";
import { ChatInput } from "./components/network/chat/chat-input";
import {
  useGetConversations,
  useGetMessages,
  useSendMessage,
  useMarkConversationRead,
  useDeleteMessage,
  useGetConversation,
  chatKeys,
} from "@/api/network/chat";
import { getAvatarFallback } from "@/lib/utils";
import type {
  ChatConversationUI,
  ChatMessageUI,
  Message,
  MessageListResponse,
} from "@/types/network";
import { useAuth } from "@/hooks/use-auth";
import { v4 as uuidv4 } from "uuid";
import { useDebounce } from "@uidotdev/usehooks";

const formatDate = (date: string) => {
  const now = new Date();
  const createdAt = new Date(date);

  // Difference  ms et en jours
  const diffMs = now.getTime() - createdAt.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  const todayStart = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const dateStart = new Date(
    createdAt.getFullYear(),
    createdAt.getMonth(),
    createdAt.getDate(),
  ).getTime();
  const diffDays = Math.floor((todayStart - dateStart) / (1000 * 60 * 60 * 24));

  if (diffSec < 60) {
    return "A l'instant";
  }
  if (diffDays === 0) {
    return createdAt.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  if (diffDays === 1) {
    return "Hier";
  }

  return createdAt.toLocaleDateString();
};

export default function ChatPage() {
  const { profil } = useAuth();
  const profilId = profil?.id;
  const queryClient = useQueryClient();
  const [conversationQuery, setConversationQuery] = useState<string | null>(
    null,
  );
  const debouncedConversationQuery = useDebounce(conversationQuery, 500);

  const [conversationUriId, setConversationUriId] = useState<string | null>(
    null,
  );
  const [messagesPagination, setMessagesPagination] = useState({
    pageSize: 10,
    pageIndex: 0,
  });
  const [conversationDmPagination, setConversationsDmPagination] = useState({
    pageSize: 10,
    pageIndex: 0,
  });
  const { data: conversationData } =
    useGetConversation(conversationUriId);

  const [conversationGroupPagination, setConversationsGroupPagination] =
    useState({
      pageSize: 10,
      pageIndex: 0,
    });

  const { data: conversationsDmData, isPending: conversationsDmPending } =
    useGetConversations({
      pagination: { ...conversationDmPagination },
      type: "dm",
      query: debouncedConversationQuery,
    });
  const { data: conversationsGroupData, isPending: conversationsGroupPending } =
    useGetConversations({
      pagination: { ...conversationGroupPagination },
      type: "group",
      query: debouncedConversationQuery,
    });

  const [selectedTab, setSelectedTab] = useState<"dm" | "groups">("dm");
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

  const [selectedMessage, setSelectedMessage] = useState<ChatMessageUI | null>(
    null,
  );
  const hasMoreDm =
    conversationsDmData.meta.page < conversationsDmData.meta.total_pages;

  const hasMoreGroup =
    conversationsGroupData.meta.page < conversationsGroupData.meta.total_pages;

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
      media: msg.media_info?.url,
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
  }, [conversationId, profilId, selectedChat?.role, queryClient]);

  useEffect(() => {
    rebuildMessagesFromCache();
  }, [rebuildMessagesFromCache, messagesData]);

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
    const conversationsData = [
      ...conversationsDmData.items,
      ...conversationsGroupData.items,
    ];
    if (conversationData) {
      conversationsData.push(conversationData);
    }

    // Déduplication + tri chronologique
    const seen = new Set<string>();
    const unique = conversationsData
      .filter((conv) => {
        if (seen.has(conv.id)) return false;
        seen.add(conv.id);
        return true;
      })
      .sort((a, b) => {
        const aCreatedAt = a.dernier_message?.created_at
          ? new Date(a.dernier_message.created_at).getTime()
          : Number.MAX_SAFE_INTEGER;
        const bCreatedAt = b.dernier_message?.created_at
          ? new Date(b.dernier_message.created_at).getTime()
          : Number.MAX_SAFE_INTEGER;

        return bCreatedAt - aCreatedAt; // Tri décroissant (plus récent en premier)
      });

    const transfConv = unique.map((conv) => {
      const chat = {} as ChatConversationUI;
      chat.id = conv.id;
      chat.type = conv.type;
      chat.lastMessage = conv.dernier_message?.contenu;
      chat.unread = conv.messages_non_lus;
      chat.time = formatDate(conv.dernier_message?.created_at);
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

    setConversations(transfConv);
  }, [conversationsDmData, conversationsGroupData, conversationData]);

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
  }, [messagesData.meta.page]);

  // Get conversation id from url
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const dmConvId = urlParams.get("dm");
    const groupConvId = urlParams.get("group");
    if (dmConvId) {
      setSelectedTab("dm");
      setConversationUriId(dmConvId);
    } else if (groupConvId) {
      setSelectedTab("groups");
      setConversationUriId(groupConvId);
    }
    const url = new URL(window.location.href);
    url.searchParams.delete("dm");
    url.searchParams.delete("group");
    window.history.replaceState({}, "", url.href);
  }, []);
  useEffect(() => {
    if (conversationData) {
      setSelectedChat({
        id: conversationData.id,
        type: conversationData.type,
        name:
          conversationData.type === "dm"
            ? conversationData.contact?.nom_complet
            : conversationData.groupe?.nom,
        avatar:
          conversationData.type === "dm"
            ? conversationData.contact?.photo_profil
            : conversationData.groupe?.image_url,
        role: conversationData.role,
        unread: conversationData.messages_non_lus,
        lastMessage: conversationData.dernier_message?.contenu,
        time: conversationData.dernier_message?.created_at,
      });
    }
  }, [conversationData]);

  const loadMoreMessages = () => {
    if (!conversationId || messagesPending || !hasMoreMessage) return;
    setMessagesPagination((prev) => ({
      ...prev,
      pageIndex: prev.pageIndex + 1,
    }));
  };

  const loadMoreConversations = (type: "dm" | "group") => {
    switch (type) {
      case "dm":
        if (conversationsDmPending || !hasMoreDm) return;
        setConversationsDmPagination((prev) => ({
          ...prev,
          pageIndex: prev.pageIndex + 1,
        }));
        break;
      case "group":
        if (conversationsGroupPending || !hasMoreGroup) return;
        setConversationsGroupPagination((prev) => ({
          ...prev,
          pageIndex: prev.pageIndex + 1,
        }));
        break;
    }
  };
  const handleQueryChange = (value: string) => {
    setConversationQuery(value);
    setConversationsDmPagination((prev) => ({ ...prev, pageIndex: 0 }));
    setConversationsGroupPagination((prev) => ({ ...prev, pageIndex: 0 }));
  };
  const getConversationData = (type: "dm" | "group") => {
    switch (type) {
      case "dm":
        return {
          isPending: hasMoreDm,
          allItemsCount: conversationsDmData.meta.total_items,
          currentItemsLength: conversationsDmData.items.length,
          loadMore: () => loadMoreConversations("dm"),
        };
      case "group":
        return {
          isPending: hasMoreGroup,
          allItemsCount: conversationsGroupData.meta.total_items,
          currentItemsLength: conversationsGroupData.items.length,
          loadMore: () => loadMoreConversations("group"),
        };
    }
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
          onSearch={handleQueryChange}
          selectedId={selectedChat?.id}
          onSelectChat={setSelectedChat}
          getCurrentData={getConversationData}
          convTab={selectedTab}
          onChangeConvTab={setSelectedTab}
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
                </div>
              </div>
              <div className="flex gap-1">
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
