import { useState } from "react";
import {
  CHECK_LIST,
  ELEMENT_TRANSFORMERS,
  MULTILINE_ELEMENT_TRANSFORMERS,
  TEXT_FORMAT_TRANSFORMERS,
  TEXT_MATCH_TRANSFORMERS,
} from "@lexical/markdown";
import { CheckListPlugin } from "@lexical/react/LexicalCheckListPlugin";
import { ClickableLinkPlugin } from "@lexical/react/LexicalClickableLinkPlugin";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { HorizontalRulePlugin } from "@lexical/react/LexicalHorizontalRulePlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { MarkdownShortcutPlugin } from "@lexical/react/LexicalMarkdownShortcutPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { TabIndentationPlugin } from "@lexical/react/LexicalTabIndentationPlugin";
import { TablePlugin } from "@lexical/react/LexicalTablePlugin";

import { ContentEditable } from "@/components/rich-text-editor/editor/editor-ui/content-editable";
import { AutoLinkPlugin } from "@/components/rich-text-editor/editor/plugins/auto-link-plugin";
import { CodeActionMenuPlugin } from "@/components/rich-text-editor/editor/plugins/code-action-menu-plugin";
import { CodeHighlightPlugin } from "@/components/rich-text-editor/editor/plugins/code-highlight-plugin";
import { ComponentPickerMenuPlugin } from "@/components/rich-text-editor/editor/plugins/component-picker-menu-plugin";
import { DraggableBlockPlugin } from "@/components/rich-text-editor/editor/plugins/draggable-block-plugin";
import { FloatingLinkEditorPlugin } from "@/components/rich-text-editor/editor/plugins/floating-link-editor-plugin";
import { FloatingTextFormatToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/floating-text-format-plugin";
import { ImagesPlugin } from "@/components/rich-text-editor/editor/plugins/images-plugin";
import { LinkPlugin } from "@/components/rich-text-editor/editor/plugins/link-plugin";
import { ListMaxIndentLevelPlugin } from "@/components/rich-text-editor/editor/plugins/list-max-indent-level-plugin";
import { AlignmentPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/alignment-picker-plugin";
import { BulletedListPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/bulleted-list-picker-plugin";
import { CheckListPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/check-list-picker-plugin";
import { CodePickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/code-picker-plugin";
import { DividerPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/divider-picker-plugin";
import { HeadingPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/heading-picker-plugin";
import { ImagePickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/image-picker-plugin";
import { NumberedListPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/numbered-list-picker-plugin";
import { ParagraphPickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/paragraph-picker-plugin";
import { QuotePickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/quote-picker-plugin";
import { TablePickerPlugin } from "@/components/rich-text-editor/editor/plugins/picker/table-picker-plugin";
import { BlockFormatDropDown } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format-toolbar-plugin";
import { FormatBulletedList } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-bulleted-list";
import { FormatCheckList } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-check-list";
import { FormatCodeBlock } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-code-block";
import { FormatHeading } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-heading";
import { FormatNumberedList } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-numbered-list";
import { FormatParagraph } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-paragraph";
import { FormatQuote } from "@/components/rich-text-editor/editor/plugins/toolbar/block-format/format-quote";
import { CodeLanguageToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/code-language-toolbar-plugin";
import { ElementFormatToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/element-format-toolbar-plugin";
import { FontFormatToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/font-format-toolbar-plugin";
import { HistoryToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/history-toolbar-plugin";
import { HorizontalRuleToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/horizontal-rule-toolbar-plugin";
import { ImageToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/image-toolbar-plugin";
import { LinkToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/link-toolbar-plugin";
import { TableToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/table-toolbar-plugin";
import { ToolbarPlugin } from "@/components/rich-text-editor/editor/plugins/toolbar/toolbar-plugin";
import { HR } from "@/components/rich-text-editor/editor/transformers/markdown-hr-transformer";
import { IMAGE } from "@/components/rich-text-editor/editor/transformers/markdown-image-transformer";
import { TABLE } from "@/components/rich-text-editor/editor/transformers/markdown-table-transformer";
import HTMLGeneratorPlugin from "@/components/rich-text-editor/editor/plugins/html-generator-plugin";
import { ActionsPlugin } from "../editor/plugins/actions/actions-plugin";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Radio } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";

export interface PluginsProps {
  placeholder?: string;
  onHtmlGenerated?: (html: string) => void;
  onSubmit?: () => void;
  onCancel?: () => void;
  canSubmit?: boolean;
  isLoading?: boolean;
}

export function Plugins({
  placeholder,
  onHtmlGenerated,
  onSubmit,
  onCancel,
  canSubmit,
  isLoading,
}: PluginsProps) {
  const [floatingAnchorElem, setFloatingAnchorElem] =
    useState<HTMLDivElement | null>(null);
  const [isLinkEditMode, setIsLinkEditMode] = useState<boolean>(false);

  const onRef = (_floatingAnchorElem: HTMLDivElement) => {
    if (_floatingAnchorElem !== null) {
      setFloatingAnchorElem(_floatingAnchorElem);
    }
  };

  return (
    <div className="relative">
      <HTMLGeneratorPlugin onHtmlGenerated={onHtmlGenerated ?? (() => {})} />
      <ToolbarPlugin>
        {({ blockType }) => (
          <div className="flex flex-col sticky top-0 z-10  gap-2 overflow-auto border-b p-1">
            <div className="flex gap-2">
              <HistoryToolbarPlugin />
              <BlockFormatDropDown>
                <FormatParagraph />
                <FormatHeading levels={["h1", "h2", "h3"]} />
                <FormatNumberedList />
                <FormatBulletedList />
                <FormatCheckList />
                <FormatCodeBlock />
                <FormatQuote />
              </BlockFormatDropDown>
              {blockType === "code" ? (
                <CodeLanguageToolbarPlugin />
              ) : (
                <div className="flex flex-col">
                  <div className="flex gap-2">
                    <ElementFormatToolbarPlugin separator={false} />
                    <FontFormatToolbarPlugin />
                  </div>
                  <div className="flex gap-2">
                    <LinkToolbarPlugin setIsLinkEditMode={setIsLinkEditMode} />
                    <HorizontalRuleToolbarPlugin />
                    <ImageToolbarPlugin />
                    <TableToolbarPlugin />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </ToolbarPlugin>
      <div className="relative">
        <RichTextPlugin
          contentEditable={
            <div className="">
              <div className="" ref={onRef}>
                <ContentEditable
                  placeholder={
                    placeholder ?? "Appuyez sur / pour les commandes..."
                  }
                  className="ContentEditable__root relative block min-h-72 overflow-auto px-8 py-4 focus:outline-none"
                />
              </div>
            </div>
          }
          ErrorBoundary={LexicalErrorBoundary}
        />
        <HistoryPlugin />

        <ListPlugin />
        <ListMaxIndentLevelPlugin />
        <CheckListPlugin />

        <TabIndentationPlugin />

        <ClickableLinkPlugin />
        <AutoLinkPlugin />
        <LinkPlugin />

        <FloatingLinkEditorPlugin
          anchorElem={floatingAnchorElem}
          isLinkEditMode={isLinkEditMode}
          setIsLinkEditMode={setIsLinkEditMode}
        />

        <CodeActionMenuPlugin anchorElem={floatingAnchorElem} />
        <CodeHighlightPlugin />

        <ComponentPickerMenuPlugin
          baseOptions={[
            ParagraphPickerPlugin(),
            HeadingPickerPlugin({ n: 1 }),
            HeadingPickerPlugin({ n: 2 }),
            HeadingPickerPlugin({ n: 3 }),
            TablePickerPlugin(),
            CheckListPickerPlugin(),
            NumberedListPickerPlugin(),
            BulletedListPickerPlugin(),
            QuotePickerPlugin(),
            CodePickerPlugin(),
            DividerPickerPlugin(),
            ImagePickerPlugin(),
            AlignmentPickerPlugin({ alignment: "left" }),
            AlignmentPickerPlugin({ alignment: "center" }),
            AlignmentPickerPlugin({ alignment: "right" }),
            AlignmentPickerPlugin({ alignment: "justify" }),
          ]}
        />
        <Separator />
        <ActionsPlugin>
          <div className="p-2 flex justify-between">
            <Button onClick={onCancel} variant={"outline"}>
              Annuler
            </Button>

            <Button
              disabled={!canSubmit}
              variant={"default"}
              onClick={onSubmit}
            >
              Publier
              {isLoading ? <Spinner /> : <Radio />}
            </Button>
          </div>
        </ActionsPlugin>
        <FloatingTextFormatToolbarPlugin
          anchorElem={floatingAnchorElem}
          setIsLinkEditMode={setIsLinkEditMode}
        />

        <HorizontalRulePlugin />

        <ImagesPlugin />

        <TablePlugin />

        <DraggableBlockPlugin anchorElem={floatingAnchorElem} />

        <MarkdownShortcutPlugin
          transformers={[
            TABLE,
            HR,
            IMAGE,
            CHECK_LIST,
            ...ELEMENT_TRANSFORMERS,
            ...MULTILINE_ELEMENT_TRANSFORMERS,
            ...TEXT_FORMAT_TRANSFORMERS,
            ...TEXT_MATCH_TRANSFORMERS,
          ]}
        />
      </div>
    </div>
  );
}
