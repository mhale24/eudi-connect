"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ComplianceIcon } from "@/components/ui/icons"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { toast } from "@/components/ui/use-toast"
import { useApi } from "@/hooks/use-api"
import { complianceApi } from "@/lib/api-client"
import { Loading } from "@/components/ui/loading"
import { ApiErrorMessage } from "@/components/ui/api-error"
import { BarChart } from "@/components/ui/charts"
import { ApiDataWrapper } from "@/components/api-data-wrapper"
import { ErrorBoundary } from "@/components/error-boundary"

// Define types for our API data structures
interface ComplianceScan {
  id: string;
  scan_date: string;
  status: 'completed' | 'in_progress' | 'failed';
  compliance_score: number;
  issues_count: number;
  critical_issues_count: number;
  merchant_id: string;
  scan_type: string;
  wallet_name?: string;
  wallet_version?: string;
  wallet_provider?: string;
  created_at?: string;
  details?: any;
}

interface ComplianceRequirement {
  id: string;
  code: string;
  category: string;
  name: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  level: 'mandatory' | 'recommended' | 'optional';
  regulation: string;
  test_description?: string;
}

// Mock data for development/fallback
const fallbackScans: ComplianceScan[] = [
  {
    id: "scan-1",
    scan_date: "2025-05-26T15:30:00Z",
    status: "completed",
    compliance_score: 92.8,
    issues_count: 4,
    critical_issues_count: 1,
    merchant_id: "EU Mobile Wallet",
    scan_type: "Mobile",
    wallet_name: "EU Mobile Wallet",
    wallet_version: "2.1.5",
    wallet_provider: "Digital Identity Labs",
    created_at: "2025-05-26T15:30:00Z"
  },
  {
    id: "scan-2",
    scan_date: "2025-05-24T12:15:00Z",
    status: "completed",
    compliance_score: 85.7,
    issues_count: 8,
    critical_issues_count: 3,
    merchant_id: "EU Web Wallet",
    scan_type: "Web",
    wallet_name: "EU Web Wallet",
    wallet_version: "1.8.3",
    wallet_provider: "Digital Identity Labs",
    created_at: "2025-05-24T12:15:00Z"
  }
];

const fallbackRequirements: ComplianceRequirement[] = [
  { 
    id: "req-1", 
    code: "SEC-001", 
    name: "Secure Communication Channels", 
    category: "security", 
    level: "mandatory",
    severity: "critical",
    regulation: "eIDAS 2.0",
    description: "Wallet must establish secure channels for communication using TLS 1.3 or higher."
  },
  { 
    id: "req-2", 
    code: "SEC-002", 
    name: "Cryptographic Algorithm Support", 
    category: "security", 
    level: "mandatory",
    severity: "high",
    regulation: "eIDAS 2.0",
    description: "Wallet must support specified cryptographic algorithms for signing operations."
  }
];

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  })
}

function formatDateLong(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric"
  })
}

function formatDateShort(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  })
}

function getStatusColor(status: string) {
  switch (status) {
    case "completed":
      return "bg-green-500"
    case "in_progress":
      return "bg-blue-500"
    case "pending":
      return "bg-yellow-500"
    case "failed":
      return "bg-red-500"
    default:
      return "bg-gray-500"
  }
}

