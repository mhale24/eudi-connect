"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DateRangePicker } from "@/components/ui/date-range-picker"
import { OverviewMetrics } from "@/components/analytics/overview-metrics"
import { CredentialChart } from "@/components/analytics/credential-chart"
import { WalletSessionsChart } from "@/components/analytics/wallet-sessions-chart"
import { ComplianceSummary } from "@/components/analytics/compliance-summary"
import { GeographicDistribution } from "@/components/analytics/geographic-distribution"

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30d")
  const [dateRange, setDateRange] = useState({ from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), to: new Date() })
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Insights and metrics for your EUDI-Connect platform
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="1y">Last year</SelectItem>
                <SelectItem value="custom">Custom range</SelectItem>
              </SelectContent>
            </Select>
            
            {timeRange === "custom" && (
              <DateRangePicker 
                from={dateRange.from} 
                to={dateRange.to} 
                onSelect={range => range && setDateRange(range)} 
              />
            )}
          </div>
          <Button variant="outline">Export Report</Button>
        </div>
      </div>
      
      <OverviewMetrics timeRange={timeRange} />
      
      <Tabs defaultValue="credentials" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="credentials">Credentials</TabsTrigger>
          <TabsTrigger value="wallet-sessions">Wallet Sessions</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="geographic">Geographic</TabsTrigger>
        </TabsList>
        <TabsContent value="credentials" className="mt-6">
          <CredentialChart timeRange={timeRange} />
        </TabsContent>
        <TabsContent value="wallet-sessions" className="mt-6">
          <WalletSessionsChart timeRange={timeRange} />
        </TabsContent>
        <TabsContent value="compliance" className="mt-6">
          <ComplianceSummary timeRange={timeRange} />
        </TabsContent>
        <TabsContent value="geographic" className="mt-6">
          <GeographicDistribution timeRange={timeRange} />
        </TabsContent>
      </Tabs>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Recent Credential Operations</CardTitle>
            <CardDescription>
              Latest credential issuance, verification, and revocation operations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50">
                  <tr>
                    <th scope="col" className="px-6 py-3">Operation</th>
                    <th scope="col" className="px-6 py-3">Credential Type</th>
                    <th scope="col" className="px-6 py-3">Timestamp</th>
                    <th scope="col" className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">Issue</td>
                    <td className="px-6 py-4">EU Digital Identity</td>
                    <td className="px-6 py-4">May 27, 2025 15:42</td>
                    <td className="px-6 py-4 text-green-600">Success</td>
                  </tr>
                  <tr className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">Verify</td>
                    <td className="px-6 py-4">Digital Driving License</td>
                    <td className="px-6 py-4">May 27, 2025 15:30</td>
                    <td className="px-6 py-4 text-green-600">Success</td>
                  </tr>
                  <tr className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">Issue</td>
                    <td className="px-6 py-4">Professional Qualification</td>
                    <td className="px-6 py-4">May 27, 2025 15:15</td>
                    <td className="px-6 py-4 text-green-600">Success</td>
                  </tr>
                  <tr className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">Verify</td>
                    <td className="px-6 py-4">EU Digital Identity</td>
                    <td className="px-6 py-4">May 27, 2025 14:58</td>
                    <td className="px-6 py-4 text-red-600">Failed</td>
                  </tr>
                  <tr className="border-b hover:bg-muted/50">
                    <td className="px-6 py-4">Revoke</td>
                    <td className="px-6 py-4">Digital Driving License</td>
                    <td className="px-6 py-4">May 27, 2025 14:45</td>
                    <td className="px-6 py-4 text-green-600">Success</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>API Performance</CardTitle>
            <CardDescription>
              Response time and availability metrics.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Average Response Time</div>
                  <div className="text-xl font-bold">248ms</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "25%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>0ms</span>
                  <span>Target: 300ms</span>
                  <span>1000ms</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Uptime</div>
                  <div className="text-xl font-bold">99.98%</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "99.98%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>90%</span>
                  <span>SLA: 99.9%</span>
                  <span>100%</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Error Rate</div>
                  <div className="text-xl font-bold">0.12%</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "1.2%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>0%</span>
                  <span>Target: &lt;1%</span>
                  <span>10%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
