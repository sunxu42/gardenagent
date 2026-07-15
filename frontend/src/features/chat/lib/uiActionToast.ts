import { toast } from "sonner"

/** Bottom-centered action feedback toast (replaces legacy UiActionToast). */
export function showUiActionToast(message: string): void {
  toast(message)
}
