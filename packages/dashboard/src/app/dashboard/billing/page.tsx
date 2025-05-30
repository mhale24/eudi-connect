"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { AreaChart } from "@/components/ui/charts"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from "recharts"
import { LoadingPage, LoadingCard, Loading } from "@/components/ui/loading"
import { ApiErrorMessage, ApiErrorFull } from "@/components/ui/api-error"
import { useApi } from "@/hooks/use-api"
import { billingApi, analyticsApi } from "@/lib/api-client"
import { toast } from "@/components/ui/use-toast"

// Define types for the API data
interface BillingPlan {
  id: string;
  name: string;
  price: number;
  billing_cycle: string;
  description?: string;
  features: string[];
  limits: {
    credential_operations: number | string;
    api_keys: number | string;
    wallet_sessions: number | string;
    compliance_scans: number | string;
  };
  popular?: boolean;
}

interface Subscription {
  id: string;
  plan_id: string;
  plan_name: string;
  name: string; // Add name property for backward compatibility
  price: number;
  billing_cycle: string;
  next_billing_date: string;
  status: string;
  features: string[];
  limits: {
    credential_operations: number | string;
    api_keys: number | string;
    wallet_sessions: number | string;
    compliance_scans: number | string;
  };
  current_usage: {
    credential_operations: number;
    api_keys: number;
    wallet_sessions: number;
    compliance_scans: number;
  };
}

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: string;
  description: string;
}

interface UsageData {
  month: string;
  credentials: number;
  wallets: number;
}

interface DailyUsageData {
  date: string;
  credentials: number;
  wallets: number;
}

// Fallback mock data for development/testing
const mockCurrentPlan = {
  id: "plan-1",
  plan_id: "plan-professional",
  plan_name: "Professional",
  price: 299,
  billing_cycle: "monthly",
  next_billing_date: "2025-06-27T00:00:00Z",
  status: "active",
  features: [
    "Up to 10,000 credential operations/month",
    "Unlimited API keys",
    "Priority support",
    "Compliance scanner",
    "Custom credential templates",
    "Webhook notifications"
  ],
  limits: {
    credential_operations: 10000,
    api_keys: "Unlimited",
    wallet_sessions: 5000,
    compliance_scans: 20
  },
  current_usage: {
    credential_operations: 6253,
    api_keys: 4,
    wallet_sessions: 2845,
    compliance_scans: 12
  }
}

const mockBillingPlans = [
  {
    id: "plan-starter",
    name: "Starter",
    price: 99,
    billing_cycle: "monthly",
    description: "For small businesses just getting started with digital identity",
    features: [
      "Up to 2,000 credential operations/month",
      "2 API keys",
      "Email support",
      "Basic compliance scanner",
      "Standard credential templates"
    ],
    limits: {
      credential_operations: 2000,
      api_keys: 2,
      wallet_sessions: 1000,
      compliance_scans: 5
    },
    popular: false
  },
  {
    id: "plan-professional",
    name: "Professional",
    price: 299,
    billing_cycle: "monthly",
    description: "For growing businesses with increasing digital identity needs",
    features: [
      "Up to 10,000 credential operations/month",
      "Unlimited API keys",
      "Priority support",
      "Compliance scanner",
      "Custom credential templates",
      "Webhook notifications"
    ],
    limits: {
      credential_operations: 10000,
      api_keys: "Unlimited",
      wallet_sessions: 5000,
      compliance_scans: 20
    },
    popular: true
  },
  {
    id: "plan-enterprise",
    name: "Enterprise",
    price: 999,
    billing_cycle: "monthly",
    description: "For large organizations with advanced digital identity requirements",
    features: [
      "Unlimited credential operations",
      "Unlimited API keys",
      "24/7 dedicated support",
      "Advanced compliance scanner",
      "Custom credential templates",
      "Webhook notifications",
      "Custom integrations",
      "SLA guarantees"
    ],
    limits: {
      credential_operations: "Unlimited",
      api_keys: "Unlimited",
      wallet_sessions: "Unlimited",
      compliance_scans: "Unlimited"
    },
    popular: false
  }
]

