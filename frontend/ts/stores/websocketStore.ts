/* eslint-disable @typescript-eslint/no-explicit-any */
//frontend/ts/stores/webSocketStore.ts
import { create } from "zustand";
import { devtools } from "zustand/middleware";

export type WebSocketStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

export type MessageType =
  | "dm.init_notification"
  | "chat.message"
  | "dm.init_success";

export interface WebSocketMessage {
  type: MessageType;
  [key: string]: any;
}

interface WebSocketState {
  // État de la connexion
  socket: WebSocket | null;
  status: WebSocketStatus;
  error: string | null;
  reconnectAttempts: number;

  // Gestionnaires d'événements
  messageHandlers: Map<MessageType, Set<(data: any) => void>>;

  // Actions
  connect: (token?: string) => void;
  disconnect: () => void;
  send: (data: any) => void;
  subscribe: (type: MessageType, handler: (data: any) => void) => () => void;
  joinRoom: (roomType: "groupe" | "conv", roomId: string) => void;
  initDM: (destinataireId: string) => void;

  // Internal
  setSocket: (socket: WebSocket | null) => void;
  setStatus: (status: WebSocketStatus) => void;
  setError: (error: string | null) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

export const useWebSocketStore = create<WebSocketState>()(
  devtools(
    (set, get) => ({
      socket: null,
      status: "disconnected",
      error: null,
      reconnectAttempts: 0,
      messageHandlers: new Map(),

      connect: (token?: string) => {
        const state = get();
        console.log("[WebSocket] Connecting...");
        // Éviter les connexions multiples
        if (
          state.socket?.readyState === WebSocket.OPEN ||
          state.socket?.readyState === WebSocket.CONNECTING
        ) {
          console.log("[WebSocket] Already connected or connecting");
          return;
        }

        set({ status: "connecting", error: null });

        try {
          // Déterminer le protocole (ws ou wss)
          const protocol =
            window.location.protocol === "https:" ? "wss:" : "ws:";
          const host = window.location.host;

          // Construction de l'URL avec token si disponible
          let wsUrl = `${protocol}//${host}/ws/chat/`;
          if (token) {
            wsUrl += `?token=${token}`;
          }

          const ws = new WebSocket(wsUrl);

          ws.onopen = () => {
            console.log("[WebSocket] Connected");
            set({
              status: "connected",
              error: null,
              socket: ws,
            });
            get().resetReconnectAttempts();
          };

          ws.onmessage = (event) => {
            try {
              console.log("[WebSocket] Event:", event);
              const message: WebSocketMessage = JSON.parse(event.data);
              console.log("[WebSocket] Message received:", message);

              // Dispatcher le message aux handlers enregistrés
              const handlers = get().messageHandlers.get(message.type);
              
              if (handlers) {
                handlers.forEach((handler) => {
                  try {
                    
                    handler(message);
                  } catch (error) {
                    console.error("[WebSocket] Handler error:", error);
                  }
                });
              }
            } catch (error) {
              console.error("[WebSocket] Failed to parse message:", error);
            }
          };

          ws.onerror = (error) => {
            console.error("[WebSocket] Error:", error);
            set({
              status: "error",
              error: "Erreur de connexion WebSocket",
            });
          };

          ws.onclose = (event) => {
            console.log("[WebSocket] Disconnected", event);
            set({
              status: "disconnected",
              socket: null,
            });

            // Tentative de reconnexion
            const attempts = get().reconnectAttempts;
            if (attempts < MAX_RECONNECT_ATTEMPTS) {
              console.log(
                `[WebSocket] Reconnecting... (${attempts + 1}/${MAX_RECONNECT_ATTEMPTS})`,
              );
              get().incrementReconnectAttempts();

              setTimeout(() => {
                get().connect(token);
              }, RECONNECT_DELAY);
            } else {
              set({
                error: "Impossible de se reconnecter au serveur",
              });
            }
          };

          set({ socket: ws });
        } catch (error) {
          console.error("[WebSocket] Connection failed:", error);
          set({
            status: "error",
            error: "Impossible de se connecter au serveur",
            socket: null,
          });
        }
      },

      disconnect: () => {
        const { socket } = get();
        if (socket) {
          console.log("[WebSocket] Disconnecting...");
          socket.close(1000, "User disconnected");
          set({
            socket: null,
            status: "disconnected",
            error: null,
          });
        }
      },

      send: (data: any) => {
        const { socket, status } = get();
        if (socket && status === "connected") {
          socket.send(JSON.stringify(data));
        } else {
          console.warn("[WebSocket] Cannot send message: not connected");
        }
      },

      subscribe: (type: MessageType, handler: (data: any) => void) => {
        const { messageHandlers } = get();

        if (!messageHandlers.has(type)) {
          messageHandlers.set(type, new Set());
        }

        messageHandlers.get(type)!.add(handler);
        // Retourner une fonction de cleanup
        return () => {
          const handlers = get().messageHandlers.get(type);
          if (handlers) {
            handlers.delete(handler);
            if (handlers.size === 0) {
              get().messageHandlers.delete(type);
            }
          }
        };
      },

      joinRoom: (roomType: "groupe" | "conv", roomId: string) => {
        get().send({
          type: "room.join",
          room_type: roomType,
          room_id: roomId,
        });
      },

      initDM: (destinataireId: string) => {
        get().send({
          type: "dm.init",
          destinataire_id: destinataireId,
        });
      },

      // Internal methods
      setSocket: (socket) => set({ socket }),
      setStatus: (status) => set({ status }),
      setError: (error) => set({ error }),
      incrementReconnectAttempts: () =>
        set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),
      resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
    }),
    { name: "WebSocket Store" },
  ),
);