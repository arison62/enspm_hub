// src/lib/chat-mock-data.ts
import type {
  ChatMessage,
  ChatConversation,
  MessageStatus,
} from "@/types/network";

// ==================== CONVERSATIONS (sidebar) ====================
export const mockConversations: ChatConversation[] = [
  // DMs
  {
    id: "dm-alice",
    type: "dm",
    name: "Alice Mballa",
    avatar: "https://i.pravatar.cc/150?u=alice",
    initials: "AM",
    lastMessage: "On se voit demain au labo ?",
    time: "14:32",
    unread: 3,
    online: true,
  },
  {
    id: "dm-boris",
    type: "dm",
    name: "Boris Kamdem",
    avatar: "https://i.pravatar.cc/150?u=boris",
    initials: "BK",
    lastMessage: "Le code review est prêt",
    time: "11:15",
    unread: 0,
    online: false,
  },
  {
    id: "dm-sarah",
    type: "dm",
    name: "Sarah Ngo",
    avatar: "https://i.pravatar.cc/150?u=sarah",
    initials: "SN",
    lastMessage: "📸",
    time: "hier",
    unread: 1,
    online: true,
  },

  // GROUPES
  {
    id: "grp-dev",
    type: "group",
    name: "Développeurs Systaliko",
    avatar: null,
    initials: "DEV",
    lastMessage: "Jean : Quelqu’un a testé le nouveau WebSocket ?",
    time: "10:45",
    unread: 12,
    online: false,
  },
  {
    id: "grp-projet-immob",
    type: "group",
    name: "Projet Immob - SecureEstate",
    avatar: null,
    initials: "IMM",
    lastMessage: "Vous avez vu le dernier commit de sécurité ?",
    time: "09:20",
    unread: 0,
    online: true,
  },
  {
    id: "grp-famille",
    type: "group",
    name: "Famille Ngo",
    avatar: null,
    initials: "FAM",
    lastMessage: "Maman : Qui vient ce dimanche ?",
    time: "hier",
    unread: 5,
    online: false,
  },
];

// ==================== GÉNÉRATEUR LAZY 1000 MESSAGES ====================
function randomDate(daysAgo: number): string {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo - Math.random() * 5);
  return date.toISOString();
}

function* generateMessagesForConversation(
  conversationId: string,
  batchSize = 20,
): Generator<ChatMessage[], void, undefined> {
  let idCounter = 10000; // pour éviter les conflits avec les messages réels
  let total = 0;
  const isGroup = conversationId.startsWith("grp");

  const participants = isGroup
    ? ["Alice", "Boris", "Sarah", "Jean", "Paul"]
    : ["Alice", "Moi"];

  while (total < 1000) {
    const batch: ChatMessage[] = [];
    const remaining = 1000 - total;
    const size = Math.min(batchSize, remaining);

    for (let i = 0; i < size; i++) {
      const isOwn = Math.random() < 0.45; // ~45% de tes messages
      const sender =
        participants[Math.floor(Math.random() * participants.length)];
      const isImage = Math.random() < 0.18;

      const message: ChatMessage = {
        id: `msg_${conversationId}_${idCounter++}`,
        senderId: isOwn ? "current-user" : sender.toLowerCase(),
        isOwn,
        content: isImage
          ? undefined
          : `${isOwn ? "Moi" : sender} : ${["Salut", "Ok", "Super idée !", "😂😂", "On avance bien", "Faut qu’on parle de la sécurité"][Math.floor(Math.random() * 6)]}`,
        type: isImage ? "image" : "text",
        images: isImage
          ? [`https://picsum.photos/id/${100 + idCounter}/600/400`]
          : undefined,
        time: randomDate(total + i),
        status: isOwn
          ? (["sent", "delivered", "read"][
              Math.floor(Math.random() * 3)
            ] as MessageStatus)
          : "read",
        author: isOwn ? undefined : sender,
        avatarUrl: isOwn
          ? undefined
          : `https://i.pravatar.cc/150?u=${sender.toLowerCase()}`,
        avatarFallback: isOwn ? undefined : sender[0],
      };

      batch.push(message);
    }

    yield batch;
    total += size;
  }
}

// ==================== STORE MOCK (pour ton composant) ====================
export const mockMessagesStore = new Map<string, ChatMessage[]>();

// Fonction pour charger les messages d’une conversation (avec lazy loading)
export function getMessagesForConversation(
  conversationId: string,
  pageSize = 20,
): {
  getInitialMessages: () => ChatMessage[];
  loadMore: () => ChatMessage[];
  hasMore: () => boolean;
} {
  if (!mockMessagesStore.has(conversationId)) {
    const generator = generateMessagesForConversation(conversationId, pageSize);
    mockMessagesStore.set(conversationId, generator.next().value!); // première batch
  }

  let currentBatch = 1;
  const generator = generateMessagesForConversation(conversationId, pageSize);

  return {
    getInitialMessages: () => mockMessagesStore.get(conversationId)!,

    loadMore: () => {
      const nextBatch = generator.next().value;
      if (!nextBatch) return [];
      const current = mockMessagesStore.get(conversationId)!;
      mockMessagesStore.set(conversationId, [...nextBatch, ...current]); // prepend pour reverse
      currentBatch++;
      return nextBatch;
    },

    hasMore: () => currentBatch * pageSize < 1000,
  };
}
