"use client"

import React from "react"
import { Loader2 } from "lucide-react"

interface LoadingProps {
  size?: number
  className?: string
  text?: string
}

export function Loading({ size = 24, className = "", text }: LoadingProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-4 ${className}`}>
      <Loader2 className="mr-2 h-6 w-6 animate-spin" style={{ height: size, width: size }} />
      {text && <p className="text-sm text-muted-foreground mt-2">{text}</p>}
    </div>
  )
}

export function LoadingPage() {
  return (
    <div className="flex h-[50vh] w-full items-center justify-center">
      <Loading size={32} text="Loading..." />
    </div>
  )
}

export function LoadingCard() {
  return (
    <div className="flex h-[200px] w-full items-center justify-center rounded-lg border bg-card text-card-foreground shadow-sm">
      <Loading text="Loading data..." />
    </div>
  )
}

export function LoadingRow() {
  return (
    <div className="flex h-[40px] w-full items-center justify-center py-2">
      <Loading size={16} />
    </div>
  )
}
