"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts"

interface ComplianceSummaryProps {
  timeRange: string
}

// Mock data for compliance status
const mockComplianceData = {
  status: [
    { name: "Pass", value: 52, color: "#10b981" },
    { name: "Warning", value: 2, color: "#f59e0b" },
    { name: "Fail", value: 1, color: "#ef4444" },
    { name: "Manual Check", value: 1, color: "#3b82f6" }
  ],
  categories: [
    { category: "Security", score: 95 },
    { category: "Privacy", score: 92 },
    { category: "Interoperability", score: 90 },
    { category: "Accessibility", score: 86 },
    { category: "Usability", score: 88 },
    { category: "Performance", score: 93 }
  ],
  history: [
    { date: "Jan 2025", score: 85 },
    { date: "Feb 2025", score: 87 },
    { date: "Mar 2025", score: 89 },
    { date: "Apr 2025", score: 91 },
    { date: "May 2025", score: 93.5 }
  ]
}

export function ComplianceSummary({ timeRange: _timeRange }: ComplianceSummaryProps) {
  return (
    <div className="grid grid-cols-1 gap-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Compliance Radar</CardTitle>
            <CardDescription>
              Compliance score by category against eIDAS 2.0 requirements
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mockComplianceData.categories}>
                <PolarGrid />
                <PolarAngleAxis dataKey="category" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar
                  name="Compliance Score"
                  dataKey="score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Requirement Status</CardTitle>
            <CardDescription>
              Status of eIDAS 2.0 compliance requirements
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <div className="h-full flex flex-col justify-center">
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={mockComplianceData.status}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {mockComplianceData.status.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-2">
                {mockComplianceData.status.map((entry, index) => (
                  <div key={index} className="flex items-center">
                    <div className="h-3 w-3 rounded-full mr-2" style={{ backgroundColor: entry.color }}></div>
                    <span className="text-sm">{entry.name}: {entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Compliance Findings</CardTitle>
          <CardDescription>
            Recent compliance scan results and findings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="border rounded-md">
              <div className="flex items-center justify-between border-b px-4 py-3">
                <div className="font-medium">Critical Findings</div>
                <div className="text-red-600 font-medium">1 Issue</div>
              </div>
              <div className="p-4">
                <div className="flex">
                  <div className="w-2 h-2 rounded-full bg-red-500 mt-2 mr-2"></div>
                  <div>
                    <h4 className="font-medium">SEC-012: Key Storage Security</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Software-based key storage detected without additional protection. Implement hardware-backed key storage or additional software protection measures.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="border rounded-md">
              <div className="flex items-center justify-between border-b px-4 py-3">
                <div className="font-medium">Warnings</div>
                <div className="text-yellow-600 font-medium">2 Issues</div>
              </div>
              <div className="p-4 space-y-4">
                <div className="flex">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2 mr-2"></div>
                  <div>
                    <h4 className="font-medium">INT-002: OpenID for Verifiable Presentations Support</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      OpenID4VP partially implemented, missing VP token response type. Update the OpenID configuration to include VP token type support.
                    </p>
                  </div>
                </div>
                <div className="flex">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2 mr-2"></div>
                  <div>
                    <h4 className="font-medium">PER-001: Response Time Requirements</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Wallet response time occasionally exceeds the recommended threshold of 500ms. Optimize wallet operations to improve response time.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
