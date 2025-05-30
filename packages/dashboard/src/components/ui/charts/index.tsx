"use client"

import React from "react"
import {
  Area,
  AreaChart as RechartsAreaChart,
  Bar as RechartsBar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Line as RechartsLine,
  LineChart as RechartsLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts"

import { cn } from "@/lib/utils"

// Sample data for demonstration
const demoData = [
  { name: "Jan", value: 100 },
  { name: "Feb", value: 150 },
  { name: "Mar", value: 180 },
  { name: "Apr", value: 120 },
  { name: "May", value: 200 },
  { name: "Jun", value: 250 },
  { name: "Jul", value: 280 },
  { name: "Aug", value: 300 },
  { name: "Sep", value: 260 },
  { name: "Oct", value: 220 },
  { name: "Nov", value: 190 },
  { name: "Dec", value: 230 },
]

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
  if (active && payload && payload.length > 0) {
    return (
      <div className="rounded-lg border bg-background p-2 shadow-sm">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-sm text-muted-foreground">
          Value: {payload[0]?.value || 0}
        </p>
      </div>
    )
  }

  return null
}

export interface ChartProps extends React.HTMLAttributes<HTMLDivElement> {
  data?: Array<Record<string, string | number>>
  xAxisDataKey?: string
  yAxisDataKey?: string
  showXAxis?: boolean
  showYAxis?: boolean
  showGrid?: boolean
  showTooltip?: boolean
  tooltipContent?: React.ReactNode
  showLegend?: boolean
}

export function LineChart({
  data = demoData,
  xAxisDataKey = "name",
  yAxisDataKey = "value",
  showXAxis = true,
  showYAxis = true,
  showGrid = true,
  showTooltip = true,
  tooltipContent,
  className,
  ...props
}: ChartProps) {
  return (
    <div className={cn("h-[300px] w-full", className)} {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart
          data={data}
          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />}
          {showXAxis && <XAxis dataKey={xAxisDataKey} stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showYAxis && <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showTooltip && <Tooltip content={tooltipContent || CustomTooltip as any} />}
          <RechartsLine
            type="monotone"
            dataKey={yAxisDataKey}
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, fill: "hsl(var(--primary))" }}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AreaChart({
  data = demoData,
  xAxisDataKey = "name",
  yAxisDataKey = "value",
  showXAxis = true,
  showYAxis = true,
  showGrid = true,
  showTooltip = true,
  tooltipContent,
  className,
  ...props
}: ChartProps) {
  return (
    <div className={cn("h-[300px] w-full", className)} {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsAreaChart
          data={data}
          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />}
          {showXAxis && <XAxis dataKey={xAxisDataKey} stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showYAxis && <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showTooltip && <Tooltip content={tooltipContent || CustomTooltip as any} />}
          <Area
            type="monotone"
            dataKey={yAxisDataKey}
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            fillOpacity={0.1}
            fill="hsl(var(--primary))"
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function BarChart({
  data = demoData,
  xAxisDataKey = "name",
  yAxisDataKey = "value",
  showXAxis = true,
  showYAxis = true,
  showGrid = true,
  showTooltip = true,
  tooltipContent,
  className,
  ...props
}: ChartProps) {
  return (
    <div className={cn("h-[300px] w-full", className)} {...props}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart
          data={data}
          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} vertical={false} />}
          {showXAxis && <XAxis dataKey={xAxisDataKey} stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showYAxis && <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />}
          {showTooltip && <Tooltip content={tooltipContent || CustomTooltip as any} />}
          <RechartsBar
            dataKey={yAxisDataKey}
            fill="hsl(var(--primary))"
            radius={[4, 4, 0, 0]}
            barSize={30}
          />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Export the components
export { Line } from "recharts"
export { Bar } from "recharts"