const mockInvoices = [
  {
    id: "inv-1",
    date: "2025-05-27T00:00:00Z",
    amount: 299,
    status: "paid",
    description: "Professional Plan - Monthly Subscription"
  },
  {
    id: "inv-2",
    date: "2025-04-27T00:00:00Z",
    amount: 299,
    status: "paid",
    description: "Professional Plan - Monthly Subscription"
  },
  {
    id: "inv-3",
    date: "2025-03-27T00:00:00Z",
    amount: 299,
    status: "paid",
    description: "Professional Plan - Monthly Subscription"
  },
  {
    id: "inv-4",
    date: "2025-02-27T00:00:00Z",
    amount: 299,
    status: "paid",
    description: "Professional Plan - Monthly Subscription"
  },
  {
    id: "inv-5",
    date: "2025-01-27T00:00:00Z",
    amount: 99,
    status: "paid",
    description: "Starter Plan - Monthly Subscription"
  }
]

const mockUsageHistory = [
  { month: "Jan", credentials: 1245, wallets: 625 },
  { month: "Feb", credentials: 2356, wallets: 1123 },
  { month: "Mar", credentials: 3245, wallets: 1625 },
  { month: "Apr", credentials: 4532, wallets: 2305 },
  { month: "May", credentials: 6253, wallets: 2845 }
]

const mockDailyUsage = [
  { date: "May 21", credentials: 187, wallets: 93 },
  { date: "May 22", credentials: 198, wallets: 97 },
  { date: "May 23", credentials: 215, wallets: 105 },
  { date: "May 24", credentials: 208, wallets: 102 },
  { date: "May 25", credentials: 193, wallets: 95 },
  { date: "May 26", credentials: 210, wallets: 103 },
  { date: "May 27", credentials: 205, wallets: 101 }
]

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  })
}

