import { useState } from "react";
import type { SerializedEditorState } from "lexical";
import { Editor } from "./editor";
import { cn } from "@/lib/utils";

export interface RichTextEditorProps {
  className?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export default function RichTextEditor({
  className,
  onChange,
  placeholder,
}: RichTextEditorProps) {
  const [editorSerializedState, setSerializedEditorState] = useState<SerializedEditorState>();



 
  return (
    <div className={cn(className)}>
      <Editor
        placeholder={placeholder}
        editorSerializedState={editorSerializedState}
        onSerializedChange={setSerializedEditorState}
        onHtmlGenerated={onChange}
      />
    </div>
  );
}
