"use client"

import { ImageIcon } from "lucide-react"

import { useToolbarContext } from "@/components/rich-text-editor/editor/context/toolbar-context"
import { InsertImageDialog } from "@/components/rich-text-editor/editor/plugins/images-plugin"
import { Button } from "@/components/ui/button"

export function ImageToolbarPlugin() {
  const { activeEditor, showModal } = useToolbarContext()

  return (
    <Button
      onClick={() => {
        showModal("Insert Image", (onClose) => (
          <InsertImageDialog activeEditor={activeEditor} onClose={onClose} />
        ))
      }}
      variant={"outline"}
      size={"icon-sm"}
      type="button"
    >
      <ImageIcon className="size-4" />
    </Button>
  )
}
