import type {
  Conversation,
  Message,
  ChatMessageUI,
  ChatConversationUI,
} from "@/types/network";

// ============================================
// DATE FORMATTING
// ============================================

export function formatChatDate(date: string): string {
  const now = new Date();
  const createdAt = new Date(date);

  const diffSec = Math.floor((now.getTime() - createdAt.getTime()) / 1000);

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

  if (diffSec < 60) return "À l'instant";
  if (diffDays === 0)
    return createdAt.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  if (diffDays === 1) return "Hier";
  return createdAt.toLocaleDateString();
}

// ============================================
// DATA TRANSFORMATIONS
// ============================================

/**
 * Transforms a raw API Message into a ChatMessageUI object.
 * @param msg - Raw message from the API
 * @param currentUserId - ID of the logged-in user (used to set `isOwn` and `canDelete`)
 * @param isAdmin - Whether the current user is admin of the conversation
 */
export function transformMessage(
  msg: Message,
  currentUserId: string | undefined,
  isAdmin: boolean,
): ChatMessageUI {

  return {
    id: msg.id,
    clientId: msg.client_id,
    conversationId: msg.conversation_id,
    content: msg.contenu,
    author: msg.expediteur?.nom_complet,
    author_slug: msg.expediteur?.slug,
    time: msg.created_at,
    type: msg.type,
    avatar: msg.expediteur?.photo_url,
    isOwn: msg.expediteur?.id === currentUserId,
    media: msg.media_info?.url,
    mediaInfo: msg.media_info,
    mediaSize: msg.media_info?.taille,
    mediaType: msg.media_info?.type,
    repliedTo: msg.reference
      ? {
          id: msg.reference.id,
          type: msg.reference.type,
          title: msg.reference.sous_titre,
          content: msg.reference.apercu,
          author: msg.reference.titre,
          media: msg.reference.media_url,
          url: msg.reference.url,
          mediaType: msg.reference.media_type,
        }
      : undefined,
    canDelete: msg.expediteur?.id === currentUserId || isAdmin,
  };
}

/**
 * Transforms a raw API Conversation into a ChatConversationUI object.
 */
export function transformConversation(conv: Conversation): ChatConversationUI {
  const base = {
    id: conv.id,
    type: conv.type,
    lastMessage: conv.dernier_message?.contenu,
    unread: conv.messages_non_lus,
    time: conv.dernier_message?.created_at
      ? formatChatDate(conv.dernier_message.created_at)
      : undefined,
  } satisfies Partial<ChatConversationUI>;

  if (conv.type === "dm") {
    return {
      ...base,
      type: "dm",
      avatar: conv.contact?.photo_url,
      name: conv.contact?.nom_complet,
    };
  }

  return {
    ...base,
    type: "group",
    avatar: conv.groupe?.image_url,
    name: conv.groupe?.nom,
    role: conv.role as ChatConversationUI["role"],
  };
}

/**
 * Deduplicates an array of items by a string key and sorts by a comparator.
 */
export function deduplicateAndSort<T>(
  items: T[],
  getKey: (item: T) => string,
  comparator: (a: T, b: T) => number,
): T[] {
  const seen = new Set<string>();
  return items
    .filter((item) => {
      const key = getKey(item);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort(comparator);
}
