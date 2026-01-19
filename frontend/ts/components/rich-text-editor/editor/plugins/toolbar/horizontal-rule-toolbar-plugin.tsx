import { INSERT_HORIZONTAL_RULE_COMMAND } from "@lexical/react/LexicalHorizontalRuleNode"
import { ScissorsIcon } from "lucide-react"

import { useToolbarContext } from "@/components/rich-text-editor/editor/context/toolbar-context"
import { Button } from "@/components/ui/button"

export function HorizontalRuleToolbarPlugin() {
  const { activeEditor } = useToolbarContext()

  return (
    <Button
      onClick={() =>
        activeEditor.dispatchCommand(INSERT_HORIZONTAL_RULE_COMMAND, undefined)
      }
      size={"icon-sm"}
      variant={"outline"}
      className=""
      type="button"
    >
      <ScissorsIcon className="size-4" />
    </Button>
  )
}
