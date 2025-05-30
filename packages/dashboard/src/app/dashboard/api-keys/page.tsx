"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Mock API keys data
const mockApiKeys = [
  {
    id: "key-1",
    name: "Production API Key",
    prefix: "pk_live_",
    suffix: "xz7a9w",
    created_at: "2025-04-15T10:30:00Z",
    last_used: "2025-05-27T15:32:18Z",
    status: "active",
    environment: "production",
    permissions: ["credentials:read", "credentials:write", "wallets:read", "wallets:write"],
    rate_limit: 100,
    total_requests: 12458
  },
  {
    id: "key-2",
    name: "Development API Key",
    prefix: "pk_dev_",
    suffix: "qr5t8p",
    created_at: "2025-04-15T10:35:00Z",
    last_used: "2025-05-26T14:45:32Z",
    status: "active",
    environment: "development",
    permissions: ["credentials:read", "credentials:write", "wallets:read", "wallets:write"],
    rate_limit: 100,
    total_requests: 8342
  },
  {
    id: "key-3",
    name: "Testing API Key",
    prefix: "pk_test_",
    suffix: "lm3n4b",
    created_at: "2025-04-20T09:15:00Z",
    last_used: "2025-05-25T16:12:45Z",
    status: "active",
    environment: "test",
    permissions: ["credentials:read", "credentials:write", "wallets:read", "wallets:write"],
    rate_limit: 100,
    total_requests: 3256
  },
  {
    id: "key-4",
    name: "Mobile App Key",
    prefix: "pk_live_",
    suffix: "gh7j8k",
    created_at: "2025-05-10T13:20:00Z",
    last_used: "2025-05-27T14:05:29Z",
    status: "active",
    environment: "production",
    permissions: ["credentials:read", "wallets:read"],
    rate_limit: 50,
    total_requests: 4521
  },
  {
    id: "key-5",
    name: "Legacy API Key",
    prefix: "pk_live_",
    suffix: "dc5v6b",
    created_at: "2025-03-05T11:45:00Z",
    last_used: "2025-04-20T09:30:15Z",
    status: "revoked",
    environment: "production",
    permissions: ["credentials:read", "credentials:write", "wallets:read", "wallets:write"],
    rate_limit: 100,
    total_requests: 25478
  }
]

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric"
  })
}

