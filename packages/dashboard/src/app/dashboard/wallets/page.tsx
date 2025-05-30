"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"

// Mock wallet provider data
const mockWalletProviders = [
  {
    id: "wallet-provider-1",
    name: "EU Wallet Reference Implementation",
    description: "Official reference implementation of the EU Digital Identity Wallet",
    version: "2.3.1",
    provider: "European Commission",
    status: "verified",
    compatibility: "full",
    last_checked: "2025-05-25T14:30:00Z",
    supported_features: [
      "OpenID4VP",
      "SIOP2",
      "ISO-MDL",
      "QR Code",
      "BLE",
      "NFC"
    ],
    active_sessions: 542,
    total_sessions: 12458,
    success_rate: 98.7
  },
  {
    id: "wallet-provider-2",
    name: "DigiWallet Pro",
    description: "Commercial EU-compliant digital identity wallet",
    version: "4.1.0",
    provider: "DigiSolutions GmbH",
    status: "verified",
    compatibility: "partial",
    last_checked: "2025-05-26T09:15:00Z",
    supported_features: [
      "OpenID4VP",
      "SIOP2",
      "QR Code",
      "BLE"
    ],
    active_sessions: 328,
    total_sessions: 8745,
    success_rate: 96.2
  },
  {
    id: "wallet-provider-3",
    name: "NationalID Mobile",
    description: "National eID wallet solution for citizens",
    version: "2.0.5",
    provider: "Ministry of Digital Affairs",
    status: "verified",
    compatibility: "partial",
    last_checked: "2025-05-24T16:45:00Z",
    supported_features: [
      "OpenID4VP",
      "SIOP2",
      "QR Code",
      "NFC"
    ],
    active_sessions: 195,
    total_sessions: 5842,
    success_rate: 97.5
  },
  {
    id: "wallet-provider-4",
    name: "PrivateID Wallet",
    description: "Privacy-focused digital identity wallet",
    version: "1.8.2",
    provider: "PrivacyTech Inc.",
    status: "testing",
    compatibility: "partial",
    last_checked: "2025-05-22T11:30:00Z",
    supported_features: [
      "OpenID4VP",
      "SIOP2",
      "QR Code"
    ],
    active_sessions: 84,
    total_sessions: 1256,
    success_rate: 93.8
  }
]

