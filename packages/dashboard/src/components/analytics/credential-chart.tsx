"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

interface CredentialChartProps {
  timeRange: string
}

// Mock data for credential operations
const mockCredentialData = {
  "7d": [
    { date: "May 21", issued: 12, verified: 35, revoked: 1 },
    { date: "May 22", issued: 15, verified: 42, revoked: 2 },
    { date: "May 23", issued: 18, verified: 53, revoked: 0 },
    { date: "May 24", issued: 22, verified: 61, revoked: 1 },
    { date: "May 25", issued: 19, verified: 57, revoked: 0 },
    { date: "May 26", issued: 21, verified: 63, revoked: 2 },
    { date: "May 27", issued: 17, verified: 41, revoked: 1 }
  ],
  "30d": [
    { date: "Apr 28", issued: 14, verified: 38, revoked: 1 },
    { date: "May 1", issued: 16, verified: 45, revoked: 0 },
    { date: "May 4", issued: 19, verified: 52, revoked: 2 },
    { date: "May 7", issued: 21, verified: 58, revoked: 1 },
    { date: "May 10", issued: 18, verified: 49, revoked: 0 },
    { date: "May 13", issued: 23, verified: 62, revoked: 1 },
    { date: "May 16", issued: 20, verified: 55, revoked: 2 },
    { date: "May 19", issued: 22, verified: 60, revoked: 1 },
    { date: "May 22", issued: 15, verified: 42, revoked: 0 },
    { date: "May 25", issued: 19, verified: 57, revoked: 1 },
    { date: "May 27", issued: 17, verified: 41, revoked: 0 }
  ]
}

// Extended data for 90d and 1y is not provided to keep the component simple
// In a real application, you would fetch this data from your API

export function CredentialChart({ timeRange }: CredentialChartProps) {
  const data = mockCredentialData[timeRange as keyof typeof mockCredentialData] || mockCredentialData["30d"]
  
  return (
    <div className="grid grid-cols-1 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Credential Operations</CardTitle>
          <CardDescription>
            Number of credentials issued, verified, and revoked over time
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorIssued" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2} />
                </linearGradient>
                <linearGradient id="colorVerified" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.2} />
                </linearGradient>
                <linearGradient id="colorRevoked" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.2} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="issued" 
                name="Issued" 
                stroke="#3b82f6" 
                fillOpacity={1} 
                fill="url(#colorIssued)" 
              />
              <Area 
                type="monotone" 
                dataKey="verified" 
                name="Verified" 
                stroke="#10b981" 
                fillOpacity={1} 
                fill="url(#colorVerified)" 
              />
              <Area 
                type="monotone" 
                dataKey="revoked" 
                name="Revoked" 
                stroke="#ef4444" 
                fillOpacity={1} 
                fill="url(#colorRevoked)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Credential Type Distribution</CardTitle>
            <CardDescription>
              Distribution of operations by credential type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">EU Digital Identity</span>
                  <span className="text-sm font-medium">42%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: "42%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Digital Driving License</span>
                  <span className="text-sm font-medium">28%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "28%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Professional Qualification</span>
                  <span className="text-sm font-medium">15%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: "15%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Healthcare ID</span>
                  <span className="text-sm font-medium">10%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500 rounded-full" style={{ width: "10%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Other</span>
                  <span className="text-sm font-medium">5%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-500 rounded-full" style={{ width: "5%" }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Verification Results</CardTitle>
            <CardDescription>
              Outcome of credential verification attempts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Valid</span>
                  <span className="text-sm font-medium">92.4%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "92.4%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Expired</span>
                  <span className="text-sm font-medium">3.8%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500 rounded-full" style={{ width: "3.8%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Revoked</span>
                  <span className="text-sm font-medium">2.1%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: "2.1%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Invalid Signature</span>
                  <span className="text-sm font-medium">1.2%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-red-600 rounded-full" style={{ width: "1.2%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Other Errors</span>
                  <span className="text-sm font-medium">0.5%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-500 rounded-full" style={{ width: "0.5%" }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
