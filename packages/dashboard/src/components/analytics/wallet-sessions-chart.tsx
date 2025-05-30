"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

interface WalletSessionsChartProps {
  timeRange: string
}

// Mock data for wallet sessions
const mockSessionsData = {
  "7d": [
    { date: "May 21", active: 68, new: 15, completed: 12 },
    { date: "May 22", active: 72, new: 18, completed: 14 },
    { date: "May 23", active: 75, new: 16, completed: 13 },
    { date: "May 24", active: 81, new: 21, completed: 15 },
    { date: "May 25", active: 84, new: 17, completed: 14 },
    { date: "May 26", active: 87, new: 19, completed: 16 },
    { date: "May 27", active: 84, new: 14, completed: 17 }
  ],
  "30d": [
    { date: "Apr 28", active: 42, new: 8, completed: 6 },
    { date: "May 1", active: 48, new: 12, completed: 8 },
    { date: "May 4", active: 53, new: 15, completed: 10 },
    { date: "May 7", active: 59, new: 14, completed: 12 },
    { date: "May 10", active: 64, new: 16, completed: 11 },
    { date: "May 13", active: 68, new: 15, completed: 13 },
    { date: "May 16", active: 73, new: 18, completed: 14 },
    { date: "May 19", active: 78, new: 17, completed: 15 },
    { date: "May 22", active: 72, new: 18, completed: 14 },
    { date: "May 25", active: 84, new: 17, completed: 14 },
    { date: "May 27", active: 84, new: 14, completed: 17 }
  ]
}

// Mock data for wallet provider distribution
const mockWalletProviderData = [
  { name: "EU Wallet Reference", sessions: 542, percentage: 42 },
  { name: "DigiWallet Pro", sessions: 328, percentage: 26 },
  { name: "NationalID Mobile", sessions: 195, percentage: 15 },
  { name: "PrivateID Wallet", sessions: 84, percentage: 7 },
  { name: "Other", sessions: 129, percentage: 10 }
]

export function WalletSessionsChart({ timeRange }: WalletSessionsChartProps) {
  const data = mockSessionsData[timeRange as keyof typeof mockSessionsData] || mockSessionsData["30d"]
  
  return (
    <div className="grid grid-cols-1 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Wallet Sessions Overview</CardTitle>
          <CardDescription>
            Active, new, and completed wallet sessions over time
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="active" 
                name="Active Sessions" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="new" 
                name="New Sessions" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="completed" 
                name="Completed Sessions" 
                stroke="#f59e0b" 
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Wallet Provider Distribution</CardTitle>
            <CardDescription>
              Active sessions by wallet provider
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockWalletProviderData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} />
                <Tooltip 
                  formatter={(value, name) => [`${value} sessions`, name]}
                  labelFormatter={() => ''}
                />
                <Bar dataKey="sessions" fill="#3b82f6" name="Active Sessions" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Session Performance</CardTitle>
            <CardDescription>
              Key metrics for wallet sessions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6 py-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Average Session Duration</div>
                  <div className="text-xl font-bold">4m 32s</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: "45%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>0m</span>
                  <span>Target: 3m</span>
                  <span>10m</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Session Success Rate</div>
                  <div className="text-xl font-bold">96.8%</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "96.8%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>80%</span>
                  <span>Target: 95%</span>
                  <span>100%</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Connection Failure Rate</div>
                  <div className="text-xl font-bold">2.3%</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: "2.3%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>0%</span>
                  <span>Target: &lt;5%</span>
                  <span>10%</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">User Abandonment Rate</div>
                  <div className="text-xl font-bold">3.5%</div>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500 rounded-full" style={{ width: "3.5%" }}></div>
                </div>
                <div className="flex justify-between text-xs mt-1">
                  <span>0%</span>
                  <span>Target: &lt;7%</span>
                  <span>15%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
