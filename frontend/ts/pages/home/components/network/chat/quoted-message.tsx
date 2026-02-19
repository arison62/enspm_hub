import { X, FileIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type RepliedMessageData = {
  id: string;
  author?: string;
  content?: string;
  media?: string;
  mediaType?: string;
};

interface QuotedMessageProps {
  repliedTo: RepliedMessageData | null | undefined;
  onCancel?: () => void;
  variant?: "input" | "bubble";
  className?: string;
}

export function QuotedMessage({
  repliedTo,
  onCancel,
  variant = "bubble",
  className,
}: QuotedMessageProps) {
  if (!repliedTo) return null;

  const isInput = variant === "input";
  const isImage = repliedTo.mediaType?.startsWith("image/") || false;
  const hasMedia = !!repliedTo.media && !repliedTo.content; // si pas de texte → on montre le média en priorité

  const displayText =
    repliedTo.content?.trim() ||
    (hasMedia ? (isImage ? "📷 Photo" : "📄 Document") : "");

  return (
    <div
      className={cn(
        "relative flex w-full rounded-lg overflow-hidden border",
        isInput
          ? "bg-muted/80 border-border p-3 mb-3"
          : "border-l-4 border-primary/60 bg-muted/30 pl-3 pr-3 py-2 mb-3",
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        {/* Nom de l’auteur */}
        {repliedTo.author && (
          <p className="text-xs font-semibold text-primary mb-1 tracking-tight">
            {repliedTo.author}
          </p>
        )}

        {/* Texte (flouté dans la preview input) */}
        <p
          className={cn(
            "text-sm break-words pr-6",
            isInput ? "line-clamp-3" : "line-clamp-2",
          )}
        >
          {displayText}
        </p>

        {/* Miniature média (si présent) */}
        {hasMedia && isImage && repliedTo.media && (
          <img
            src={repliedTo.media}
            alt=""
            className="mt-2 max-h-20 max-w-[140px] rounded object-cover border border-border/50"
          />
        )}

        {hasMedia && !isImage && (
          <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
            <FileIcon className="h-4 w-4" />
            Document
          </div>
        )}
      </div>

      {/* Bouton fermer uniquement dans l’input */}
      {isInput && onCancel && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-2 top-2 h-7 w-7 rounded-full hover:bg-background/80"
          onClick={onCancel}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
