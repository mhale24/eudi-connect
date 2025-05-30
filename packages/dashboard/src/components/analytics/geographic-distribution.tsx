"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface GeographicDistributionProps {
  timeRange: string
}

// Mock data for geographic distribution
const mockGeoData = [
  { country: "Germany", operations: 2458, growth: 23.5 },
  { country: "France", operations: 1872, growth: 18.7 },
  { country: "Italy", operations: 1453, growth: 15.2 },
  { country: "Spain", operations: 1128, growth: 12.8 },
  { country: "Netherlands", operations: 986, growth: 19.4 },
  { country: "Belgium", operations: 845, growth: 16.7 },
  { country: "Sweden", operations: 732, growth: 14.3 },
  { country: "Poland", operations: 625, growth: 21.6 },
  { country: "Austria", operations: 547, growth: 13.5 },
  { country: "Other EU", operations: 1678, growth: 17.9 }
]

export function GeographicDistribution({ timeRange: _timeRange }: GeographicDistributionProps) {
  return (
    <div className="grid grid-cols-1 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Geographic Distribution</CardTitle>
          <CardDescription>
            Credential operations by country
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={mockGeoData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              layout="vertical"
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="country" type="category" width={100} />
              <Tooltip
                formatter={(value, name) => [
                  name === "operations" ? `${value.toLocaleString()} operations` : `${value}% growth`,
                  name === "operations" ? "Operations" : "Growth"
                ]}
              />
              <Bar dataKey="operations" fill="#3b82f6" name="Operations" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Growth Markets</CardTitle>
            <CardDescription>
              Countries with highest growth in credential operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockGeoData
                .sort((a, b) => b.growth - a.growth)
                .slice(0, 5)
                .map((country, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm">{country.country}</span>
                      <span className="text-sm font-medium">+{country.growth}%</span>
                    </div>
                    <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full" 
                        style={{ width: `${(country.growth / 25) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Device Distribution</CardTitle>
            <CardDescription>
              Credential operations by device type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Mobile (Android)</span>
                  <span className="text-sm font-medium">48%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: "48%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Mobile (iOS)</span>
                  <span className="text-sm font-medium">42%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: "42%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Desktop</span>
                  <span className="text-sm font-medium">8%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: "8%" }}></div>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Tablet</span>
                  <span className="text-sm font-medium">2%</span>
                </div>
                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500 rounded-full" style={{ width: "2%" }}></div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t">
              <h4 className="text-sm font-medium mb-3">Connection Methods</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">QR Code</span>
                    <span className="text-sm font-medium">72%</span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: "72%" }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">NFC</span>
                    <span className="text-sm font-medium">18%</span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full" style={{ width: "18%" }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Bluetooth</span>
                    <span className="text-sm font-medium">10%</span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full" style={{ width: "10%" }}></div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
