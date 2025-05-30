"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AreaChart, BarChart, LineChart } from "@/components/ui/charts"
import { useApi } from "@/hooks/use-api"
import { analyticsApi } from "@/lib/api-client"
import { LoadingCard, Loading } from "@/components/ui/loading"
import { ApiErrorMessage } from "@/components/ui/api-error"

// Define types for dashboard stats
interface DashboardStats {
  credentials: {
    total: number;
    issued_last_month: number;
    growth_percentage: number;
  };
  wallets: {
    active: number;
    growth_percentage: number;
  };
  verification: {
    rate: number;
    growth_percentage: number;
  };
  compliance: {
    score: number;
    change_percentage: number;
  };
  performance: {
    latency: number;
    api_success_rate: number;
    verification_success_rate: number;
  };
}

interface UsageTrend {
  date: string;
  credentials: number;
  wallets: number;
}

export default function DashboardPage() {
  // Fetch dashboard stats
  const { 
    data: dashboardStats, 
    isLoading: isLoadingStats, 
    error: statsError,
    refetch: refetchStats 
  } = useApi<DashboardStats>();

  // Fetch usage trends data
  const { 
    data: usageTrends, 
    isLoading: isLoadingTrends, 
    error: trendsError,
    refetch: refetchTrends 
  } = useApi<UsageTrend[]>();

  // Function to handle retrying API requests
  const handleRetryStats = () => {
    void (async () => {
      try {
        await refetchStats(async () => await analyticsApi.getDashboardStats());
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      }
    })();
  };

  const handleRetryTrends = () => {
    void (async () => {
      try {
        await refetchTrends(async () => await analyticsApi.getUsageTrends());
      } catch (error) {
        console.error('Error fetching usage trends:', error);
      }
    })();
  };

  // Fetch data when component mounts
  useEffect(() => {
    handleRetryStats();
    handleRetryTrends();
  }, []);

  return (
    <div className="flex flex-col gap-8" data-testid="dashboard-page">
      <div className="flex items-center justify-between" data-testid="dashboard-header">
        <h1 className="text-3xl font-bold tracking-tight" data-testid="dashboard-title">Dashboard</h1>
        <div className="flex items-center gap-4">
          <Button variant="outline">Download Report</Button>
          <Button>Create Credential</Button>
        </div>
      </div>
      
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {isLoadingStats ? (
              <div data-testid="dashboard-loading-stats">
                <LoadingCard data-testid="loading-card-1" />
                <LoadingCard data-testid="loading-card-2" />
                <LoadingCard data-testid="loading-card-3" />
                <LoadingCard data-testid="loading-card-4" />
              </div>
            ) : statsError ? (
              <div className="col-span-4" data-testid="dashboard-stats-error">
                <ApiErrorMessage error={statsError} onRetry={handleRetryStats} data-testid="stats-error-message" />
              </div>
            ) : dashboardStats ? (
              <div data-testid="dashboard-stats-content">
                <Card data-testid="credentials-card">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Credentials
                    </CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <rect width="18" height="14" x="3" y="5" rx="2" />
                      <path d="M21 8H8" />
                      <path d="M21 12H8" />
                      <path d="M21 16H8" />
                      <path d="M4 9h1" />
                      <path d="M4 13h1" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardStats.credentials.total.toLocaleString()}</div>
                    <p className={`text-xs ${dashboardStats.credentials.growth_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboardStats.credentials.growth_percentage >= 0 ? '+' : ''}
                      {dashboardStats.credentials.growth_percentage.toFixed(1)}% from last month
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Active Wallets
                    </CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4" />
                      <path d="M4 6v12c0 1.1.9 2 2 2h14v-4" />
                      <path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardStats.wallets.active.toLocaleString()}</div>
                    <p className={`text-xs ${dashboardStats.wallets.growth_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboardStats.wallets.growth_percentage >= 0 ? '+' : ''}
                      {dashboardStats.wallets.growth_percentage.toFixed(1)}% from last month
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Verification Rate</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardStats.verification.rate.toFixed(1)}%</div>
                    <p className={`text-xs ${dashboardStats.verification.growth_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboardStats.verification.growth_percentage >= 0 ? '+' : ''}
                      {dashboardStats.verification.growth_percentage.toFixed(1)}% from last month
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Compliance Score
                    </CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardStats.compliance.score.toFixed(1)}%</div>
                    <p className={`text-xs ${dashboardStats.compliance.change_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboardStats.compliance.change_percentage >= 0 ? '+' : ''}
                      {dashboardStats.compliance.change_percentage.toFixed(1)}% from last scan
                    </p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="col-span-4 flex h-40 items-center justify-center">
                <p className="text-muted-foreground">No dashboard data available</p>
              </div>
            )}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Credential Operations</CardTitle>
                <CardDescription>
                  Daily credential issuance and verification operations.
                </CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <div className="h-[300px] w-full">
                  {isLoadingTrends ? (
                    <div className="flex h-full items-center justify-center" data-testid="trends-loading">
                      <Loading size={32} text="Loading usage data..." data-testid="trends-loading-indicator" />
                    </div>
                  ) : trendsError ? (
                    <div className="flex h-full items-center justify-center" data-testid="trends-error">
                      <ApiErrorMessage error={trendsError} onRetry={handleRetryTrends} className="max-w-md" data-testid="trends-error-message" />
                    </div>
                  ) : usageTrends && usageTrends.length > 0 ? (
                    <LineChart
                      data={usageTrends.map(trend => ({
                        name: trend.date,
                        value: trend.credentials
                      }))}
                      xAxisDataKey="name"
                      yAxisDataKey="value"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      No usage data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Credential Distribution</CardTitle>
                <CardDescription>
                  Distribution by credential type.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] w-full">
                  {/* Placeholder for chart */}
                  <div className="h-full w-full rounded-md border border-dashed flex items-center justify-center text-muted-foreground">
                    Pie Chart - Credential Types
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Compliance Status</CardTitle>
                <CardDescription>
                  eIDAS 2 compliance status for your wallets.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingStats ? (
                  <div className="flex h-40 items-center justify-center">
                    <Loading size={32} text="Loading compliance data..." />
                  </div>
                ) : statsError ? (
                  <div className="flex h-40 items-center justify-center">
                    <ApiErrorMessage error={statsError} onRetry={handleRetryStats} className="max-w-md" />
                  </div>
                ) : dashboardStats ? (
                  <div className="space-y-8">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">Mobile Wallet v2.1</div>
                        <div className="text-sm text-muted-foreground">{dashboardStats.compliance.score}%</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${dashboardStats.compliance.score}%` }} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">Web Wallet v1.8</div>
                        <div className="text-sm text-muted-foreground">{Math.max(75, dashboardStats.compliance.score - 10)}%</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.max(75, dashboardStats.compliance.score - 10)}%` }} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">Enterprise Wallet v3.0</div>
                        <div className="text-sm text-muted-foreground">{Math.min(99, dashboardStats.compliance.score + 5)}%</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(99, dashboardStats.compliance.score + 5)}%` }} />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-40 items-center justify-center">
                    <p className="text-muted-foreground">No compliance data available</p>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Link href="/dashboard/compliance" className="text-sm text-primary hover:underline">
                  View detailed compliance reports
                </Link>
              </CardFooter>
            </Card>
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Latest credential operations and compliance events.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingStats ? (
                  <div className="flex h-[300px] items-center justify-center">
                    <Loading size={32} text="Loading recent activity..." />
                  </div>
                ) : statsError ? (
                  <div className="flex h-[300px] items-center justify-center">
                    <ApiErrorMessage error={statsError} onRetry={handleRetryStats} className="max-w-md" />
                  </div>
                ) : dashboardStats ? (
                  <div className="space-y-4">
                    {/* Mock recent activity based on real data */}
                    {[...Array(5)].map((_, i) => {
                      const isVerification = i % 2 === 0;
                      const credentialId = dashboardStats.credentials.total - i;
                      const timeAgo = (i + 1) * 5;
                      
                      return (
                        <div key={i} className="flex items-center gap-4">
                          <div className={`h-10 w-10 rounded-full flex items-center justify-center ${isVerification ? 'bg-primary/10 text-primary' : 'bg-muted'}`}>
                            {isVerification ? (
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="h-5 w-5"
                              >
                                <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
                                <rect width="6" height="4" x="9" y="3" rx="2" />
                                <path d="m9 14 2 2 4-4" />
                              </svg>
                            ) : (
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="h-5 w-5"
                              >
                                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                                <polyline points="14 2 14 8 20 8" />
                              </svg>
                            )}
                          </div>
                          <div className="flex-1 space-y-1">
                            <p className="text-sm font-medium leading-none">
                              {isVerification 
                                ? `Verified credential #${credentialId}` 
                                : `Issued new credential #${credentialId}`}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {isVerification 
                                ? `EU Driver's License verification successful` 
                                : `EU Digital Identity credential issued`}
                            </p>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {`${timeAgo}m ago`}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex h-[300px] items-center justify-center">
                    <p className="text-muted-foreground">No recent activity available</p>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Link href="/dashboard/activity" className="text-sm text-primary hover:underline">
                  View all activity
                </Link>
              </CardFooter>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Credential Operations Over Time</CardTitle>
                <CardDescription>
                  Monthly credential issuance and verification trends.
                </CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <div className="h-[300px] w-full">
                  {/* Placeholder for chart */}
                  <div className="h-full w-full rounded-md border border-dashed flex items-center justify-center text-muted-foreground">
                    Line Chart - Operations Over Time
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>
                  API performance and reliability metrics.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingStats ? (
                  <div className="flex h-full items-center justify-center">
                    <Loading size={32} text="Loading metrics..." />
                  </div>
                ) : statsError ? (
                  <div className="flex h-full items-center justify-center">
                    <ApiErrorMessage error={statsError} onRetry={handleRetryStats} className="max-w-md" />
                  </div>
                ) : dashboardStats ? (
                  <div className="space-y-8">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">API Response Time (P95)</div>
                        <div className="text-sm text-muted-foreground">{dashboardStats.performance.latency}ms</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, (dashboardStats.performance.latency / 800) * 100)}%` }} />
                      </div>
                      <div className="text-xs text-muted-foreground">Target: 800ms</div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">API Success Rate</div>
                        <div className="text-sm text-muted-foreground">{dashboardStats.performance.api_success_rate.toFixed(2)}%</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${dashboardStats.performance.api_success_rate}%` }} />
                      </div>
                      <div className="text-xs text-muted-foreground">Target: 99.9%</div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">Verification Success Rate</div>
                        <div className="text-sm text-muted-foreground">{dashboardStats.performance.verification_success_rate.toFixed(1)}%</div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary">
                        <div className="h-2 rounded-full bg-primary" style={{ width: `${dashboardStats.performance.verification_success_rate}%` }} />
                      </div>
                      <div className="text-xs text-muted-foreground">Target: 98%</div>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-muted-foreground">No performance data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Available Reports</CardTitle>
              <CardDescription>
                Download detailed reports about your EUDI-Connect usage.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Monthly Usage Report</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        Detailed credential operations and API usage statistics.
                      </p>
                    </CardContent>
                    <CardFooter>
                      <Button size="sm" variant="outline" className="w-full">Download PDF</Button>
                    </CardFooter>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Compliance Report</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        eIDAS 2 compliance status for all registered wallets.
                      </p>
                    </CardContent>
                    <CardFooter>
                      <Button size="sm" variant="outline" className="w-full">Download PDF</Button>
                    </CardFooter>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Performance Report</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        API performance metrics and SLA compliance data.
                      </p>
                    </CardContent>
                    <CardFooter>
                      <Button size="sm" variant="outline" className="w-full">Download PDF</Button>
                    </CardFooter>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
