import { useState, useEffect, useMemo, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useDebounce } from "@uidotdev/usehooks";
import { v4 as uuidv4 } from "uuid";

import {
  useGetConversations,
  useGetMessages,
  useSendMessage,
  useMarkConversationRead,
  useDeleteMessage,
  useGetConversation,
  useGetReferencePreview,
  chatKeys,
} from "@/api/network/chat";
import { useAuth } from "@/hooks/use-auth";
import {
  transformMessage,
  transformConversation,
  deduplicateAndSort,
} from "@/lib/chat-utils";
import type {
  ChatConversationUI,
  ChatMessageUI,
  Message,
  MessageListResponse,
  RepliedToMessage,
} from "@/types/network";

// ============================================
// PAGINATION STATE
// ============================================

const DEFAULT_PAGE = { pageSize: 10, pageIndex: 0 };

// ============================================
// HOOK
// ============================================

export function useChatPage() {
  const { profil } = useAuth();
  const queryClient = useQueryClient();

  // ── Search / filter ──────────────────────────────────────────────────────
  const [conversationQuery, setConversationQuery] = useState<string>("");
  const debouncedQuery = useDebounce(conversationQuery, 500);

  // ── URL-driven pre-selection ──────────────────────────────────────────────
  const [conversationUriId, setConversationUriId] = useState<string | null>(
    null,
  );

  // ── Pagination ───────────────────────────────────────────────────────────
  const [messagesPagination, setMessagesPagination] = useState(DEFAULT_PAGE);
  const [dmPagination, setDmPagination] = useState(DEFAULT_PAGE);
  const [groupPagination, setGroupPagination] = useState(DEFAULT_PAGE);

  // ── UI state ─────────────────────────────────────────────────────────────
  const [selectedTab, setSelectedTab] = useState<"dm" | "groups">("dm");
  const [selectedChat, setSelectedChat] = useState<ChatConversationUI | null>(
    null,
  );
  const [selectedReference, setSelectedReference] =
    useState<RepliedToMessage | null>(null);

  const conversationId = selectedChat?.id ?? "";
  // Reference preview params (from URL)
  const [referenceParams, setReferenceParams] = useState<{
    referenceType: string;
    referenceId: string;
  } | null>(null);

  const { data: referencePreview } = useGetReferencePreview({
    referenceId: referenceParams?.referenceId ?? "",
    referenceType: referenceParams?.referenceType ?? "",
    enabled: !!referenceParams,
  });

  // ── API queries ──────────────────────────────────────────────────────────
  const { data: conversationFromUrl } = useGetConversation(conversationUriId);

  const { data: dmData, isPending: dmPending } = useGetConversations({
    pagination: dmPagination,
    type: "dm",
    query: debouncedQuery,
  });

  const { data: groupData, isPending: groupPending } = useGetConversations({
    pagination: groupPagination,
    type: "group",
    query: debouncedQuery,
  });

  const { data: messagesData, isPending: messagesPending } = useGetMessages({
    conversationId: conversationId || null,
    pagination: messagesPagination,
  });

  // ── Mutations ────────────────────────────────────────────────────────────
  const { mutate: sendMessageMutate } = useSendMessage();
  const { mutate: markRead } = useMarkConversationRead();
  const { mutate: deleteMessageMutate } = useDeleteMessage();

  // ── Derived pagination flags ─────────────────────────────────────────────
  const hasMoreMessages =
    messagesData.meta.page < messagesData.meta.total_pages;
  const hasMoreDm = dmData.meta.page < dmData.meta.total_pages;
  const hasMoreGroup = groupData.meta.page < groupData.meta.total_pages;

  // ── Messages: rebuilt from all cached pages ──────────────────────────────
  const messages = useMemo<ChatMessageUI[]>(() => {
    if (!conversationId) return [];

    const allCachedPages = queryClient.getQueriesData<MessageListResponse>({
      queryKey: chatKeys.messages(conversationId),
      exact: false,
    });

    let allMessages: Message[] = [];
    allCachedPages.forEach(([, page]) => {
      if (page?.items) allMessages = [...allMessages, ...page.items];
    });

    const sorted = deduplicateAndSort(
      allMessages,
      (msg) => msg.client_id ?? msg.id,
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );

    const isAdmin = selectedChat?.role === "admin";
    return sorted.map((msg) => transformMessage(msg, profil?.id, isAdmin));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    conversationId,
    messagesData,
    profil?.id,
    selectedChat?.role,
    queryClient,
  ]);

  // ── Conversations: merged from DM + group + URL-driven ───────────────────
  const conversations = useMemo<ChatConversationUI[]>(() => {
    const raw = [...dmData.items, ...groupData.items];
    if (conversationFromUrl) raw.push(conversationFromUrl);

    const sorted = deduplicateAndSort(
      raw,
      (conv) => conv.id,
      (a, b) => {
        const aTime = a.dernier_message?.created_at
          ? new Date(a.dernier_message.created_at).getTime()
          : Number.MAX_SAFE_INTEGER;
        const bTime = b.dernier_message?.created_at
          ? new Date(b.dernier_message.created_at).getTime()
          : Number.MAX_SAFE_INTEGER;
        return bTime - aTime; // descending: most recent first
      },
    );

    return sorted.map(transformConversation);
  }, [dmData, groupData, conversationFromUrl]);

  // ── Subscribe to cache updates to keep messages fresh ───────────────────
  // This is needed for optimistic updates / websocket invalidations.
  const rebuildMessages = useCallback(() => {
    // Triggering a re-render is enough since `messages` is a useMemo that reads from cache.
    // We force it by invalidating slightly; the simplest approach is to just invalidate and
    // let react-query re-run. If you need imperatively re-read, keep a counter state instead.
  }, []);

  useEffect(() => {
    if (!conversationId) return;

    return queryClient.getQueryCache().subscribe((event) => {
      const key = event.query.queryKey;
      if (
        (event.type === "updated" || event.type === "removed") &&
        key[0] === "chat" &&
        key[1] === "messages" &&
        key[2] === conversationId
      ) {
        rebuildMessages();
      }
    });
  }, [conversationId, queryClient, rebuildMessages]);

  useEffect(() => {
    if (referencePreview) {
      const uiData: RepliedToMessage = {
        id: referencePreview.id,
        title: referencePreview.titre,
        content: referencePreview.apercu,
        type: referencePreview.type,
        author: referencePreview.sous_titre,
        url: referencePreview.url,
        media: referencePreview.media_url,
        mediaType: referencePreview.media_type,
      };
      setSelectedReference(uiData);
      setReferenceParams(null);
    }
  }, [referencePreview]);

  // ── Reset message pagination when switching chat ─────────────────────────
  useEffect(() => {
    setMessagesPagination(DEFAULT_PAGE);
  }, [conversationId]);

  // ── Mark conversation as read when entering it ───────────────────────────
  useEffect(() => {
    if (conversationId && selectedChat?.unread && selectedChat.unread > 0) {
      markRead(conversationId);
    }
  }, [conversationId]); // intentionally narrow: only trigger on navigation

  // ── Hydrate selected chat from URL param ─────────────────────────────────
  useEffect(() => {
    if (!conversationFromUrl) return;
    setSelectedChat(transformConversation(conversationFromUrl));
  }, [conversationFromUrl]);

  // ── Read URL query params on mount ───────────────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const dmId = params.get("dm");
    const type = params.get("type");
    const refId = params.get("ref");
    const groupId = params.get("group");

    if (dmId) {
      setSelectedTab("dm");
      setConversationUriId(dmId);
    } else if (groupId) {
      setSelectedTab("groups");
      setConversationUriId(groupId);
    }
    if (type && refId) {
      setReferenceParams({ referenceType: type, referenceId: refId });
    }

    // Clean the URL without reload
    const url = new URL(window.location.href);
    url.searchParams.delete("dm");
    url.searchParams.delete("group");
    url.searchParams.delete("type");
    url.searchParams.delete("ref");
    window.history.replaceState({}, "", url.href);
  }, []);

  // ── Actions ──────────────────────────────────────────────────────────────
  const handleSearchChange = useCallback((value: string) => {
    setConversationQuery(value);
    setDmPagination((prev) => ({ ...prev, pageIndex: 0 }));
    setGroupPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }, []);

  const loadMoreMessages = useCallback(() => {
    if (messagesPending || !hasMoreMessages) return;
    setMessagesPagination((prev) => ({
      ...prev,
      pageIndex: prev.pageIndex + 1,
    }));
  }, [messagesPending, hasMoreMessages]);

  const loadMoreConversations = useCallback(
    (type: "dm" | "group") => {
      if (type === "dm") {
        if (dmPending || !hasMoreDm) return;
        setDmPagination((prev) => ({ ...prev, pageIndex: prev.pageIndex + 1 }));
      } else {
        if (groupPending || !hasMoreGroup) return;
        setGroupPagination((prev) => ({
          ...prev,
          pageIndex: prev.pageIndex + 1,
        }));
      }
    },
    [dmPending, hasMoreDm, groupPending, hasMoreGroup],
  );

  const sendMessage = useCallback(
    (text?: string, media?: string) => {
      if (!selectedChat) return;
      sendMessageMutate({
        conversationId: selectedChat.id,
        data: {
          contenu: text,
          media_base64: media,
          client_id: uuidv4(),
          reference_id: selectedReference?.id,
          reference_type: selectedReference?.type,
        },
      });
    },
    [selectedChat, selectedReference, sendMessageMutate],
  );

  const deleteMessage = useCallback(
    (messageId: string) => {
      if (!conversationId) return;
      deleteMessageMutate({ messageId, conversationId });
    },
    [conversationId, deleteMessageMutate],
  );

  /**
   * Returns pagination info for the ChatSidebar's "load more" strategy.
   */
  const getConversationPaginationData = useCallback(
    (type: "dm" | "group") => {
      if (type === "dm") {
        return {
          isPending: dmPending,
          hasMore: hasMoreDm,
          allItemsCount: dmData.meta.total_items,
          currentItemsLength: dmData.items.length,
          loadMore: () => loadMoreConversations("dm"),
        };
      }
      return {
        isPending: groupPending,
        hasMore: hasMoreGroup,
        allItemsCount: groupData.meta.total_items,
        currentItemsLength: groupData.items.length,
        loadMore: () => loadMoreConversations("group"),
      };
    },
    [
      hasMoreDm,
      hasMoreGroup,
      dmData.meta,
      dmData.items.length,
      groupData.meta,
      groupData.items.length,
      loadMoreConversations,
      dmPending,
      groupPending,
    ],
  );

  return {
    // State
    selectedTab,
    setSelectedTab,
    selectedChat,
    setSelectedChat,
    selectedReference,
    setSelectedReference,
    conversations,
    messages,

    // Loading
    messagesPending,

    // Pagination metadata
    messagesTotalItems: messagesData.meta.total_items,
    hasMoreMessages,

    // Actions
    handleSearchChange,
    loadMoreMessages,
    sendMessage,
    deleteMessage,
    getConversationPaginationData,

    // Computed
    conversationId,
  };
}