function getInvoiceStatusBadge(status: string) {
  switch (status) {
    case "paid":
      return <Badge variant="outline" className="border-green-500 text-green-600">Paid</Badge>
    case "pending":
      return <Badge variant="outline" className="border-yellow-500 text-yellow-600">Pending</Badge>
    case "failed":
      return <Badge variant="outline" className="border-red-500 text-red-600">Failed</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

export default function BillingPage() {
  // Fetch current subscription
  const { 
    data: subscription, 
    isLoading: isLoadingSubscription, 
    error: subscriptionError, 
    refetch: refetchSubscription 
  } = useApi<Subscription>();
  
  // Fetch available plans
  const { 
    data: plans, 
    isLoading: isLoadingPlans, 
    error: plansError, 
    refetch: refetchPlans 
  } = useApi<BillingPlan[]>();
  
  // Fetch invoices
  const { 
    data: invoices, 
    isLoading: isLoadingInvoices, 
    error: invoicesError, 
    refetch: refetchInvoices 
  } = useApi<Invoice[]>();
  
  // Fetch usage trends
  const { 
    data: usageTrends, 
    isLoading: isLoadingUsageTrends, 
    error: usageTrendsError, 
    refetch: refetchUsageTrends 
  } = useApi<UsageData[]>();
  
  // Fetch daily usage
  const { 
    data: dailyUsage, 
    isLoading: isLoadingDailyUsage, 
    error: dailyUsageError, 
    refetch: refetchDailyUsage 
  } = useApi<DailyUsageData[]>();
  
  // Load data when component mounts
  useEffect(() => {
    const fetchData = async () => {
      await refetchSubscription(async () => await billingApi.getSubscription());
      await refetchPlans(async () => await billingApi.getPlans());
      await refetchInvoices(async () => await billingApi.getInvoices());
      await refetchUsageTrends(async () => await analyticsApi.getUsageTrends('30d'));
      await refetchDailyUsage(async () => await analyticsApi.getUsageTrends('7d'));
    };
    fetchData();
  }, [refetchSubscription, refetchPlans, refetchInvoices, refetchUsageTrends, refetchDailyUsage]);
  
  // Use API data with fallback to mock data if needed
  const currentPlan = subscription || mockCurrentPlan;
  const availablePlans = plans || mockBillingPlans;
  const invoicesList = invoices || mockInvoices;
  const usageHistory = usageTrends || mockUsageHistory;
  const dailyUsageData = dailyUsage || mockDailyUsage;
  
  // Loading and error states
  const isLoading = isLoadingSubscription || isLoadingPlans || isLoadingInvoices || isLoadingUsageTrends || isLoadingDailyUsage;
  const hasErrors = subscriptionError || plansError || invoicesError || usageTrendsError || dailyUsageError;
  
  // Handle plan upgrade
  const handleUpgradePlan = async () => {
    if (!selectedPlan) return;
    
    try {
      await billingApi.updatePlan(selectedPlan);
      toast({
        title: "Subscription updated",
        description: "Your subscription has been successfully updated.",
      });
      refetchSubscription(async () => await billingApi.getSubscription());
      setShowUpgradeDialog(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update subscription. Please try again later.",
        variant: "destructive",
      });
    }
  };
  const [activeTab, setActiveTab] = useState("subscription")
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing & Subscription</h1>
          <p className="text-muted-foreground">
            Manage your subscription plan and billing details
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline">Billing Portal</Button>
          <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
            <DialogTrigger asChild>
              <Button>Upgrade Plan</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Upgrade Your Plan</DialogTitle>
                <DialogDescription>
                  Choose a plan that fits your business needs
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {isLoadingPlans ? (
                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                      <LoadingCard />
                      <LoadingCard />
                      <LoadingCard />
                    </div>
                  ) : (
                    availablePlans.map((plan) => (
                      <Card 
                        key={plan.id} 
                        className={`cursor-pointer transition-all hover:border-primary ${
                          selectedPlan === plan.id ? 'border-primary ring-2 ring-primary ring-opacity-20' : ''
                        } ${plan.popular ? 'relative' : ''}`}
                        onClick={() => setSelectedPlan(plan.id)}
                      >
                        {plan.popular && (
                          <div className="absolute -top-3 left-0 right-0 mx-auto w-max">
                            <Badge className="bg-primary">Popular</Badge>
                          </div>
                        )}
                        <CardHeader>
                          <CardTitle>{plan.name}</CardTitle>
                          <CardDescription>{plan.description}</CardDescription>
                          <div className="mt-2">
                            <span className="text-3xl font-bold">€{plan.price}</span>
                            <span className="text-muted-foreground">/month</span>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm">
                            {plan.features.map((feature, i) => (
                              <li key={i} className="flex items-center">
                                <svg 
                                  xmlns="http://www.w3.org/2000/svg" 
                                  width="16" 
                                  height="16" 
                                  viewBox="0 0 24 24" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                  className="mr-2 text-green-500"
                                >
                                  <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                                {feature}
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowUpgradeDialog(false)}>Cancel</Button>
                <Button disabled={!selectedPlan} onClick={handleUpgradePlan}>Confirm Upgrade</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="subscription">Subscription</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
        </TabsList>
        
        <TabsContent value="subscription" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Current Plan</CardTitle>
                <CardDescription>
                  Your active subscription plan and details
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  {hasErrors && (
                    <div className="space-y-4">
                      {subscriptionError && (
                        <ApiErrorMessage 
                          error={subscriptionError} 
                          onRetry={() => refetchSubscription(async () => await billingApi.getSubscription())} 
                        />
                      )}
                      {plansError && (
                        <ApiErrorMessage 
                          error={plansError} 
                          onRetry={() => refetchPlans(async () => await billingApi.getPlans())} 
                        />
                      )}
                      {invoicesError && (
                        <ApiErrorMessage 
                          error={invoicesError} 
                          onRetry={() => refetchInvoices(async () => await billingApi.getInvoices())} 
                        />
                      )}
                      {usageTrendsError && (
                        <ApiErrorMessage 
                          error={usageTrendsError} 
                          onRetry={() => refetchUsageTrends(async () => await analyticsApi.getUsageTrends('30d'))} 
                        />
                      )}
                    </div>
                  )}
                  
                  <div className="flex flex-col space-y-2 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
                    <h2 className="text-3xl font-bold tracking-tight">Billing</h2>
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => {
                          navigator.clipboard.writeText("EUDI-12345")
                          toast({
                            title: "Copied to clipboard",
                            description: "Your merchant ID has been copied to clipboard",
                          })
                        }}
                        variant="outline"
                      >
                        Merchant ID: EUDI-12345
                      </Button>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-xl font-bold">{currentPlan.plan_name} Plan</h3>
                      <p className="text-muted-foreground">
                        €{currentPlan.price}/{currentPlan.billing_cycle}
                      </p>
                    </div>
                    <Badge className="bg-green-500">Active</Badge>
                  </div>
                  
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Next billing date: {formatDateTime(currentPlan.next_billing_date)}</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                    <div>
                      <h4 className="text-sm font-medium mb-2">Credential Operations</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{currentPlan.current_usage.credential_operations.toLocaleString()}</span>
                          <span>of {currentPlan.limits.credential_operations.toLocaleString()}</span>
                        </div>
                        <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded-full" 
                            style={{ 
                              width: `${(currentPlan.current_usage.credential_operations / (currentPlan.limits.credential_operations as number)) * 100}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium mb-2">Wallet Sessions</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{currentPlan.current_usage.wallet_sessions.toLocaleString()}</span>
                          <span>of {currentPlan.limits.wallet_sessions.toLocaleString()}</span>
                        </div>
                        <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ 
                              width: `${(currentPlan.current_usage.wallet_sessions / (currentPlan.limits.wallet_sessions as number)) * 100}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium mb-2">API Keys</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{currentPlan.current_usage.api_keys}</span>
                          <span>of {currentPlan.limits.api_keys}</span>
                        </div>
                        {typeof currentPlan.limits.api_keys === 'number' && (
                          <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-purple-500 rounded-full" 
                              style={{ 
                                width: `${(currentPlan.current_usage.api_keys / (currentPlan.limits.api_keys as number)) * 100}%` 
                              }}
                            ></div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium mb-2">Compliance Scans</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{currentPlan.current_usage.compliance_scans}</span>
                          <span>of {currentPlan.limits.compliance_scans}</span>
                        </div>
                        <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-orange-500 rounded-full" 
                            style={{ 
                              width: `${(currentPlan.current_usage.compliance_scans / (currentPlan.limits.compliance_scans as number)) * 100}%` 
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button variant="outline">Change Billing Cycle</Button>
                <Button onClick={() => setShowUpgradeDialog(true)}>Upgrade Plan</Button>
              </CardFooter>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Plan Features</CardTitle>
                <CardDescription>
                  Features included in your current plan
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {currentPlan.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <svg 
                        xmlns="http://www.w3.org/2000/svg" 
                        width="16" 
                        height="16" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                        className="mr-2 text-green-500"
                      >
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Link href="/dashboard/documentation/billing-plans" className="w-full">
                  <Button variant="outline" className="w-full">View All Plans</Button>
                </Link>
              </CardFooter>
            </Card>
          </div>
          
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
              <CardDescription>
                Manage your payment methods
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 border rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white font-bold">
                    VISA
                  </div>
                  <div>
                    <p className="font-medium">Visa ending in 4242</p>
                    <p className="text-sm text-muted-foreground">Expires 12/2028</p>
                  </div>
                </div>
                <Badge>Default</Badge>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button variant="outline">Add Payment Method</Button>
              <Button variant="outline">Update Payment Method</Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="usage" className="mt-6">
          <div className="grid grid-cols-1 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Monthly Usage</CardTitle>
                <CardDescription>
                  Credential operations and wallet sessions over the past 5 months
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px]">
                {isLoadingUsageTrends ? (
                  <div className="flex h-full items-center justify-center">
                    <Loading size={24} text="Loading usage data..." />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={usageHistory} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="credentials" name="Credential Operations" fill="#3b82f6" />
                      <Bar dataKey="wallets" name="Wallet Sessions" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Daily Usage (Last 7 Days)</CardTitle>
                <CardDescription>
                  Recent credential operations and wallet sessions
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={dailyUsageData}
                    margin={{
                      top: 5,
                      right: 10,
                      left: 10,
                      bottom: 0,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="credentials" 
                      name="Credential Operations" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="wallets" 
                      name="Wallet Sessions" 
                      stroke="#10b981" 
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
                  <CardTitle>Credential Operations Breakdown</CardTitle>
                  <CardDescription>
                    Usage by operation type
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Issuance</span>
                        <span className="text-sm font-medium">3,254 (52%)</span>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: "52%" }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Verification</span>
                        <span className="text-sm font-medium">2,687 (43%)</span>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 rounded-full" style={{ width: "43%" }}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Revocation</span>
                        <span className="text-sm font-medium">312 (5%)</span>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{ width: "5%" }}></div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Cost Projection</CardTitle>
                  <CardDescription>
                    Estimated cost based on current usage
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Current Month Usage</span>
                        <span className="text-sm font-medium">€299 (100%)</span>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: "100%" }}></div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Projected Next Month</span>
                        <span className="text-sm font-medium">€299 (base plan)</span>
                      </div>
                      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: "100%" }}></div>
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <h4 className="text-sm font-medium mb-2">Upgrade Recommendations</h4>
                      <p className="text-sm text-muted-foreground">
                        Based on your current usage trends, you&apos;re using 63% of your monthly allocation.
                        Your current plan is appropriate for your needs.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="invoices" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Invoices</CardTitle>
              <CardDescription>
                View and download your invoices
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingInvoices ? (
                <div className="flex h-[300px] items-center justify-center">
                  <Loading size={24} text="Loading invoice data..." />
                </div>
              ) : invoicesList.length === 0 ? (
                <div className="flex h-[200px] items-center justify-center rounded-lg border border-dashed">
                  <div className="text-center">
                    <h3 className="text-lg font-medium">No invoices available</h3>
                    <p className="text-sm text-muted-foreground">Invoices will appear here once you have active billing.</p>
                  </div>
                </div>
              ) : (
                <div className="relative overflow-x-auto rounded-md border">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs uppercase bg-muted/50">
                      <tr>
                        <th scope="col" className="px-6 py-3">Invoice ID</th>
                        <th scope="col" className="px-6 py-3">Date</th>
                        <th scope="col" className="px-6 py-3">Amount</th>
                        <th scope="col" className="px-6 py-3">Description</th>
                        <th scope="col" className="px-6 py-3">Status</th>
                        <th scope="col" className="px-6 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoicesList.map(invoice => (
                      <tr key={invoice.id} className="border-b hover:bg-muted/50">
                        <td className="px-6 py-4 font-mono text-xs">
                          {invoice.id}
                        </td>
                        <td className="px-6 py-4">
                          {formatDateTime(invoice.date)}
                        </td>
                        <td className="px-6 py-4 font-medium">
                          €{invoice.amount}
                        </td>
                        <td className="px-6 py-4">
                          {invoice.description}
                        </td>
                        <td className="px-6 py-4">
                          {getInvoiceStatusBadge(invoice.status)}
                        </td>
                        <td className="px-6 py-4">
                          <Button variant="ghost" size="sm">
                            <svg 
                              xmlns="http://www.w3.org/2000/svg" 
                              width="16" 
                              height="16" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              stroke="currentColor" 
                              strokeWidth="2" 
                              strokeLinecap="round" 
                              strokeLinejoin="round"
                              className="mr-2"
                            >
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                              <polyline points="7 10 12 15 17 10"></polyline>
                              <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            Download
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex justify-between">
              <p className="text-sm text-muted-foreground">
                Showing 5 of 5 invoices
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled>Previous</Button>
                <Button variant="outline" size="sm" disabled>Next</Button>
              </div>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
