import { SearchIcon, Tag } from "lucide-react";
import * as React from "react";
import { useEffect, useMemo, useState } from "react";

import {
  Combobox,
  ComboboxChip,
  ComboboxChips,
  ComboboxCollection,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxGroupLabel,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxPopup,
  ComboboxSeparator,
  ComboboxValue,
} from "@/components/ui/combobox";


interface SearchFieldProps {
  selectedItems: { label: string; value: string }[];
  onItemsChange: (items: { label: string; value: string }[]) => void;
  items: { label: string; value: string }[];
}


export default function SearchField({
  selectedItems,
  onItemsChange,
  items,
}: SearchFieldProps) {
  const [open, setOpen] = useState(selectedItems.length === 0);

  // Keep popup open when no selection is made
  useEffect(() => {
    if (selectedItems.length === 0) {
      setOpen(true);
    }
  }, [selectedItems.length]);

  const groupedItems = useMemo(() => {
    const selectedValues = selectedItems.map((item) => item.value);

    // Separate items into enabled and disabled
    const selected: typeof items = [];
    const unselected: typeof items = [];

    items.forEach((item) => {
      const isSelected = selectedValues.includes(item.value);
      if (isSelected) {
        selected.push(item);
      } else {
        unselected.push(item);
      }
    });

    // Sort enabled items: selected first, then available, then by custom order
    const sortedEnabled = [...selected].sort((a, b) => {
      const aSelected = selectedValues.includes(a.value);
      const bSelected = selectedValues.includes(b.value);

      // Selected items first
      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      // Then sort by custom category order
    
      return a.value.localeCompare(b.value);
    });

    // Sort disabled items by custom category order
    const sortedDisabled = [...unselected].sort((a, b) => {
      
      return a.value.localeCompare(b.value);
    });

    // Return groups similar to the grouped example
    const groups: Array<{ type: "unselected" | "selected"; items: typeof items }> =
      [];

    if (sortedEnabled.length > 0) {
      groups.push({ items: sortedEnabled, type: "selected" });
    }

    if (sortedDisabled.length > 0) {
      groups.push({ items: sortedDisabled, type: "unselected" });
    }

    return groups;
  }, [selectedItems, items]);

  const handleValueChange = (newItems: { label: string; value: string }[]) => {
    onItemsChange(newItems);
    setOpen(false);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Combobox
        aria-label="Selectionner des filtres"
        autoHighlight
        items={groupedItems}
        multiple
        onOpenChange={setOpen}
        onValueChange={handleValueChange}
        open={open}
        value={selectedItems}
      >
        <ComboboxChips
          className="**:data-[slot=combobox-start-addon]:[&_svg]:-me-0.5 rounded-xl p-[calc(--spacing(2)-1px)] before:rounded-xl"
          startAddon={
            <SearchIcon />
          }
        >
          <ComboboxValue>
            {(value: { value: string; label: string }[]) => (
              <>
                {value?.map((item) => (
                  <ComboboxChip aria-label={item.label} key={item.value}>
                    <div className="flex items-center gap-1.5">
                      <Tag />
                      <span>{item.label}</span>
                    </div>
                  </ComboboxChip>
                ))}
                <ComboboxInput
                  aria-label="Rechercher"
                  size="lg"
                />
              </>
            )}
          </ComboboxValue>
        </ComboboxChips>
        <ComboboxPopup>
          <ComboboxEmpty>No filters found.</ComboboxEmpty>
          <ComboboxList>
            {(group: (typeof groupedItems)[number]) => (
              <React.Fragment key={group.type}>
                {group.type === "unselected" && (
                  <ComboboxSeparator className="my-2" />
                )}
                <ComboboxGroup items={group.items}>
                  <ComboboxGroupLabel>
                    {group.type === "selected"
                      ? "Selectionés"
                      : "Non selectionés"}
                  </ComboboxGroupLabel>
                  <ComboboxCollection>
                    {(item: (typeof group.items)[number]) => (
                      <ComboboxItem
                        disabled={group.type === "selected"}
                        key={item.value}
                        value={item}
                      >
                        <div className="flex items-center gap-2">
                          <Tag />
                          <span>{item.label}</span>
                        </div>
                      </ComboboxItem>
                    )}
                  </ComboboxCollection>
                </ComboboxGroup>
              </React.Fragment>
            )}
          </ComboboxList>
        </ComboboxPopup>
      </Combobox>
    </div>
  );
}