function getScoreColor(score: number) {
  if (score >= 90) return "text-green-600"
  if (score >= 70) return "text-yellow-600"
  return "text-red-600"
}

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState("scans")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [scanName, setScanName] = useState("")
  const [scanType, setScanType] = useState("web")
  const [activeScan, setActiveScan] = useState<ComplianceScan | null>(null)
  const [chartData, setChartData] = useState<Array<{name: string, value: number}>>([])
  
  // API hooks for scans
  const { 
    data: scans, 
    isLoading: isLoadingScans, 
    error: scansError, 
    request: requestScans,
    refetch: refetchScans
  } = useApi<ComplianceScan[]>([])

  // API hooks for requirements
  const { 
    data: requirements, 
    isLoading: isLoadingRequirements, 
    error: requirementsError, 
    request: requestRequirements,
    refetch: refetchRequirements
  } = useApi<ComplianceRequirement[]>([])
  
  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Request scans data
        const scansData = await requestScans(async () => await complianceApi.getScans())
        
        // Request requirements data
        await requestRequirements(async () => await complianceApi.getRequirements())
        
        // If we have scans, set the latest as active and prepare chart data
        if (scansData && scansData.length > 0) {
          setActiveScan(scansData[0])
          prepareChartData(scansData)
        }
      } catch (err) {
        console.error("Error fetching compliance data:", err)
      }
    }
    
    fetchData()
  }, [])
  
  // Prepare chart data from scan history
  const prepareChartData = (scanData: ComplianceScan[]) => {
    const chartDataPoints = scanData
      .slice(0, 6) // Get last 6 scans
      .reverse() // Display oldest to newest
      .map(scan => ({
        name: formatDateShort(scan.scan_date),
        value: scan.compliance_score,
      }))
    
    setChartData(chartDataPoints)
  }
  
  // Get latest scan for the metrics
  const latestScan = scans && scans.length > 0 ? scans[0] : null
  
  // Handler for new scan creation
  const handleCreateScan = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!scanName) {
      toast({
        title: "Validation Error",
        description: "Please enter a scan name",
        variant: "destructive"
      })
      return
    }
    
    try {
      // Create new scan - in a real app this would call the API
      // const newScan = await requestScans('/api/compliance/scans/create', { method: 'POST', body: { name: scanName, type: scanType } })
      
      toast({
        title: "Scan Initiated",
        description: `${scanName} scan has been started. You'll be notified when it completes.`
      })
      
      // Close dialog and reset form
      setIsCreateDialogOpen(false)
      setScanName("")
      setScanType("web")
      
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create compliance scan",
        variant: "destructive"
      })
    }
  }
  
  // Custom empty states for better UX
  const emptyScanComponent = (
    <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed">
      <div className="text-center">
        <h3 className="text-lg font-medium">No compliance scans available</h3>
        <p className="text-sm text-muted-foreground">Run your first compliance scan to see results here.</p>
        <Button className="mt-4" onClick={() => setIsCreateDialogOpen(true)}>
          Create Scan
        </Button>
      </div>
    </div>
  )
  
  const emptyRequirementsComponent = (
    <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed">
      <div className="text-center">
        <h3 className="text-lg font-medium">No requirements available</h3>
        <p className="text-sm text-muted-foreground">Requirements will appear once loaded from the API.</p>
      </div>
    </div>
  )

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Compliance</h1>
          <p className="text-muted-foreground">Monitor your wallet's compliance with eIDAS 2.0 requirements</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <ComplianceIcon className="mr-2 h-4 w-4" />
              Run Compliance Scan
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create Compliance Scan</DialogTitle>
              <DialogDescription>
                Configure and run a new compliance scan for your wallet implementation.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateScan}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="name" className="text-right">
                    Name
                  </Label>
                  <Input
                    id="name"
                    value={scanName}
                    onChange={(e) => setScanName(e.target.value)}
                    className="col-span-3"
                    placeholder="My Wallet Scan"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="scan-type" className="text-right">
                    Type
                  </Label>
                  <Select
                    value={scanType}
                    onValueChange={(value) => setScanType(value)}
                  >
                    <SelectTrigger className="col-span-3" id="scan-type">
                      <SelectValue placeholder="Select scan type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="web">Web Wallet</SelectItem>
                      <SelectItem value="mobile">Mobile Wallet</SelectItem>
                      <SelectItem value="hardware">Hardware Wallet</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Start Scan</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="scans" onValueChange={setActiveTab} value={activeTab}>
        <TabsList>
          <TabsTrigger value="scans">Scans</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
        </TabsList>
        
        <TabsContent value="scans" className="space-y-4">
          <div className="flex justify-between">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Compliance Scans</h2>
              <p className="text-muted-foreground">
                Monitor your wallet's compliance with eIDAS 2.0 requirements
              </p>
            </div>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <ComplianceIcon className="mr-2 h-4 w-4" />
              New Scan
            </Button>
          </div>
          
          <ApiDataWrapper
            data={scans}
            isLoading={isLoadingScans}
            error={scansError}
            onRetry={() => refetchScans(async () => await complianceApi.getScans())}
            emptyComponent={emptyScanComponent}
          >
            {(scanData) => (
              <div>
                <div className="grid gap-6 md:grid-cols-3">
                  <Card className="col-span-1">
                    <CardHeader>
                      <CardTitle>Compliance Score</CardTitle>
                      <CardDescription>
                        Latest scan results
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="text-center">
                      {latestScan ? (
                        <>
                          <div className={`text-5xl font-bold mb-2 ${getScoreColor(latestScan.compliance_score)}`}>
                            {latestScan.compliance_score}%
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Last updated: {formatDateLong(latestScan.scan_date)}
                          </p>
                        </>
                      ) : (
                        <div className="p-6">
                          <p className="text-muted-foreground">No scan data available</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                  
                  <Card className="col-span-2">
                    <CardHeader>
                      <CardTitle>Compliance Trend</CardTitle>
                      <CardDescription>
                        Historical compliance scores
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {chartData.length > 0 ? (
                        <div className="h-[200px]">
                          <BarChart
                            data={chartData}
                            xAxisDataKey="name"
                            yAxisDataKey="value"
                          />
                        </div>
                      ) : (
                        <div className="flex h-[200px] items-center justify-center">
                          <p className="text-muted-foreground">Not enough historical data</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
                
                <div className="mt-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Scan History</CardTitle>
                      <CardDescription>
                        View and manage your compliance scans
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="rounded-md border">
                        <div className="flex items-center p-4 bg-muted/50">
                          <div className="flex flex-1 items-center space-x-2">
                            <div className="w-[150px] font-medium">Scan Date</div>
                            <div className="w-[200px] font-medium">Wallet</div>
                            <div className="w-[100px] font-medium">Status</div>
                            <div className="w-[100px] font-medium">Score</div>
                          </div>
                          <div className="flex w-[100px] items-center justify-center font-medium">
                            Actions
                          </div>
                        </div>
                        <div className="divide-y">
                          {scanData.map((scan) => (
                            <div key={scan.id} className="flex items-center p-4 hover:bg-muted/30 cursor-pointer" onClick={() => setActiveScan(scan)}>
                              <div className="flex flex-1 items-center space-x-2">
                                <div className="w-[150px]">
                                  {formatDate(scan.scan_date)}
                                </div>
                                <div className="w-[200px]">
                                  <div className="font-medium">{scan.wallet_name || scan.merchant_id}</div>
                                  <div className="text-sm text-muted-foreground">
                                    Version: {scan.wallet_version || 'Unknown'}
                                  </div>
                                </div>
                                <div className="w-[100px]">
                                  <Badge className="capitalize" variant={scan.status === 'completed' ? 'default' : scan.status === 'in_progress' ? 'outline' : 'destructive'}>
                                    {scan.status}
                                  </Badge>
                                </div>
                                <div className={`w-[100px] font-medium ${getScoreColor(scan.compliance_score)}`}>
                                  {scan.compliance_score}%
                                </div>
                              </div>
                              <div className="flex w-[100px] items-center justify-center">
                                <Link href={`/dashboard/compliance/${scan.id}`}>
                                  <Button variant="ghost" size="sm">View</Button>
                                </Link>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                
                {activeScan && (
                  <div className="mt-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Scan Details</CardTitle>
                        <CardDescription>
                          {activeScan.wallet_name || activeScan.merchant_id} - {activeScan.wallet_version || 'Unknown version'}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-4 md:grid-cols-3">
                          <div className="space-y-2">
                            <div className="text-sm font-medium">Status</div>
                            <Badge className="capitalize" variant={activeScan.status === 'completed' ? 'default' : activeScan.status === 'in_progress' ? 'outline' : 'destructive'}>
                              {activeScan.status}
                            </Badge>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="text-sm font-medium">Score</div>
                            <div className={`text-xl font-bold ${getScoreColor(activeScan.compliance_score)}`}>
                              {activeScan.compliance_score}%
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="text-sm font-medium">Issues</div>
                            <div className="flex space-x-4">
                              <div>
                                <span className="text-red-500 font-bold">{activeScan.critical_issues_count}</span> critical
                              </div>
                              <div>
                                <span className="text-yellow-500 font-bold">{activeScan.issues_count - activeScan.critical_issues_count}</span> other
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="mt-6 flex justify-end">
                          <Link href={`/dashboard/compliance/${activeScan.id}`}>
                            <Button>View Detailed Report</Button>
                          </Link>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </div>
            )}
          </ApiDataWrapper>
        </TabsContent>
        
        <TabsContent value="requirements" className="space-y-4">
          <ApiDataWrapper
            data={requirements}
            isLoading={isLoadingRequirements}
            error={requirementsError}
            onRetry={() => refetchRequirements(async () => await complianceApi.getRequirements())}
            emptyComponent={emptyRequirementsComponent}
          >
            {(requirementsData) => (
              <div className="rounded-md border">
                <div className="flex items-center p-4 bg-muted/50">
                  <div className="flex flex-1 items-center space-x-2">
                    <div className="w-[120px] font-medium">Code</div>
                    <div className="w-[250px] font-medium">Name</div>
                    <div className="w-[150px] font-medium">Category</div>
                    <div className="w-[150px] font-medium">Level</div>
                  </div>
                  <div className="flex w-[100px] items-center justify-center font-medium">
                    Actions
                  </div>
                </div>
                <div className="divide-y">
                  {requirementsData.map((req) => (
                    <div key={req.id} className="flex items-center p-4 hover:bg-muted/30">
                      <div className="flex flex-1 items-center space-x-2">
                        <div className="w-[120px] font-mono text-sm">
                          {req.code}
                        </div>
                        <div className="w-[250px]">
                          <div className="font-medium">{req.name}</div>
                          <div className="text-sm text-muted-foreground truncate max-w-[240px]">
                            {req.description}
                          </div>
                        </div>
                        <div className="w-[150px]">
                          <Badge variant={req.category === "security" ? "destructive" : req.category === "privacy" ? "outline" : "secondary"} className="capitalize">
                            {req.category}
                          </Badge>
                        </div>
                        <div className="w-[150px]">
                          <Badge variant={req.level === "mandatory" ? "default" : req.level === "recommended" ? "secondary" : "outline"} className="capitalize">
                            {req.level}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex w-[100px] items-center justify-center">
                        <Link href={`/dashboard/compliance/requirements/${req.id}`}>
                          <Button variant="ghost" size="sm">Details</Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ApiDataWrapper>
        </TabsContent>
      </Tabs>
    </div>
  )
}
