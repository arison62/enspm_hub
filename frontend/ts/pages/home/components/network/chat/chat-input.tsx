import React, { useState } from "react";
import { Smile, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type {RepliedToMessage } from "@/types/network";
import { QuotedMessage } from "./quoted-message";
import { FileInput } from "./file-input";

interface Message {
  text: string | null;
  media: string | null;
  mediaName?: string | null;
  mediaType?: string | null;
  mediaSize?: number | null;
  repliedToId?: string;
}

interface ChatInputProps {
  selectedReference: RepliedToMessage | null;
  onSendMessage: (message: Message) => void;
  onSelectedReferenceChange?: (message: RepliedToMessage | null) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  selectedReference,
  onSelectedReferenceChange,
}) => {
  const [text, setText] = useState("");
  const [mediaBase64, setMediaBase64] = useState<string | null>(null);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleSend = () => {
    if (text.trim() || mediaBase64) {
      onSendMessage({
        text,
        media: mediaBase64,
        mediaName: mediaFile?.name || null,
        mediaType: mediaFile?.type || null,
        mediaSize: mediaFile?.size || null,
        repliedToId: selectedReference?.id,
      });

      // Reset
      setText("");
      setMediaBase64(null);
      setMediaFile(null);
      setUploadError(null);
      onSelectedReferenceChange?.(null);
      handleFileDelete();
    }
  };

  const handleFileLoaded = (base64: string, file: File) => {
    setMediaBase64(base64);
    setMediaFile(file);
    setUploadError(null);
  };

  const handleFileError = (error: string) => {
    setUploadError(error);
  };

  const handleFileDelete = () => {
    setMediaBase64(null);
    setMediaFile(null);
    setUploadError(null);
    console.log("File deleted");
  };

  const hasContent = text.trim() || mediaBase64;

  return (
    <FileInput
      onError={handleFileError}
      onFileLoaded={handleFileLoaded}
      onProgress={() => {}}
      onCancel={() => {}}
      onDelete={handleFileDelete}
      hasFile={!!mediaBase64}
      previewBase64={mediaBase64}
      previewFile={mediaFile}
    >
      <div className="p-4 border-t bg-background">
        {/* Message de réponse */}
        {selectedReference && (
          <QuotedMessage
            repliedTo={{
              id: selectedReference.id,
              type: selectedReference.type,
              author: selectedReference.author,
              content: selectedReference.content,
              title: selectedReference.title,
              media: selectedReference.media,
              mediaType: selectedReference.mediaType,
            }}
            variant="input"
            onCancel={() => onSelectedReferenceChange?.(null)}
          />
        )}

        {/* Erreur upload */}
        {uploadError && (
          <div className="mb-3 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {uploadError}
          </div>
        )}

        {/* Prévisualisation fichier - UNE SEULE FOIS ICI */}
        <div className="mb-3 max-w-6xl mx-auto">
          <FileInput.Preview />
        </div>

        <div className="flex items-end gap-2 max-w-6xl mx-auto">
          <Button variant="ghost" size="icon" className="shrink-0">
            <Smile className="h-5 w-5" />
          </Button>

          {/* Trigger - UNE SEULE FOIS ICI */}
          <FileInput.Trigger />

          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" &&
              !e.shiftKey &&
              (e.preventDefault(), handleSend())
            }
            placeholder={
              mediaBase64 ? "Ajoutez un message..." : "Écrivez votre message..."
            }
            className="flex-1 bg-secondary/50 border-none focus-visible:ring-1 min-h-[42px] resize-none"
            rows={1}
          />

          {hasContent && (
            <Button onClick={handleSend} size="icon" className="shrink-0">
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    </FileInput>
  );
};
