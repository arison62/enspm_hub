import { TableIcon } from "lucide-react"

import { useToolbarContext } from "@/components/rich-text-editor/editor/context/toolbar-context"
import { InsertTableDialog } from "@/components/rich-text-editor/editor/plugins/table-plugin"
import { Button } from "@/components/ui/button"

export function TableToolbarPlugin() {
  const { activeEditor, showModal } = useToolbarContext()

  return (
    <Button
      onClick={() =>
        showModal("Insert Table", (onClose) => (
          <InsertTableDialog activeEditor={activeEditor} onClose={onClose} />
        ))
      }
      size={"icon-sm"}
      variant={"outline"}
      type="button"
      className=""
    >
      <TableIcon className="size-4" />
    </Button>
  )
}
