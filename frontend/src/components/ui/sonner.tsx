import type { ComponentProps } from "react"
import { Toaster as Sonner } from "sonner"

type ToasterProps = ComponentProps<typeof Sonner>

function Toaster({ ...props }: ToasterProps) {
  return (
    <Sonner
      className="toaster group"
      position="bottom-center"
      offset={{ bottom: "6rem" }}
      toastOptions={{
        duration: 3200,
        classNames: {
          toast:
            "chat-ios-toast liquid-glass group-[.toaster]:bg-transparent group-[.toaster]:border-0 group-[.toaster]:shadow-none group-[.toaster]:text-inherit",
          title: "text-sm",
          description: "text-sm opacity-90",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
