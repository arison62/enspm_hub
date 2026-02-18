import React, { useState } from "react";
import { Smile, Paperclip, Send, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface Message {
  text: string | null;
  media: string | null;
}

interface ChatInputProps {
  onSendMessage: (message: Message) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
  const [text, setText] = useState("");
  const [mediaBase64, setMediaBase64] = useState<string | null>(null);

  const handleSend = () => {
    if (text.trim() || mediaBase64) {
      onSendMessage({ text, media: mediaBase64 });
      setText("");
      setMediaBase64(null);
    }
  };

  return (
    <div className="p-4 border-t bg-background">
      <div className="flex items-center gap-2 max-w-6xl mx-auto">
        <Button variant="ghost" size="icon" className="shrink-0">
          <Smile className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="shrink-0">
          <Paperclip className="h-5 w-5" />
        </Button>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Écrivez votre message..."
          className="flex-1 bg-secondary/50 border-none focus-visible:ring-1"
        />
        {text.trim() ? (
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
