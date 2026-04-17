import { cn } from "@/lib/utils"
import { Loader2Icon } from "lucide-react"

function Spinner({
  className,
  "aria-label": ariaLabel = "Loading",
  ...props
}: React.ComponentProps<"svg">) {
  return (
    <Loader2Icon
      role="status"
      aria-label={ariaLabel}
      className={cn("size-4 animate-spin", className)}
      {...props}
    />
  )
}

export { Spinner }
