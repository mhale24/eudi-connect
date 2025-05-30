"use client"

import { useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { CredentialType, CredentialField, HistoricalStat as _HistoricalStat, VerificationResult } from "@/types"

interface _PageParams {
  params: {
    id: string
  }
}

// Mock credential type data
const mockCredentialTypes: { [key: string]: CredentialType } = {
  "type-1": {
    id: "type-1",
    name: "EU Digital Identity",
    schema: "https://eudi-connect.eu/schemas/eudi",
    description: "European Digital Identity credential following eIDAS 2.0 specifications. Provides a standardized way to digitally identify citizens across the European Union, compliant with latest privacy and security regulations.",
    created_at: "2025-04-12T10:00:00Z",
    updated_at: "2025-05-15T14:30:00Z",
    created_by: "admin@example.com",
    total_issued: 3456,
    total_verified: 8921,
    total_revoked: 128,
    status: "active",
    template: {
      fields: [
        { name: "firstName", type: "string", required: true, description: "First name of the holder" },
        { name: "lastName", type: "string", required: true, description: "Last name of the holder" },
        { name: "dateOfBirth", type: "date", required: true, description: "Date of birth in ISO format" },
        { name: "nationality", type: "string", required: true, description: "Nationality code in ISO 3166-1 alpha-2 format" },
        { name: "idNumber", type: "string", required: true, description: "National identification number" },
        { name: "issuingAuthority", type: "string", required: true, description: "Authority that issued the identity document" },
        { name: "expiryDate", type: "date", required: true, description: "Expiry date in ISO format" },
        { name: "photo", type: "binary", required: false, description: "Biometric photo data" }
      ],
      context: ["https://www.w3.org/2018/credentials/v1", "https://eudi-connect.eu/2025/credentials/identity/v1"],
      type: ["VerifiableCredential", "EuropeanDigitalIdentityCredential"],
      revocation_registry: "https://eudi-connect.eu/revocation/v1/status",
      cryptographic_suite: "Ed25519Signature2020"
    },
    historical_stats: [
      { month: "Jan", issued: 210, verified: 423, revoked: 5 },
      { month: "Feb", issued: 245, verified: 512, revoked: 8 },
      { month: "Mar", issued: 320, verified: 645, revoked: 12 },
      { month: "Apr", issued: 340, verified: 732, revoked: 15 },
      { month: "May", issued: 390, verified: 821, revoked: 14 }
    ],
    verification_results: [
      { name: "Valid", value: 8540 },
      { name: "Expired", value: 218 },
      { name: "Revoked", value: 128 },
      { name: "Invalid Signature", value: 35 }
    ]
  },
  "type-2": {
    id: "type-2",
    name: "Digital Driving License",
    schema: "https://eudi-connect.eu/schemas/ddl",
    description: "EU compliant digital driving license credential",
    created_at: "2025-04-15T14:30:00Z",
    updated_at: "2025-05-10T09:15:00Z",
    created_by: "admin@example.com",
    total_issued: 1289,
    total_verified: 3421,
    total_revoked: 42,
    status: "active"
  }
}

// Mock recent activities
const mockRecentActivities = [
  {
    id: "act-1",
    action: "credential_issued",
    user_id: "user-456",
    wallet_id: "wallet-123",
    timestamp: "2025-05-27T14:32:15Z",
    details: {
      credential_id: "cred-9876",
      issuer: "organization-789"
    }
  },
  {
    id: "act-2",
    action: "credential_verified",
    user_id: "user-789",
    wallet_id: "wallet-456",
    timestamp: "2025-05-27T13:45:22Z",
    details: {
      verification_id: "verify-1234",
      verifier: "organization-123"
    }
  },
  {
    id: "act-3",
    action: "template_updated",
    user_id: "admin@example.com",
    timestamp: "2025-05-26T16:10:05Z",
    details: {
      changes: ["Added photo field", "Updated nationality field requirements"]
    }
  },
  {
    id: "act-4",
    action: "credential_revoked",
    user_id: "user-123",
    wallet_id: "wallet-789",
    timestamp: "2025-05-26T15:22:38Z",
    details: {
      credential_id: "cred-5432",
      reason: "Information update required"
    }
  },
  {
    id: "act-5",
    action: "credential_issued",
    user_id: "user-789",
    wallet_id: "wallet-456",
    timestamp: "2025-05-26T14:15:09Z",
    details: {
      credential_id: "cred-6543",
      issuer: "organization-456"
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

function getActionBadge(action: string) {
  switch (action) {
    case "credential_issued":
      return <Badge className="bg-blue-500">Issued</Badge>
    case "credential_verified":
      return <Badge className="bg-green-500">Verified</Badge>
    case "credential_revoked":
      return <Badge className="bg-red-500">Revoked</Badge>
    case "template_updated":
      return <Badge className="bg-purple-500">Template Updated</Badge>
    default:
      return <Badge>{action}</Badge>
  }
}

// Colors for the pie chart
const COLORS = ['#4CAF50', '#FFC107', '#F44336', '#9C27B0'];

export default function CredentialTypePage() {
  const params = useParams<{id: string}>()
  const credentialTypeId = params.id
  const [activeTab, setActiveTab] = useState("overview")
  
  // Get the credential type data (would fetch from API in a real implementation)
  const credentialType: CredentialType = mockCredentialTypes[credentialTypeId] || {
    id: credentialTypeId,
    name: "Unknown Credential Type",
    schema: "unknown",
    description: "This credential type does not exist",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    created_by: "system",
    total_issued: 0,
    total_verified: 0,
    total_revoked: 0,
    status: "inactive" as const,
    template: {
      fields: [],
      context: [],
      type: []
    },
    historical_stats: [],
    verification_results: []
  } as CredentialType
  
  if (!credentialType) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px]">
        <h2 className="text-xl font-semibold mb-2">Credential Type Not Found</h2>
        <p className="text-muted-foreground mb-6">The credential type you&apos;re looking for doesn&apos;t exist or has been removed.</p>
        <Link href="/dashboard/credentials">
          <Button>Return to Credentials</Button>
        </Link>
      </div>
    )
  }
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{credentialType.name}</h1>
          <p className="text-muted-foreground">
            {credentialType.schema}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline">Export Schema</Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button>Issue Credential</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Issue {credentialType.name}</DialogTitle>
                <DialogDescription>
                  Issue a new credential to a user&apos;s wallet.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="wallet-id" className="text-right">
                    Wallet ID
                  </Label>
                  <Input
                    id="wallet-id"
                    className="col-span-3"
                    placeholder="Enter wallet identifier"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="user-id" className="text-right">
                    User ID
                  </Label>
                  <Input
                    id="user-id"
                    className="col-span-3"
                    placeholder="Enter user identifier"
                  />
                </div>
                {credentialType.template?.fields?.map((field: CredentialField, index: number) => (
                  <div key={index} className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor={`field-${field.name}`} className="text-right">
                      {field.name} {field.required && <span className="text-red-500">*</span>}
                    </Label>
                    <Input
                      id={`field-${field.name}`}
                      className="col-span-3"
                      placeholder={field.description}
                      type={field.type === 'date' ? 'date' : 'text'}
                    />
                  </div>
                ))}
              </div>
              <DialogFooter>
                <Button type="submit">Issue Credential</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="template">Template</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="activity">Recent Activity</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Credential Type Details</CardTitle>
                <CardDescription>
                  Information about this credential type and its usage. Don&apos;t share this credential with unauthorized parties.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
{/* Rest of the code remains the same */}
                    <h3 className="font-medium">Description</h3>
                    <p className="text-muted-foreground mt-1">{credentialType.description}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-medium">Created</h3>
                      <p className="text-muted-foreground mt-1">{formatDateTime(credentialType.created_at)}</p>
                    </div>
                    <div>
                      <h3 className="font-medium">Last Updated</h3>
                      <p className="text-muted-foreground mt-1">{formatDateTime(credentialType.updated_at ?? credentialType.created_at)}</p>
                    </div>
                    <div>
                      <h3 className="font-medium">Created By</h3>
                      <p className="text-muted-foreground mt-1">{credentialType.created_by ?? 'Unknown'}</p>
                    </div>
                    <div>
                      <h3 className="font-medium">Status</h3>
                      <Badge variant="outline" className="mt-1 capitalize">{credentialType.status}</Badge>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium">Schema URL</h3>
                    <p className="text-muted-foreground mt-1 break-all">{credentialType.schema}</p>
                  </div>
                  
                  {credentialType.template?.revocation_registry && (
                    <div>
                      <h3 className="font-medium">Revocation Registry</h3>
                      <p className="text-muted-foreground mt-1 break-all">{credentialType.template.revocation_registry}</p>
                    </div>
                  )}
                  
                  {credentialType.template?.cryptographic_suite && (
                    <div>
                      <h3 className="font-medium">Cryptographic Suite</h3>
                      <p className="text-muted-foreground mt-1">{credentialType.template.cryptographic_suite}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Usage Statistics</CardTitle>
                <CardDescription>
                  Credential operation statistics.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  <div className="flex flex-col items-center">
                    <div className="text-4xl font-bold">
                      {credentialType.total_issued.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Total Issued</div>
                  </div>
                  
                  <div className="flex flex-col items-center">
                    <div className="text-4xl font-bold">
                      {credentialType.total_verified.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Total Verified</div>
                  </div>
                  
                  <div className="flex flex-col items-center">
                    <div className="text-4xl font-bold">
                      {(credentialType.total_revoked ?? 0).toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Total Revoked</div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-center">
                <Link href={`/dashboard/credentials/analytics?type=${credentialTypeId}`}>
                  <Button variant="outline">View Detailed Analytics</Button>
                </Link>
              </CardFooter>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="template" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Template Fields</CardTitle>
                <CardDescription>
                  Field to verify the holder&apos;s control over the credential.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative overflow-x-auto rounded-md border">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs uppercase bg-muted/50">
                      <tr>
                        <th scope="col" className="px-6 py-3">Field Name</th>
                        <th scope="col" className="px-6 py-3">Type</th>
                        <th scope="col" className="px-6 py-3">Required</th>
                        <th scope="col" className="px-6 py-3">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {credentialType.template?.fields?.map((field: CredentialField, index: number) => (
                        <tr key={index} className="border-b hover:bg-muted/50">
                          <td className="px-6 py-4 font-medium">{field.name}</td>
                          <td className="px-6 py-4 capitalize">{field.type}</td>
                          <td className="px-6 py-4">{field.required ? "Yes" : "No"}</td>
                          <td className="px-6 py-4">{field.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button variant="outline">Export Template</Button>
                <Button>Edit Template</Button>
              </CardFooter>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Context and Type</CardTitle>
                <CardDescription>
                  Credential context and type definitions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium">@context</h3>
                    <div className="mt-2 space-y-2">
                      {credentialType.template?.context?.map((ctx: string, index: number) => (
                        <div key={index} className="rounded-md bg-muted p-2 text-xs break-all">
                          {ctx}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium">type</h3>
                    <div className="mt-2 space-y-2">
                      {credentialType.template?.type?.map((type: string, index: number) => (
                        <div key={index} className="rounded-md bg-muted p-2 text-xs">
                          {type}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="w-full">
                  View JSON Schema
                </Button>
              </CardFooter>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="analytics" className="mt-6">
          <div className="grid grid-cols-1 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Historical Operations</CardTitle>
                <CardDescription>
                  Monthly credential operations over time.
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px]">
                {credentialType.historical_stats?.map && (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={credentialType.historical_stats}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="issued" fill="#3b82f6" name="Issued" />
                      <Bar dataKey="verified" fill="#10b981" name="Verified" />
                      <Bar dataKey="revoked" fill="#ef4444" name="Revoked" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Verification Results</CardTitle>
                  <CardDescription>
                    Breakdown of verification outcomes.
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  {credentialType.verification_results?.length && (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={credentialType.verification_results}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          {credentialType.verification_results?.map((entry: VerificationResult, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Usage Metrics</CardTitle>
                  <CardDescription>
                    Key performance indicators.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium">Verification Rate</h3>
                        <p className="text-xs text-muted-foreground">Issuer&apos;s public key for signature verifications per issuance</p>
                      </div>
                      <div className="text-2xl font-bold">
                        {(credentialType.total_verified / credentialType.total_issued).toFixed(2)}x
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium">Revocation Rate</h3>
                        <p className="text-xs text-muted-foreground">Percentage of credentials revoked</p>
                      </div>
                      <div className="text-2xl font-bold">
                        {(((credentialType.total_revoked ?? 0) / credentialType.total_issued) * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium">Daily Average (30d)</h3>
                        <p className="text-xs text-muted-foreground">Daily credential operations</p>
                      </div>
                      <div className="text-2xl font-bold">
                        {Math.round((credentialType.total_issued + credentialType.total_verified) / 30)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="activity" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Recent operations performed with this credential type.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-8">
                {mockRecentActivities.map((activity) => (
                  <div key={activity.id} className="flex">
                    <div className="mr-4 flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      <span className="text-xl">
                        {activity.action === "credential_issued" && "📝"}
                        {activity.action === "credential_verified" && "✅"}
                        {activity.action === "credential_revoked" && "❌"}
                        {activity.action === "template_updated" && "🔄"}
                      </span>
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <p className="font-medium">
                            {activity.action === "template_updated" 
                              ? `Template updated by ${activity.user_id}`
                              : `Credential ${activity.action.split('_')[1]} for user ${activity.user_id}`
                            }
                          </p>
                          <div className="ml-2">
                            {getActionBadge(activity.action)}
                          </div>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(activity.timestamp)}
                        </span>
                      </div>
                      
                      {activity.wallet_id && (
                        <p className="text-sm text-muted-foreground">
                          Wallet ID: <span className="font-mono">{activity.wallet_id}</span>
                        </p>
                      )}
                      
                      {activity.details && (
                        <div className="rounded-md bg-muted p-2 mt-2">
                          <h4 className="text-xs font-medium mb-1">Details</h4>
                          <div className="text-xs">
                            {Object.entries(activity.details).map(([key, value]) => (
                              <div key={key} className="flex items-start">
                                <span className="font-medium min-w-[100px]">{key}:</span>
                                <span>
                                  {Array.isArray(value) 
                                    ? value.map((item, i) => <div key={i}>{item}</div>) 
                                    : value as string
                                  }
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter className="flex justify-center">
              <Button variant="outline">Load More Activity</Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
