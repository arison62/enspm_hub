import { useWebSocket } from "@/hooks/use-websocket";
import { cn } from "@/lib/utils";
import { WifiOff, Loader2 } from "lucide-react";

export const WebSocketStatus = () => {
  const { status, error } = useWebSocket();

  if (status === "connected") return null; // Ne rien afficher si connecté

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium shadow-lg",
        status === "connecting" && "bg-yellow-500 text-white",
        status === "disconnected" && "bg-gray-500 text-white",
        status === "error" && "bg-red-500 text-white",
      )}
    >
      {status === "connecting" && (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Connexion...</span>
        </>
      )}
      {status === "disconnected" && (
        <>
          <WifiOff className="h-4 w-4" />
          <span>Déconnecté</span>
        </>
      )}
      {status === "error" && (
        <>
          <WifiOff className="h-4 w-4" />
          <span>{error || "Erreur de connexion"}</span>
        </>
      )}
    </div>
  );
};
