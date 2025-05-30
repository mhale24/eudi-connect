"use client"

import { Card, CardContent } from "@/components/ui/card"
import { ArrowUp, ArrowDown } from "lucide-react"

interface OverviewMetricsProps {
  timeRange: string
}

// Mock data for overview metrics
const mockMetrics = {
  "7d": {
    credentials_issued: { value: 124, change: 8.5 },
    credentials_verified: { value: 352, change: 12.3 },
    active_wallets: { value: 87, change: 5.2 },
    compliance_score: { value: 93.5, change: 1.8 }
  },
  "30d": {
    credentials_issued: { value: 583, change: 15.2 },
    credentials_verified: { value: 1467, change: 23.8 },
    active_wallets: { value: 215, change: 18.7 },
    compliance_score: { value: 93.5, change: 2.5 }
  },
  "90d": {
    credentials_issued: { value: 1895, change: 42.1 },
    credentials_verified: { value: 4823, change: 36.5 },
    active_wallets: { value: 348, change: 28.3 },
    compliance_score: { value: 93.5, change: 4.2 }
  },
  "1y": {
    credentials_issued: { value: 7862, change: 124.3 },
    credentials_verified: { value: 19547, change: 96.8 },
    active_wallets: { value: 542, change: 85.3 },
    compliance_score: { value: 93.5, change: 15.7 }
  },
  "custom": {
    credentials_issued: { value: 583, change: 15.2 },
    credentials_verified: { value: 1467, change: 23.8 },
    active_wallets: { value: 215, change: 18.7 },
    compliance_score: { value: 93.5, change: 2.5 }
  }
}

export function OverviewMetrics({ timeRange }: OverviewMetricsProps) {
  const metrics = mockMetrics[timeRange as keyof typeof mockMetrics] || mockMetrics["30d"]
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Credentials Issued"
        value={metrics.credentials_issued.value}
        change={metrics.credentials_issued.change}
        format="number"
      />
      <MetricCard
        title="Credentials Verified"
        value={metrics.credentials_verified.value}
        change={metrics.credentials_verified.change}
        format="number"
      />
      <MetricCard
        title="Active Wallets"
        value={metrics.active_wallets.value}
        change={metrics.active_wallets.change}
        format="number"
      />
      <MetricCard
        title="Compliance Score"
        value={metrics.compliance_score.value}
        change={metrics.compliance_score.change}
        format="percentage"
      />
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: number
  change: number
  format: "number" | "percentage" | "currency"
}

function MetricCard({ title, value, change, format }: MetricCardProps) {
  const formattedValue = format === "percentage" 
    ? `${value}%` 
    : format === "currency" 
      ? `€${value.toLocaleString()}` 
      : value.toLocaleString()
  
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col space-y-1.5">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="flex items-end justify-between">
            <h2 className="text-3xl font-bold">{formattedValue}</h2>
            <div className={`flex items-center ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change >= 0 ? (
                <ArrowUp className="mr-1 h-4 w-4" />
              ) : (
                <ArrowDown className="mr-1 h-4 w-4" />
              )}
              <span className="text-sm font-medium">{Math.abs(change)}%</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