// Mock wallet sessions data
const mockWalletSessions = [
  {
    id: "session-1",
    wallet_provider_id: "wallet-provider-1",
    wallet_provider_name: "EU Wallet Reference Implementation",
    user_id: "user-123",
    status: "active",
    created_at: "2025-05-27T14:25:00Z",
    last_activity: "2025-05-27T15:10:22Z",
    operations: [
      { type: "connect", timestamp: "2025-05-27T14:25:00Z", status: "success" },
      { type: "request_credential", timestamp: "2025-05-27T14:28:15Z", status: "success" },
      { type: "present_credential", timestamp: "2025-05-27T15:10:22Z", status: "success" }
    ],
    device_info: {
      os: "Android 15",
      model: "Google Pixel 9",
      ip_address: "192.168.1.1",
      location: "Berlin, Germany"
    }
  },
  {
    id: "session-2",
    wallet_provider_id: "wallet-provider-2",
    wallet_provider_name: "DigiWallet Pro",
    user_id: "user-456",
    status: "active",
    created_at: "2025-05-27T13:42:10Z",
    last_activity: "2025-05-27T14:55:33Z",
    operations: [
      { type: "connect", timestamp: "2025-05-27T13:42:10Z", status: "success" },
      { type: "request_credential", timestamp: "2025-05-27T13:45:22Z", status: "success" },
      { type: "present_credential", timestamp: "2025-05-27T14:55:33Z", status: "success" }
    ],
    device_info: {
      os: "iOS 18.2",
      model: "iPhone 16 Pro",
      ip_address: "192.168.1.2",
      location: "Paris, France"
    }
  },
  {
    id: "session-3",
    wallet_provider_id: "wallet-provider-3",
    wallet_provider_name: "NationalID Mobile",
    user_id: "user-789",
    status: "active",
    created_at: "2025-05-27T12:15:45Z",
    last_activity: "2025-05-27T12:38:12Z",
    operations: [
      { type: "connect", timestamp: "2025-05-27T12:15:45Z", status: "success" },
      { type: "request_credential", timestamp: "2025-05-27T12:20:38Z", status: "success" },
      { type: "present_credential", timestamp: "2025-05-27T12:38:12Z", status: "success" }
    ],
    device_info: {
      os: "Android 15",
      model: "Samsung Galaxy S25",
      ip_address: "192.168.1.3",
      location: "Madrid, Spain"
    }
  },
  {
    id: "session-4",
    wallet_provider_id: "wallet-provider-1",
    wallet_provider_name: "EU Wallet Reference Implementation",
    user_id: "user-234",
    status: "completed",
    created_at: "2025-05-27T10:30:12Z",
    last_activity: "2025-05-27T11:05:48Z",
    operations: [
      { type: "connect", timestamp: "2025-05-27T10:30:12Z", status: "success" },
      { type: "request_credential", timestamp: "2025-05-27T10:35:27Z", status: "success" },
      { type: "present_credential", timestamp: "2025-05-27T10:42:18Z", status: "success" },
      { type: "disconnect", timestamp: "2025-05-27T11:05:48Z", status: "success" }
    ],
    device_info: {
      os: "iOS 18.1",
      model: "iPhone 15",
      ip_address: "192.168.1.4",
      location: "Rome, Italy"
    }
  },
  {
    id: "session-5",
    wallet_provider_id: "wallet-provider-4",
    wallet_provider_name: "PrivateID Wallet",
    user_id: "user-567",
    status: "error",
    created_at: "2025-05-27T09:15:22Z",
    last_activity: "2025-05-27T09:18:45Z",
    operations: [
      { type: "connect", timestamp: "2025-05-27T09:15:22Z", status: "success" },
      { type: "request_credential", timestamp: "2025-05-27T09:18:45Z", status: "error" }
    ],
    error: {
      code: "unsupported_credential_type",
      message: "The wallet does not support the requested credential type"
    },
    device_info: {
      os: "Android 14",
      model: "OnePlus 13",
      ip_address: "192.168.1.5",
      location: "Amsterdam, Netherlands"
    }
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

function getCompatibilityBadge(compatibility: string) {
  switch (compatibility) {
    case "full":
      return <Badge className="bg-green-500">Full Compatibility</Badge>
    case "partial":
      return <Badge className="bg-yellow-500">Partial Compatibility</Badge>
    case "limited":
      return <Badge className="bg-orange-500">Limited Compatibility</Badge>
    case "incompatible":
      return <Badge className="bg-red-500">Incompatible</Badge>
    default:
      return <Badge>{compatibility}</Badge>
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "active":
      return <Badge variant="outline" className="border-green-500 text-green-600">Active</Badge>
    case "completed":
      return <Badge variant="outline" className="border-blue-500 text-blue-600">Completed</Badge>
    case "error":
      return <Badge variant="outline" className="border-red-500 text-red-600">Error</Badge>
    case "expired":
      return <Badge variant="outline" className="border-yellow-500 text-yellow-600">Expired</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

export default function WalletsPage() {
  const [activeTab, setActiveTab] = useState("wallet-providers")
  const [statusFilter, setStatusFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  
  // Filter sessions based on search query and filters
  const filteredSessions = mockWalletSessions.filter(session => {
    const matchesSearch = searchQuery === "" || 
      session.wallet_provider_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.id.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStatus = statusFilter === "all" || session.status === statusFilter
    
    return matchesSearch && matchesStatus
  })
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Wallet Integration</h1>
          <p className="text-muted-foreground">
            Manage wallet providers and monitor wallet sessions
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Dialog>
            <DialogTrigger asChild>
              <Button>Register New Wallet Provider</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Register Wallet Provider</DialogTitle>
                <DialogDescription>
                  Add a new wallet provider to connect with your applications.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="name" className="text-right">
                    Name
                  </Label>
                  <Input
                    id="name"
                    className="col-span-3"
                    placeholder="e.g., MyWallet App"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="provider" className="text-right">
                    Provider
                  </Label>
                  <Input
                    id="provider"
                    className="col-span-3"
                    placeholder="e.g., Example Corporation"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="version" className="text-right">
                    Version
                  </Label>
                  <Input
                    id="version"
                    className="col-span-3"
                    placeholder="e.g., 1.0.0"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="description" className="text-right">
                    Description
                  </Label>
                  <Input
                    id="description"
                    className="col-span-3"
                    placeholder="Describe the wallet provider"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="features" className="text-right">
                    Features
                  </Label>
                  <div className="col-span-3 flex flex-wrap gap-2">
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">OpenID4VP</Badge>
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">SIOP2</Badge>
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">ISO-MDL</Badge>
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">QR Code</Badge>
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">BLE</Badge>
                    <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">NFC</Badge>
                    <Button variant="outline" size="sm" className="h-6">+ More</Button>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Register Wallet Provider</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button variant="outline">Integration Guide</Button>
        </div>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="wallet-providers">Wallet Providers</TabsTrigger>
          <TabsTrigger value="wallet-sessions">Wallet Sessions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="wallet-providers" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockWalletProviders.map(provider => (
              <Card key={provider.id} className="overflow-hidden">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-center">
                    <CardTitle>{provider.name}</CardTitle>
                    <Badge className={`capitalize ${
                      provider.status === 'verified' ? 'bg-green-500' : 
                      provider.status === 'testing' ? 'bg-blue-500' :
                      'bg-gray-500'
                    }`}>
                      {provider.status}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {provider.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Provider:</dt>
                      <dd className="font-medium">{provider.provider}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Version:</dt>
                      <dd className="font-medium">{provider.version}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Compatibility:</dt>
                      <dd className="font-medium">
                        {getCompatibilityBadge(provider.compatibility)}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Last Checked:</dt>
                      <dd className="font-medium">{formatDateTime(provider.last_checked)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground mb-1">Supported Features:</dt>
                      <dd className="flex flex-wrap gap-1">
                        {provider.supported_features.map((feature, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
                <CardFooter className="flex justify-between border-t bg-muted/50 px-6 py-3">
                  <div className="text-sm">
                    <div className="font-medium">{provider.active_sessions} active sessions</div>
                    <div className="text-muted-foreground">{provider.success_rate}% success rate</div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">Test</Button>
                    <Link href={`/dashboard/wallets/providers/${provider.id}`}>
                      <Button variant="default" size="sm">View</Button>
                    </Link>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="wallet-sessions" className="mt-6">
          <div className="rounded-md border">
            <div className="p-4 flex flex-wrap gap-4 border-b">
              <div className="flex-1 min-w-[250px]">
                <Input
                  placeholder="Search by wallet provider, user ID or session ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Status:</span>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                    <SelectItem value="expired">Expired</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button variant="outline" size="sm" className="h-9">
                Refresh
              </Button>
            </div>
            <div className="relative overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50">
                  <tr>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Session ID
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Wallet Provider
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      User ID
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Created
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Last Activity
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 whitespace-nowrap">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSessions.map(session => (
                    <tr key={session.id} className="border-b hover:bg-muted/50">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs">
                        {session.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {session.wallet_provider_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs">
                        {session.user_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {formatDateTime(session.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {formatDateTime(session.last_activity)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(session.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-2">
                          <Link href={`/dashboard/wallets/sessions/${session.id}`}>
                            <Button variant="ghost" size="sm">View</Button>
                          </Link>
                          {session.status === "active" && (
                            <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                              End
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredSessions.length === 0 && (
              <div className="px-6 py-8 text-center text-muted-foreground">
                No wallet sessions found matching your criteria.
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
