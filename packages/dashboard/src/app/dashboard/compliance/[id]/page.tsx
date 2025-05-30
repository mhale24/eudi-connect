"use client"

import { useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs as _Tabs, TabsContent as _TabsContent, TabsList as _TabsList, TabsTrigger as _TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { ComplianceIcon } from "@/components/ui/icons"

// Result type definition
interface Requirement {
  id: string;
  code: string;
  name: string;
  category: string;
  level: string;
  description: string;
  legal_reference?: string;
}

interface Result {
  id: string;
  requirement: Requirement;
  status: string;
  message: string;
  details: Record<string, unknown>;
  remediation_steps?: string;
  execution_time_ms: number;
  executed_at: string;
}

// Mock scan result data
const mockScan = {
  id: "scan-1",
  name: "Mobile Wallet v2.1",
  wallet_name: "EU Mobile Wallet",
  wallet_version: "2.1.5",
  wallet_provider: "Digital Identity Labs",
  status: "completed",
  created_at: "2025-05-26T15:30:00Z",
  started_at: "2025-05-26T15:30:05Z",
  completed_at: "2025-05-26T15:32:38Z",
  total_requirements: 56,
  passed_requirements: 52,
  failed_requirements: 1,
  warning_requirements: 2,
  manual_check_requirements: 1,
  compliance_score: 92.8,
  description: "Compliance scan for EU Mobile Wallet v2.1.5 implementation against eIDAS 2.0 requirements.",
  config: {
    category_filter: null,
    level_filter: null,
    timestamp: "2025-05-26T15:30:00Z"
  }
}

// Mock detailed results
const mockResults = [
  {
    id: "result-1",
    requirement: {
      id: "req-1",
      code: "SEC-001",
      name: "Secure Communication Channels",
      category: "security",
      level: "mandatory",
      description: "Wallet must establish secure channels for communication using TLS 1.3 or higher.",
      legal_reference: "eIDAS 2.0 Article 6a(4)"
    },
    status: "pass",
    message: "TLS 1.3 successfully detected",
    details: {
      detected_tls_version: "1.3",
      cipher_suites: ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"],
      certificate_valid: true
    },
    execution_time_ms: 245,
    executed_at: "2025-05-26T15:30:12Z"
  },
  {
    id: "result-2",
    requirement: {
      id: "req-2",
      code: "SEC-002",
      name: "Cryptographic Algorithm Support",
      category: "security",
      level: "mandatory",
      description: "Wallet must support specified cryptographic algorithms for signing operations.",
      legal_reference: "eIDAS 2.0 Article 6a(4)"
    },
    status: "pass",
    message: "All required algorithms supported",
    details: {
      supported_algorithms: ["ES256", "EdDSA", "RS256"],
      required_algorithms: ["ES256", "EdDSA"]
    },
    execution_time_ms: 178,
    executed_at: "2025-05-26T15:30:15Z"
  },
  {
    id: "result-3",
    requirement: {
      id: "req-3",
      code: "PRV-001",
      name: "Data Minimization",
      category: "privacy",
      level: "mandatory",
      description: "Wallet must implement data minimization principles and only request necessary data.",
      legal_reference: "eIDAS 2.0 Article 6a(4)(e), GDPR Article 5(1)(c)"
    },
    status: "pass",
    message: "Data minimization principles implemented correctly",
    details: {
      selective_disclosure: true,
      purpose_limitation: true,
      data_retention_policy: true
    },
    execution_time_ms: 310,
    executed_at: "2025-05-26T15:30:19Z"
  },
  {
    id: "result-4",
    requirement: {
      id: "req-4",
      code: "INT-002",
      name: "OpenID for Verifiable Presentations Support",
      category: "interoperability",
      level: "mandatory",
      description: "Wallet must support OpenID for Verifiable Presentations protocol.",
      legal_reference: "eIDAS 2.0 Article 6a(4)(c)"
    },
    status: "warning",
    message: "OpenID4VP partially implemented, missing VP token response type",
    details: {
      authorization_endpoint: true,
      token_endpoint: true,
      presentation_endpoint: true,
      vp_token_type: false,
      recommended_fix: "Implement VP token type according to OpenID4VP specification section 6.3.1"
    },
    remediation_steps: "Update the OpenID configuration to include VP token type support according to the OpenID4VP specification.",
    execution_time_ms: 289,
    executed_at: "2025-05-26T15:30:25Z"
  },
  {
    id: "result-5",
    requirement: {
      id: "req-5",
      code: "SEC-012",
      name: "Key Storage Security",
      category: "security",
      level: "mandatory",
      description: "Cryptographic keys must be securely stored, preferably in hardware-backed secure elements.",
      legal_reference: "eIDAS 2.0 Article 6a(4)"
    },
    status: "fail",
    message: "Software-based key storage detected without additional protection",
    details: {
      key_storage_type: "software",
      hardware_backed: false,
      additional_protection: false,
      recommendation: "Implement hardware-backed key storage or additional software protection measures like white-box cryptography"
    },
    remediation_steps: "Upgrade the key storage mechanism to use platform-specific secure storage options like Android Keystore or iOS Secure Enclave.",
    execution_time_ms: 267,
    executed_at: "2025-05-26T15:30:31Z"
  },
  {
    id: "result-6",
    requirement: {
      id: "req-6",
      code: "USA-001",
      name: "User Interface Accessibility",
      category: "usability",
      level: "mandatory",
      description: "Wallet interface must be accessible according to WCAG 2.1 AA standards.",
      legal_reference: "eIDAS 2.0 Article 6a(4)(d)"
    },
    status: "manual_check_required",
    message: "Manual accessibility audit required",
    details: {
      automated_checks: {
        color_contrast: true,
        text_alternatives: true,
        keyboard_navigation: "unknown"
      },
      manual_audit_guide: "https://www.w3.org/WAI/WCAG21/quickref/"
    },
    execution_time_ms: 195,
    executed_at: "2025-05-26T15:30:36Z"
  }
]

// Result status colors
function getStatusColor(status: string) {
  switch (status) {
    case "pass":
      return "bg-green-500"
    case "warning":
      return "bg-yellow-500"
    case "fail":
      return "bg-red-500"
    case "manual_check_required":
      return "bg-blue-500"
    case "not_applicable":
      return "bg-gray-500"
    default:
      return "bg-gray-500"
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "pass":
      return <Badge variant="default" className="capitalize">Pass</Badge>
    case "warning":
      return <Badge variant="secondary" className="bg-yellow-500 text-white capitalize">Warning</Badge>
    case "fail":
      return <Badge variant="destructive" className="capitalize">Fail</Badge>
    case "manual_check_required":
      return <Badge variant="secondary" className="bg-blue-500 text-white capitalize">Manual Check</Badge>
    case "not_applicable":
      return <Badge variant="outline" className="capitalize">N/A</Badge>
    default:
      return <Badge variant="outline" className="capitalize">{status}</Badge>
  }
}

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric"
  })
}

