import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ClearUserDataDialogProps {
  open: boolean;
  busy: boolean;
  error: string | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function ClearUserDataDialog({
  open,
  busy,
  error,
  onOpenChange,
  onConfirm,
}: ClearUserDataDialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className={cn(
            "fixed inset-0 z-[60] bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 motion-reduce:animate-none",
          )}
        />
        <DialogPrimitive.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-[60] w-[min(92vw,24rem)] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-destructive/40 bg-background p-6 shadow-lg outline-none",
          )}
          aria-describedby="clear-user-data-desc"
        >
          <DialogPrimitive.Title className="text-lg font-semibold text-destructive">
            清空用户数据？
          </DialogPrimitive.Title>
          <DialogPrimitive.Description
            id="clear-user-data-desc"
            className="mt-3 text-sm leading-relaxed text-muted-foreground"
          >
            将永久删除本机对话、个人设置、IndexedDB 历史，以及服务端的 checkpoint 与 Mem0/FAISS
            记忆，并生成新用户身份后刷新页面。此操作不可恢复。
          </DialogPrimitive.Description>
          {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="outline" disabled={busy} onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button
              type="button"
              disabled={busy}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={onConfirm}
            >
              {busy ? "清空中…" : "确认清空"}
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
