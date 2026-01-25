"use client"

import {
  type InitialConfigType,
  LexicalComposer,
} from "@lexical/react/LexicalComposer"
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin"
import type { EditorState, SerializedEditorState } from "lexical"

import { editorTheme } from "@/components/rich-text-editor/editor/themes/editor-theme"
import { TooltipProvider } from "@/components/ui/tooltip"

import { nodes } from "./nodes"
import { Plugins } from "./plugins"

const editorConfig: InitialConfigType = {
  namespace: "Editor",
  theme: editorTheme,
  nodes,
  onError: (error: Error) => {
    console.error(error)
  },
}

export function Editor({
  editorState,
  placeholder,
  editorSerializedState,
  onChange,
  onSerializedChange,
  onHtmlGenerated,
  onSubmit,
  onCancel,
  canSubmit,
  isLoading,
}: {
  editorState?: EditorState;
  placeholder?: string;
  editorSerializedState?: SerializedEditorState;
  onChange?: (editorState: EditorState) => void;
  onHtmlGenerated?: (html: string) => void;
  onSerializedChange?: (editorSerializedState: SerializedEditorState) => void;
  onSubmit?: () => void;
  onCancel?: () => void;
  canSubmit?: boolean;
  isLoading?: boolean;
}) {
  return (
    <div className="bg-background overflow-hidden rounded-lg border shadow">
      <LexicalComposer
        initialConfig={{
          ...editorConfig,
          ...(editorState ? { editorState } : {}),
          ...(editorSerializedState
            ? { editorState: JSON.stringify(editorSerializedState) }
            : {}),
        }}
      >
        <TooltipProvider>
          <Plugins
            placeholder={placeholder}
            onHtmlGenerated={onHtmlGenerated}
            onSubmit={onSubmit}
            onCancel={onCancel}
            canSubmit={canSubmit}
            isLoading={isLoading}
          />

          <OnChangePlugin
            ignoreSelectionChange={true}
            onChange={(editorState) => {
              onChange?.(editorState);
              onSerializedChange?.(editorState.toJSON());
            }}
          />
        </TooltipProvider>
      </LexicalComposer>
    </div>
  );
}
