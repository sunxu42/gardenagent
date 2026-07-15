import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { AppearanceMode } from "../types";
import "./settings-ios.css";

interface ClearUserDataDialogProps {
  open: boolean;
  busy: boolean;
  error: string | null;
  appearance: AppearanceMode;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function ClearUserDataDialog({
  open,
  busy,
  error,
  appearance,
  onOpenChange,
  onConfirm,
}: ClearUserDataDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent
        data-appearance={appearance}
        className="ios-settings-root ios-settings-alert fixed left-1/2 top-1/2 z-[60] w-[min(92vw,24rem)] -translate-x-1/2 -translate-y-1/2 gap-0 border-0 bg-transparent p-0 shadow-none outline-none sm:rounded-none"
        overlayClassName="ios-settings-root ios-settings-alert-overlay"
      >
        <AlertDialogTitle className="ios-settings-alert__title">清空用户数据？</AlertDialogTitle>
        <AlertDialogDescription id="clear-user-data-desc" className="ios-settings-alert__desc">
          将永久删除本机对话、个人设置、本地数据库历史，以及服务端的检查点与向量记忆，并生成新用户身份后刷新页面。此操作不可恢复。
        </AlertDialogDescription>
        {error ? <p className="mt-3 text-sm text-[var(--apple-red)]">{error}</p> : null}
        <div className="ios-settings-alert__actions">
          <AlertDialogCancel
            disabled={busy}
            className="ios-settings-alert__btn ios-settings-alert__btn--cancel mt-0 h-auto border-0 bg-transparent p-0 shadow-none hover:bg-transparent"
          >
            取消
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={busy}
            onClick={onConfirm}
            className="ios-settings-alert__btn ios-settings-alert__btn--destructive h-auto border-0 bg-transparent p-0 shadow-none hover:bg-transparent"
          >
            {busy ? "清空中…" : "确认清空"}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