function formatRelativeTime(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return `${diffInSeconds} seconds ago`
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)} minutes ago`
  } else if (diffInSeconds < 86400) {
    return `${Math.floor(diffInSeconds / 3600)} hours ago`
  } else {
    return `${Math.floor(diffInSeconds / 86400)} days ago`
  }
}

function getEnvironmentBadge(environment: string) {
  switch (environment) {
    case "production":
      return <Badge className="bg-blue-500">Production</Badge>
    case "development":
      return <Badge className="bg-yellow-500">Development</Badge>
    case "test":
      return <Badge className="bg-purple-500">Test</Badge>
    default:
      return <Badge>{environment}</Badge>
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "active":
      return <Badge variant="outline" className="border-green-500 text-green-600">Active</Badge>
    case "revoked":
      return <Badge variant="outline" className="border-red-500 text-red-600">Revoked</Badge>
    case "expired":
      return <Badge variant="outline" className="border-yellow-500 text-yellow-600">Expired</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

export default function ApiKeysPage() {
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showNewApiKey, setShowNewApiKey] = useState(false)
  const [newApiKey, setNewApiKey] = useState("")
  const [copySuccess, setCopySuccess] = useState(false)
  
  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(newApiKey)
      .then(() => {
        setCopySuccess(true)
        setTimeout(() => setCopySuccess(false), 2000)
      })
      .catch(err => {
        console.error("Failed to copy: ", err)
      })
  }
  
  const handleCreateApiKey = () => {
    // In a real application, this would call an API to create a new key
    setShowCreateDialog(false)
    setNewApiKey("pk_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p")
    setShowNewApiKey(true)
  }
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground">
            Manage API keys for integrating with EUDI-Connect
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>Create API Key</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create New API Key</DialogTitle>
                <DialogDescription>
                  Create a new API key for integrating with EUDI-Connect services.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="key-name" className="text-right">
                    Key Name
                  </Label>
                  <Input
                    id="key-name"
                    className="col-span-3"
                    placeholder="e.g., Production API Key"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="environment" className="text-right">
                    Environment
                  </Label>
                  <Select defaultValue="production">
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select environment" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="production">Production</SelectItem>
                      <SelectItem value="development">Development</SelectItem>
                      <SelectItem value="test">Test</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="rate-limit" className="text-right">
                    Rate Limit
                  </Label>
                  <Select defaultValue="100">
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select rate limit" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="50">50 requests/min</SelectItem>
                      <SelectItem value="100">100 requests/min</SelectItem>
                      <SelectItem value="200">200 requests/min</SelectItem>
                      <SelectItem value="500">500 requests/min</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-start gap-4">
                  <Label className="text-right pt-2">
                    Permissions
                  </Label>
                  <div className="col-span-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="credentials-read" className="h-4 w-4" defaultChecked />
                      <Label htmlFor="credentials-read" className="font-normal">
                        credentials:read
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="credentials-write" className="h-4 w-4" defaultChecked />
                      <Label htmlFor="credentials-write" className="font-normal">
                        credentials:write
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="wallets-read" className="h-4 w-4" defaultChecked />
                      <Label htmlFor="wallets-read" className="font-normal">
                        wallets:read
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="wallets-write" className="h-4 w-4" defaultChecked />
                      <Label htmlFor="wallets-write" className="font-normal">
                        wallets:write
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="compliance-read" className="h-4 w-4" />
                      <Label htmlFor="compliance-read" className="font-normal">
                        compliance:read
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="billing-read" className="h-4 w-4" />
                      <Label htmlFor="billing-read" className="font-normal">
                        billing:read
                      </Label>
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateApiKey}>
                  Create API Key
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          <Dialog open={showNewApiKey} onOpenChange={setShowNewApiKey}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>API Key Created</DialogTitle>
                <DialogDescription>
                  Your new API key has been created. Please copy it now as you won&apos;t be able to view it again.
                </DialogDescription>
              </DialogHeader>
              <div className="py-6">
                <div className="bg-muted p-4 rounded-md font-mono text-sm break-all">
                  {newApiKey}
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Be sure to keep this key secure. Don&apos;t commit it to version control or share it publicly.
                </p>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewApiKey(false)}>
                  Done
                </Button>
                <Button onClick={handleCopyApiKey}>
                  {copySuccess ? "Copied!" : "Copy to Clipboard"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          <Button variant="outline">View API Documentation</Button>
        </div>
      </div>
      
      <div className="space-y-6">
        {mockApiKeys.map(key => (
          <Card key={key.id} className={key.status === "revoked" ? "border-red-200 opacity-70" : ""}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle>{key.name}</CardTitle>
                  {getEnvironmentBadge(key.environment)}
                  {getStatusBadge(key.status)}
                </div>
                <div className="font-mono text-sm bg-muted px-2 py-1 rounded">
                  {key.prefix}•••••••{key.suffix}
                </div>
              </div>
              <CardDescription>
                Created on {formatDateTime(key.created_at)} • Last used {formatRelativeTime(key.last_used)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-sm font-medium mb-2">Permissions</h3>
                  <div className="flex flex-wrap gap-1">
                    {key.permissions.map((permission, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {permission}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium mb-2">Rate Limit</h3>
                  <p className="text-sm">{key.rate_limit} requests per minute</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium mb-2">Usage</h3>
                  <p className="text-sm">{key.total_requests.toLocaleString()} total requests</p>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              {key.status === "active" && (
                <>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">Edit</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                      <DialogHeader>
                        <DialogTitle>Edit API Key</DialogTitle>
                        <DialogDescription>
                          Update the settings for this API key.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="edit-key-name" className="text-right">
                            Key Name
                          </Label>
                          <Input
                            id="edit-key-name"
                            className="col-span-3"
                            defaultValue={key.name}
                          />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="edit-rate-limit" className="text-right">
                            Rate Limit
                          </Label>
                          <Select defaultValue={key.rate_limit.toString()}>
                            <SelectTrigger className="col-span-3">
                              <SelectValue placeholder="Select rate limit" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="50">50 requests/min</SelectItem>
                              <SelectItem value="100">100 requests/min</SelectItem>
                              <SelectItem value="200">200 requests/min</SelectItem>
                              <SelectItem value="500">500 requests/min</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid grid-cols-4 items-start gap-4">
                          <Label className="text-right pt-2">
                            Permissions
                          </Label>
                          <div className="col-span-3 space-y-2">
                            {["credentials:read", "credentials:write", "wallets:read", "wallets:write", "compliance:read", "billing:read"].map((perm) => (
                              <div key={perm} className="flex items-center gap-2">
                                <input 
                                  type="checkbox" 
                                  id={`edit-${perm}`} 
                                  className="h-4 w-4" 
                                  defaultChecked={key.permissions.includes(perm)} 
                                />
                                <Label htmlFor={`edit-${perm}`} className="font-normal">
                                  {perm}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button type="submit">Save Changes</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                        Revoke
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Revoke API Key</DialogTitle>
                        <DialogDescription>
                          Are you sure you want to revoke this API key? This action cannot be undone.
                        </DialogDescription>
                      </DialogHeader>
                      <DialogFooter className="mt-4">
                        <Button variant="outline">Cancel</Button>
                        <Button variant="destructive">Revoke Key</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </>
              )}
              <Button variant="ghost" size="sm">View Usage</Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
