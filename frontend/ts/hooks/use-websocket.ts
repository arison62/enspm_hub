// frontend/ts/hooks/use-websocket.ts

import { useEffect } from "react";
import {
  useWebSocketStore,
  type MessageType,
} from "@/stores/websocketStore";

export const useWebSocket = () => {
  const store = useWebSocketStore();

  return {
    // État
    status: store.status,
    isConnected: store.status === "connected",
    error: store.error,

    // Actions
    connect: store.connect,
    disconnect: store.disconnect,
    send: store.send,
    joinRoom: store.joinRoom,
    initDM: store.initDM,
  };
};

/**
 * Hook pour s'abonner à un type de message spécifique
 */
export const useWebSocketMessage = (
  type: MessageType,
  handler: (data: any) => void,
  deps: React.DependencyList = [],
) => {
  const subscribe = useWebSocketStore((state) => state.subscribe);

  useEffect(() => {
    const unsubscribe = subscribe(type, handler);
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, subscribe, ...deps]);
};

/**
 * Hook pour rejoindre automatiquement une room
 */
export const useWebSocketRoom = (
  roomType: "groupe" | "conv",
  roomId: string | null,
  enabled: boolean = true,
) => {
  const { joinRoom, isConnected } = useWebSocket();

  useEffect(() => {
    if (enabled && isConnected && roomId) {
      console.log(`[WebSocket] Joining room: ${roomType}_${roomId}`);
      joinRoom(roomType, roomId);
    }
  }, [enabled, isConnected, roomType, roomId, joinRoom]);
};