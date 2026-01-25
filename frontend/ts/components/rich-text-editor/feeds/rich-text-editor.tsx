import { useState } from "react";
import type { SerializedEditorState } from "lexical";
import { Editor } from "./editor";
import { cn } from "@/lib/utils";


export interface RichTextEditorProps {
  className?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: () => void;
  onCancel?: () => void;
  canSubmit?: boolean;
  isLoading?: boolean;
}

export default function RichTextEditor({
  className,
  onChange,
  placeholder,
  canSubmit,
  onSubmit,
  onCancel,
  isLoading
}: RichTextEditorProps) {
  const [editorSerializedState, setSerializedEditorState] =
    useState<SerializedEditorState>();

  return (
    <div className={cn(className)}>
      <Editor
        placeholder={placeholder}
        editorSerializedState={editorSerializedState}
        onSerializedChange={setSerializedEditorState}
        onHtmlGenerated={onChange}
        canSubmit={canSubmit}
        onSubmit={onSubmit}
        onCancel={onCancel}
        isLoading={isLoading}
      />
    </div>
  );
}
