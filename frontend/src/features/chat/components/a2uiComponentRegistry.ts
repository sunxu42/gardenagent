import type { ComponentRegistry } from "a2ui-shadcn";
import { BinaryChoiceButton } from "./BinaryChoiceButton";
import { DatePicker } from "./DatePicker";
import { DataTableColumnHeader } from "./DataTableColumnHeader";
import { DataTableRowOption } from "./DataTableRowOption";
import { EmojiOption } from "./EmojiOption";
import { MultiSelectConfirmButton } from "./MultiSelectConfirmButton";
import { MultiSelectOption } from "./MultiSelectOption";
import { PlanOptionCard } from "./PlanOptionCard";
import { SingleSelectOption } from "./SingleSelectOption";

/** Custom A2UI adapters; must be passed to each A2UISurface instance. */
export const a2uiComponentRegistry: ComponentRegistry = {
  PlanOptionCard,
  MultiSelectOption,
  MultiSelectConfirmButton,
  BinaryChoiceButton,
  DatePicker,
  EmojiOption,
  SingleSelectOption,
  DataTableColumnHeader,
  DataTableRowOption,
};
