import React, { useState } from "react";
import { Smile, Paperclip, Send, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { ChatMessageUI } from "@/types/network";

import { QuotedMessage } from "./quoted-message";

interface Message {
  text: string | null;
  media: string | null;
  repliedToId?: string; // ← nouveau
}

interface ChatInputProps {
  selectedMessage: ChatMessageUI | null;
  onSendMessage: (message: Message) => void;
  onSelectedMessageChange?: (message: ChatMessageUI | null) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  selectedMessage,
  onSelectedMessageChange,
}) => {
  const [text, setText] = useState("");
  const [mediaBase64, setMediaBase64] = useState<string | null>(null);

  const handleSend = () => {
    if (text.trim() || mediaBase64) {
      onSendMessage({
        text,
        media: mediaBase64,
        repliedToId: selectedMessage?.id,
      });
      setText("");
      setMediaBase64(null);
      onSelectedMessageChange?.(null); // ← ferme automatiquement après envoi
    }
  };

  return (
    <div className="p-4 border-t bg-background">
     
      {selectedMessage && (
        <QuotedMessage
          repliedTo={{
            id: selectedMessage.id,
            author: selectedMessage.author,
            content: selectedMessage.content,
            media: selectedMessage.media,
            mediaType: selectedMessage.mediaType,
          }}
          variant="input"
          onCancel={() => onSelectedMessageChange?.(null)}
        />
      )}

      <div className="flex items-center gap-2 max-w-6xl mx-auto">
        {/* boutons existants ... */}
        <Button variant="ghost" size="icon" className="shrink-0">
          <Smile className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="shrink-0">
          <Paperclip className="h-5 w-5" />
        </Button>

        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) =>
            e.key === "Enter" &&
            !e.shiftKey &&
            (e.preventDefault(), handleSend())
          }
          placeholder="Écrivez votre message..."
          className="flex-1 bg-secondary/50 border-none focus-visible:ring-1 min-h-[42px]"
        />

        {text.trim() || mediaBase64 ? (
          <Button onClick={handleSend} size="icon" className="shrink-0">
            <Send className="h-5 w-5" />
          </Button>
        ) : (
          <Button variant="ghost" size="icon" className="shrink-0">
            <Mic className="h-5 w-5" />
          </Button>
        )}
      </div>
    </div>
  );
};