function formatDuration(startDate: string, endDate: string) {
  const start = new Date(startDate).getTime()
  const end = new Date(endDate).getTime()
  const durationMs = end - start
  
  // Format as minutes:seconds.milliseconds
  const minutes = Math.floor(durationMs / 60000)
  const seconds = Math.floor((durationMs % 60000) / 1000)
  const ms = durationMs % 1000
  
  return `${minutes}:${seconds.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
}

// Filter functions for results
function filterResults(results: Result[], filter: string) {
  if (filter === "all") return results;
  return results.filter(result => result.status === filter);
}

export default function ScanDetailPage() {
  const params = useParams()
  const scanId = params.id
  const [statusFilter, setStatusFilter] = useState("all")
  
  // In a real implementation, we would fetch the scan and results based on the ID
  const scan = mockScan
  const results = filterResults(mockResults, statusFilter === "all" ? "all" : statusFilter)
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-bold tracking-tight">{scan.name}</h1>
          <p className="text-muted-foreground">
            Scan ID: {scanId}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline">
            Export PDF
          </Button>
          <Link href="/dashboard/compliance">
            <Button variant="secondary">
              Back to Scans
            </Button>
          </Link>
          <Button>
            <ComplianceIcon className="mr-2 h-4 w-4" />
            Run Again
          </Button>
        </div>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Wallet Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Name:</dt>
                <dd className="font-medium">{scan.wallet_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Version:</dt>
                <dd className="font-medium">{scan.wallet_version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Provider:</dt>
                <dd className="font-medium">{scan.wallet_provider}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Scan Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Started:</dt>
                <dd className="font-medium">{formatDateTime(scan.started_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Completed:</dt>
                <dd className="font-medium">{formatDateTime(scan.completed_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Duration:</dt>
                <dd className="font-medium">{formatDuration(scan.started_at, scan.completed_at)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Compliance Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center gap-2">
              <div className="text-4xl font-bold">
                {scan.compliance_score}%
              </div>
              <Progress value={scan.compliance_score} className="h-2 w-full" />
              <div className="text-xs text-muted-foreground">
                {scan.passed_requirements} of {scan.total_requirements} requirements passed
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Results Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span className="text-muted-foreground">Pass:</span>
                </dt>
                <dd className="font-medium">{scan.passed_requirements}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-yellow-500" />
                  <span className="text-muted-foreground">Warning:</span>
                </dt>
                <dd className="font-medium">{scan.warning_requirements}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-red-500" />
                  <span className="text-muted-foreground">Fail:</span>
                </dt>
                <dd className="font-medium">{scan.failed_requirements}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                  <span className="text-muted-foreground">Manual Check:</span>
                </dt>
                <dd className="font-medium">{scan.manual_check_requirements}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Detailed Results</CardTitle>
          <CardDescription>
            Individual requirement validation results for this compliance scan.
          </CardDescription>
          <div className="flex items-center gap-2 pt-4">
            <Button 
              variant={statusFilter === "all" ? "default" : "outline"} 
              size="sm"
              onClick={() => setStatusFilter("all")}
            >
              All ({mockResults.length})
            </Button>
            <Button 
              variant={statusFilter === "pass" ? "default" : "outline"} 
              size="sm"
              onClick={() => setStatusFilter("pass")}
              className="border-green-200 text-green-700 hover:text-green-700 hover:bg-green-50"
            >
              Pass ({mockResults.filter(r => r.status === "pass").length})
            </Button>
            <Button 
              variant={statusFilter === "warning" ? "default" : "outline"} 
              size="sm"
              onClick={() => setStatusFilter("warning")}
              className="border-yellow-200 text-yellow-700 hover:text-yellow-700 hover:bg-yellow-50"
            >
              Warning ({mockResults.filter(r => r.status === "warning").length})
            </Button>
            <Button 
              variant={statusFilter === "fail" ? "default" : "outline"} 
              size="sm"
              onClick={() => setStatusFilter("fail")}
              className="border-red-200 text-red-700 hover:text-red-700 hover:bg-red-50"
            >
              Fail ({mockResults.filter(r => r.status === "fail").length})
            </Button>
            <Button 
              variant={statusFilter === "manual_check_required" ? "default" : "outline"} 
              size="sm"
              onClick={() => setStatusFilter("manual_check_required")}
              className="border-blue-200 text-blue-700 hover:text-blue-700 hover:bg-blue-50"
            >
              Manual ({mockResults.filter(r => r.status === "manual_check_required").length})
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {results.map((result) => (
              <Card key={result['id']} className={
                result.status === "fail" ? "border-red-200" :
                result.status === "warning" ? "border-yellow-200" :
                result.status === "manual_check_required" ? "border-blue-200" :
                ""
              }>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`h-3 w-3 rounded-full ${getStatusColor(result.status)}`} />
                      <CardTitle className="text-base font-semibold">
                        {result.requirement.code}: {result.requirement.name}
                      </CardTitle>
                    </div>
                    {getStatusBadge(result.status)}
                  </div>
                  <CardDescription>
                    {result.requirement.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium">Result</h4>
                      <p className="text-sm text-muted-foreground">{result.message}</p>
                    </div>
                    
                    {result.status === "fail" && result.remediation_steps && (
                      <div className="rounded-md bg-red-50 p-4">
                        <h4 className="text-sm font-medium text-red-800">Remediation Steps</h4>
                        <p className="text-sm text-red-700">{result.remediation_steps}</p>
                      </div>
                    )}
                    
                    {result.status === "warning" && result.remediation_steps && (
                      <div className="rounded-md bg-yellow-50 p-4">
                        <h4 className="text-sm font-medium text-yellow-800">Recommendations</h4>
                        <p className="text-sm text-yellow-700">{result.remediation_steps}</p>
                      </div>
                    )}
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-sm font-medium">Category</h4>
                        <Badge variant="outline" className="mt-1 capitalize">{result.requirement.category}</Badge>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium">Level</h4>
                        <Badge variant="outline" className="mt-1 capitalize">{result.requirement.level}</Badge>
                      </div>
                    </div>
                    
                    {result.requirement.legal_reference && (
                      <div>
                        <h4 className="text-sm font-medium">Legal Reference</h4>
                        <p className="text-sm text-muted-foreground">{result.requirement.legal_reference}</p>
                      </div>
                    )}
                    
                    <div>
                      <h4 className="text-sm font-medium">Execution Details</h4>
                      <div className="text-sm text-muted-foreground flex items-center gap-4 mt-1">
                        <span>Time: {result.execution_time_ms}ms</span>
                        <span>Date: {formatDateTime(result.executed_at)}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button variant="ghost" size="sm">View Technical Details</Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
