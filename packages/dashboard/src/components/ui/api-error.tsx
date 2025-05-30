"use client"

import React from "react"
import { AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ApiError } from "@/lib/api-client"

interface ApiErrorProps {
  error: ApiError | Error | null
  onRetry?: () => void | Promise<any>
  className?: string
}

export function ApiErrorMessage({ error, onRetry, className = "" }: ApiErrorProps) {
  if (!error) return null

  let title = "Error"
  let message = "An unexpected error occurred. Please try again later."
  
  if (error instanceof ApiError) {
    title = `Error ${error.status}`
    
    // Handle common API error status codes
    switch (error.status) {
      case 401:
        message = "You are not authenticated. Please log in and try again."
        break
      case 403:
        message = "You don't have permission to perform this action."
        break
      case 404:
        message = "The requested resource was not found."
        break
      case 422:
        message = "The submitted data is invalid. Please check your input and try again."
        break
      case 429:
        message = "Too many requests. Please try again later."
        break
      case 500:
        message = "Internal server error. Our team has been notified."
        break
      default:
        message = error.message || "An error occurred while communicating with the server."
    }
  } else {
    message = error.message || message
  }

  return (
    <Alert variant="destructive" className={`my-4 ${className}`}>
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex flex-col gap-2">
        <p>{message}</p>
        {onRetry && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onRetry} 
            className="mt-2 w-full sm:w-auto"
          >
            Try again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

export function ApiErrorFull({ error, onRetry }: ApiErrorProps) {
  return (
    <div className="flex h-[50vh] w-full flex-col items-center justify-center p-4">
      <AlertTriangle className="h-16 w-16 text-destructive mb-4" />
      <ApiErrorMessage error={error} onRetry={onRetry} className="max-w-md" />
    </div>
  )
}
