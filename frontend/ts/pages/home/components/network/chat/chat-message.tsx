import type { ChatMessageUI } from "@/types/network";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { cn, getAvatarFallback } from "@/lib/utils";
import {
  FileIcon,
  Download,
  MoreVertical,
  Copy,
  Info,
  Trash2,
  Reply,
} from "lucide-react";
import { useMemo } from "react";
import { QuotedMessage } from "./quoted-message";
import { Link } from "@inertiajs/react";

interface ChatMessageProps {
  message: ChatMessageUI;
  onDeleteMessage?: (messageId: string, conversationId: string) => void;
  onSelectMessageChange?: (message: ChatMessageUI | null) => void;
}

export function ChatMessage({
  message,
  onDeleteMessage,
  onSelectMessageChange,
}: ChatMessageProps) {

  // Message système
  if (message.type === "system") {
    return (
      <p className="text-xs text-center text-muted-foreground">
        {message.content}
      </p>
    );
  }

  // Copier le contenu (texte ou lien du média)
  const handleCopy = () => {
    const textToCopy = message.content || message.media || "";
    navigator.clipboard.writeText(textToCopy);
    toast.info("Contenu copié dans le presse-papier");
  };

  // Afficher les détails du message
  const handleDetails = () => {
    toast.info(
      <div className="text-xs space-y-1">
        <p>ID : {message.id}</p>
        <p>Envoyé le : {new Date(message.time).toLocaleString()}</p>
        {message.mediaSize && (
          <p>
            Taille : {(Number(message.mediaSize) / 1024 / 1024).toFixed(2)} Mo
          </p>
        )}
        {message.mediaType && <p>Type : {message.mediaType}</p>}
      </div>,
    );
  };

  // Supprimer le message
  const handleDelete = () => {
    if (onDeleteMessage) {
      onDeleteMessage(message.id, message.conversationId);
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3",
        message.isOwn ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "flex gap-3 max-w-[80%]",
          message.isOwn ? "flex-row-reverse" : "flex-row",
        )}
      >
        {/* Avatar */}
        <Link
          href={message.author_slug ? `/profile/${message.author_slug}` : ""}
        >
          <Avatar className="h-8 w-8 self-end">
            <AvatarImage src={message.avatar} />
            <AvatarFallback className="text-[10px]">
              {getAvatarFallback(message.author)}
            </AvatarFallback>
          </Avatar>
        </Link>

        {/* Contenu du message */}
        <div
          className={cn(
            "flex flex-col",
            message.isOwn ? "items-end" : "items-start",
          )}
        >
          {/* Nom de l'auteur (pour les messages des autres) */}
          {message.author && !message.isOwn && (
            <span className="text-[10px] font-medium mb-1 ml-1 text-muted-foreground">
              {message.author}
            </span>
          )}

          {/* Bulle du message avec menu */}
          <div
            className={cn(
              "rounded-2xl px-4 py-2 shadow-sm group relative",
              message.isOwn
                ? "bg-primary text-primary-foreground rounded-br-none"
                : "bg-muted rounded-bl-none",
            )}
          >
            {/* Contenu et menu en flex row */}

            <div className="flex">
              <div className="flex flex-col items-start justify-between gap-2">
                {message.repliedTo && (
                  <QuotedMessage
                    repliedTo={message.repliedTo}
                    variant="bubble"
                  />
                )}
                <div className="">
                  <div className="flex-1 min-w-0">
                    {message.media && (
                      <MessageMedia
                        media={message.media}
                        mediaType={message.mediaType}
                        mediaSize={message.mediaSize}
                      />
                    )}
                    {message.content && (
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {message.content}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              {/* Menu à trois points (toujours visible discrètement) */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 opacity-50 hover:opacity-100 -mt-1 -mr-2"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                  <DropdownMenuItem
                    onClick={() => onSelectMessageChange?.(message)}
                  >
                    <Reply className="mr-2 h-4 w-4" /> Repondre
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleCopy}>
                    <Copy className="mr-2 h-4 w-4" />
                    Copier
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleDetails}>
                    <Info className="mr-2 h-4 w-4" />
                    Détails
                  </DropdownMenuItem>
                  {message.canDelete && (
                    <DropdownMenuItem
                      onClick={handleDelete}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Supprimer
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Heure et statut */}
          <div className="flex items-center gap-1 mt-1 px-1">
            <span className="text-[9px] opacity-60">
              {new Date(message.time).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {message.isOwn && message.status && (
              <span className="text-[9px] opacity-60">· {message.status}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Sous-composant pour l'affichage du média (inchangé)
interface MessageMediaProps {
  media: string;
  mediaType?: string;
  mediaSize?: number;
}

function MessageMedia({ media, mediaType, mediaSize }: MessageMediaProps) {
  const isImage = mediaType?.startsWith("image/");

  if (isImage) {
    return (
      <img
        src={media}
        alt=""
        className="rounded-lg max-w-full max-h-64 object-contain"
      />
    );
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const fileInfo = useMemo(() => {
    let fileName = "Document";
    if (mediaType) {
      const parts = mediaType.split("/");
      const ext = parts[1] || "";
      fileName = `fichier.${ext}`;
    }
    return fileName;
  }, [mediaType]);

  const handleDownload = () => {
    if (media.startsWith("data:")) {
      const matches = media.match(/^data:([^;]+);base64,(.+)$/);
      if (matches) {
        const mimeType = matches[1];
        const base64Data = matches[2];
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileInfo;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        return;
      }
    }
    const a = document.createElement("a");
    a.href = media;
    a.download = fileInfo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-background/10">
      <FileIcon className="h-8 w-8" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{fileInfo}</p>
        {mediaSize && (
          <p className="text-xs opacity-70">
            {(Number(mediaSize) / 1024 / 1024).toFixed(2)} Mo
          </p>
        )}
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={handleDownload}
        title="Télécharger"
      >
        <Download className="h-4 w-4" />
      </Button>
    </div>
  );
}
