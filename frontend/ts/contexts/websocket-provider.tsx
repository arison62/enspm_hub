// frontend/ts/contexts/websocket-provider.tsx

import { useEffect } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocketMessage } from "@/hooks/use-websocket";
import { useAuth } from "@/hooks/use-auth";

export const WebSocketProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { connect, disconnect, status, error } = useWebSocket();
  const { profil, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();


useEffect(() => {
  if (isAuthenticated) {
    connect();
  }

  return () => {
    disconnect();
  };
}, [profil, connect, disconnect, isAuthenticated]);

  useWebSocketMessage("chat.message", (data) => {
    console.log("[WebSocket] Chat message received: ", data);
    if (data.room_type === "groupe") {
      queryClient.invalidateQueries({
        queryKey: ["groupMessages", data.room_id],
      });
    } else if (data.room_type === "conv") {
      queryClient.invalidateQueries({
        queryKey: ["conversationMessages", data.room_id],
      });

      queryClient.invalidateQueries({
        queryKey: ["recentConversations", data.destinataire_id],
      });
    }
  });

  useWebSocketMessage("dm.init_notification", (data) => {
    console.log("[WebSocket] DM notification received: ", data);
    queryClient.invalidateQueries({
      queryKey: ["recentConversations", data.destinataire_id],
    });
  });

  useWebSocketMessage("dm.init_success", (data) => {
    console.log("[WebSocket] DM initialized: ", data);
  });
  useEffect(() => {
    if (error) {
      console.error("[WebSocket] Error: ", error);
    }
  });
  useEffect(() => {
    if (status === "connected") {
      console.log("[WebSocket] Connected to server");
    } else if (status === "connecting") {
      console.log("[WebSocket] Connecting...");
    } else if (status === "disconnected") {
      console.log("[WebSocket]  Disconnected");
    }
  }, [status]);
  return <>{children}</>;
};
