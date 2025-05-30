"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { DateRangePickerProps } from "@/types"

export function DateRangePicker({
  from,
  to,
  onSelect,
  className,
}: DateRangePickerProps): React.ReactElement {
  const handleClick = React.useCallback(() => {
    // In a real implementation, this would open a date picker dialog
    // For now, we'll just use a placeholder function
    const today = new Date()
    const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
    onSelect({ from: today, to: nextWeek })
  }, [onSelect])

  return (
    <div className={cn("grid gap-2", className)}>
      <Button
        variant="outline"
        className={cn(
          "w-[300px] justify-start text-left font-normal",
        )}
        onClick={handleClick}
        type="button"
      >
        <CalendarIcon className="mr-2 h-4 w-4" />
        {from ? (
          to ? (
            <>
              {from.toLocaleDateString()} - {to.toLocaleDateString()}
            </>
          ) : (
            from.toLocaleDateString()
          )
        ) : (
          <span>Pick a date range</span>
        )}
      </Button>
    </div>
  )
}

export { type DateRangePickerProps }
