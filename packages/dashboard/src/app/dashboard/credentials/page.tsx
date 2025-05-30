"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { LoadingPage, LoadingCard, Loading } from "@/components/ui/loading"
import { ApiErrorMessage, ApiErrorFull } from "@/components/ui/api-error"
import { useApi } from "@/hooks/use-api"
import { credentialTypesApi, credentialsApi } from "@/lib/api-client"
import { toast } from "@/components/ui/use-toast"

// Define types for our data based on the backend schema
interface CredentialType {
  id: string;
  name: string;
  schema: string;
  description: string;
  created_at: string;
  updated_at?: string;
  status: 'active' | 'inactive' | 'deprecated';
  total_issued: number;
  total_verified: number;
  total_revoked?: number;
}

interface CredentialLog {
  id: string;
  operation: 'issue' | 'verify' | 'revoke';
  credential_type_id: string;
  credential_type_name: string;
  wallet_id: string;
  timestamp: string;
  status: 'success' | 'failed' | 'pending';
  error?: string;
  user_id: string;
  metadata: Record<string, any>;
}
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric"
  })
}

function getOperationBadge(operation: string) {
  switch (operation) {
    case "issue":
      return <Badge className="bg-blue-500">Issue</Badge>
    case "verify":
      return <Badge className="bg-green-500">Verify</Badge>
    case "revoke":
      return <Badge className="bg-red-500">Revoke</Badge>
    default:
      return <Badge>{operation}</Badge>
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "success":
      return <Badge variant="outline" className="border-green-500 text-green-600">Success</Badge>
    case "failed":
      return <Badge variant="outline" className="border-red-500 text-red-600">Failed</Badge>
    case "pending":
      return <Badge variant="outline" className="border-yellow-500 text-yellow-600">Pending</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

export default function CredentialsPage() {
  const [activeTab, setActiveTab] = useState("credential-types")
  const [searchQuery, setSearchQuery] = useState("")
  const [operationFilter, setOperationFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")

  // Fetch credential types from the API using the API client
  const { 
    data: credentialTypes, 
    isLoading, 
    error, 
    refetch 
  } = useApi<CredentialType[]>()
  
  // Fetch data when component mounts
  useEffect(() => {
    const fetchCredentialTypes = async () => {
      try {
        await refetch(async () => await credentialTypesApi.getAll())
      } catch (err) {
        console.error('Failed to fetch credential types:', err)
      }
    }
    fetchCredentialTypes()
  }, [refetch])
  
  // Create handler functions that match the expected signature
  const handleRetryCredentialTypes = () => {
    // Need to handle the returned promise to avoid type errors
    void (async () => {
      try {
        await refetch(async () => await credentialTypesApi.getAll())
      } catch (error) {
        console.error('Error retrying credential types fetch:', error)
      }
    })()
  }

  // Fetch credential logs from the API using the API client
  const { 
    data: credentialLogs, 
    isLoading: isLoadingLogs, 
    error: errorLogs, 
    refetch: refetchLogs 
  } = useApi<CredentialLog[]>()
  
  // Fetch data when component mounts
  useEffect(() => {
    const fetchCredentialLogs = async () => {
      try {
        await refetchLogs(async () => await credentialsApi.getLogs())
      } catch (err) {
        console.error('Failed to fetch credential logs:', err)
      }
    }
    fetchCredentialLogs()
  }, [refetchLogs])
  
  const handleRetryCredentialLogs = () => {
    // Need to handle the returned promise to avoid type errors
    void (async () => {
      try {
        await refetchLogs(async () => await credentialsApi.getLogs())
      } catch (error) {
        console.error('Error retrying credential logs fetch:', error)
      }
    })()
  }

  // Filter credential types based on active tab
  const filteredCredentialTypes = credentialTypes ? credentialTypes.filter((type) => {
    if (activeTab === "credential-types") return true
    return type.status === activeTab
  }) : []

  // Filter logs based on search query and filters
  const filteredLogs = credentialLogs ? credentialLogs.filter((log: CredentialLog) => {
    const matchesSearch = searchQuery === "" || 
      log.credential_type_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.wallet_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.user_id.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesOperation = operationFilter === "all" || log.operation === operationFilter
    const matchesStatus = statusFilter === "all" || log.status === statusFilter
    
    return matchesSearch && matchesOperation && matchesStatus
  }) : []

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Credential Management</h1>
          <p className="text-muted-foreground">
            Issue, verify, and manage verifiable credentials
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Dialog>
            <DialogTrigger asChild>
              <Button>Create Credential Type</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create New Credential Type</DialogTitle>
                <DialogDescription>
                  You don&apos;t have any credential types created yet. Define a new credential type that can be issued to users&apos; wallets.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="name" className="text-right text-sm font-medium">
                    Name
                  </label>
                  <Input
                    id="name"
                    className="col-span-3"
                    placeholder="e.g., EU Digital Identity"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="schema" className="text-right text-sm font-medium">
                    Schema URL
                  </label>
                  <Input
                    id="schema"
                    className="col-span-3"
                    placeholder="e.g., https://eudi-connect.eu/schemas/example"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="description" className="text-right text-sm font-medium">
                    Description
                  </label>
                  <Input
                    id="description"
                    className="col-span-3"
                    placeholder="Describe the purpose of this credential type"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Create Credential Type</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button variant="outline">View Documentation</Button>
        </div>
      </div>
      
      {error && <ApiErrorMessage error={error} onRetry={refetch} />}
      {errorLogs && <ApiErrorMessage error={errorLogs} onRetry={refetchLogs} />}
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="credential-types">Credential Types</TabsTrigger>
          <TabsTrigger value="credential-logs">Operation Logs</TabsTrigger>
        </TabsList>
        
        <TabsContent value="credential-types" className="mt-6">
          {isLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <LoadingCard />
              <LoadingCard />
              <LoadingCard />
            </div>
          ) : error ? (
            <ApiErrorFull 
              error={error} 
              onRetry={handleRetryCredentialTypes}
            />
          ) : filteredCredentialTypes.length === 0 ? (
            <Card>
              <CardContent className="flex h-40 flex-col items-center justify-center p-6">
                <p className="mb-2 text-lg font-medium">No credential types found</p>
                <p className="text-center text-sm text-muted-foreground">
                  You haven&apos;t created any credential types yet.
                </p>
                <Button className="mt-4" asChild>
                  <Link href="/dashboard/credentials/types/new">Create New Type</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredCredentialTypes.map((type) => (
                <Card key={type.id} className="overflow-hidden">
                  <CardHeader className="pb-2">
                    <CardTitle>{type.name}</CardTitle>
                    <CardDescription className="flex justify-between">
                      <span>{type.description}</span>
                      <Badge variant={type.status === "active" ? "default" : type.status === "deprecated" ? "destructive" : "outline"}>
                        {type.status}
                      </Badge>
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-xl font-bold text-blue-500">{type.total_issued.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Issued</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-green-500">{type.total_verified.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Verified</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-red-500">{(type.total_revoked || 0).toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Revoked</div>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter className="bg-muted/50 pb-2 pt-2">
                    <div className="flex w-full justify-between">
                      <Button variant="ghost" asChild>
                        <Link href={`/dashboard/credentials/types/${type.id}`}>Details</Link>
                      </Button>
                      <Button variant="ghost" asChild>
                        <Link href={`/dashboard/credentials/issue?typeId=${type.id}`}>Issue</Link>
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="credential-logs" className="space-y-4">
          <div className="rounded-lg border bg-card">
            <div className="flex flex-col md:flex-row justify-between p-4 space-y-2 md:space-y-0">
              <div className="flex items-center">
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 w-full md:w-[150px] lg:w-[250px]"
                />
              </div>
              <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Operation:</span>
                  <Select value={operationFilter} onValueChange={setOperationFilter}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="All Operations" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="issue">Issue</SelectItem>
                      <SelectItem value="verify">Verify</SelectItem>
                      <SelectItem value="revoke">Revoke</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="All Statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="success">Success</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            {isLoadingLogs ? (
              <div className="flex h-[300px] items-center justify-center">
                <Loading size={32} text="Loading credential logs..." />
              </div>
            ) : errorLogs ? (
              <div className="p-6">
                <ApiErrorMessage 
                  error={errorLogs} 
                  onRetry={handleRetryCredentialLogs}
                />
              </div>
            ) : (
              <>
                <div className="relative overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs uppercase bg-muted/50">
                      <tr>
                        <th scope="col" className="px-6 py-3 whitespace-nowrap">
                          Operation
                        </th>
                        <th scope="col" className="px-6 py-3 whitespace-nowrap">
                          Credential Type
                        </th>
                        <th scope="col" className="px-6 py-3 whitespace-nowrap">
                          Wallet ID
                        </th>
                        <th scope="col" className="px-6 py-3 whitespace-nowrap">
                          User ID
                        </th>
                        <th scope="col" className="px-6 py-3 whitespace-nowrap">
                          Timestamp
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
                      {filteredLogs && filteredLogs.length > 0 ? (
                        filteredLogs.map(log => (
                          <tr key={log.id} className="border-b hover:bg-muted/50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              {getOperationBadge(log.operation)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {log.credential_type_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="font-mono text-xs">{log.wallet_id}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="font-mono text-xs">{log.user_id}</span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {formatDateTime(log.timestamp)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {getStatusBadge(log.status)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <Link href={`/dashboard/credentials/logs/${log.id}`}>
                                <Button variant="ghost" size="sm">View Details</Button>
                              </Link>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="px-6 py-8 text-center text-muted-foreground">
                            No credential operations found matching your criteria.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                {filteredLogs && filteredLogs.length > 0 && (
                  <div className="flex items-center justify-between px-6 py-4">
                    <div className="text-sm text-muted-foreground">
                      Showing {filteredLogs.length} results
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleRetryCredentialLogs}
                    >
                      Refresh
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
