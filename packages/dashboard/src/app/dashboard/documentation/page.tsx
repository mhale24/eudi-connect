"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"

// Mock documentation categories and content
const mockDocCategories = [
  {
    id: "getting-started",
    name: "Getting Started",
    icon: "📚",
    description: "Introduction to EUDI-Connect and basic setup"
  },
  {
    id: "credential-api",
    name: "Credential API",
    icon: "🔐",
    description: "APIs for issuing and verifying W3C Verifiable Credentials"
  },
  {
    id: "wallet-integration",
    name: "Wallet Integration",
    icon: "📱",
    description: "Connect with EU Digital Identity Wallets"
  },
  {
    id: "compliance",
    name: "eIDAS 2.0 Compliance",
    icon: "✅",
    description: "Ensuring compliance with EU regulations"
  },
  {
    id: "sdks",
    name: "SDKs & Libraries",
    icon: "🧰",
    description: "Client libraries and SDKs for different platforms"
  },
  {
    id: "webhooks",
    name: "Webhooks",
    icon: "🔄",
    description: "Real-time notifications for credential operations"
  }
]

const mockDocItems = {
  "getting-started": [
    {
      id: "gs-1",
      title: "Introduction to EUDI-Connect",
      description: "Overview of the platform and its capabilities",
      type: "guide",
      updated_at: "2025-05-15T10:00:00Z"
    },
    {
      id: "gs-2",
      title: "Account Setup",
      description: "Creating and configuring your EUDI-Connect account",
      type: "guide",
      updated_at: "2025-05-16T14:30:00Z"
    },
    {
      id: "gs-3",
      title: "API Keys & Authentication",
      description: "Managing API keys and authenticating with the EUDI-Connect API",
      type: "guide",
      updated_at: "2025-05-18T09:15:00Z"
    },
    {
      id: "gs-4",
      title: "Integration Architecture",
      description: "Understanding the EUDI-Connect integration architecture",
      type: "reference",
      updated_at: "2025-05-20T11:45:00Z"
    }
  ],
  "credential-api": [
    {
      id: "cred-1",
      title: "Credential Issuance API",
      description: "Issuing W3C Verifiable Credentials to wallets",
      type: "reference",
      updated_at: "2025-05-12T10:30:00Z"
    },
    {
      id: "cred-2",
      title: "Credential Verification API",
      description: "Verifying credentials presented by wallet holders",
      type: "reference",
      updated_at: "2025-05-13T14:45:00Z"
    },
    {
      id: "cred-3",
      title: "Credential Revocation API",
      description: "Revoking previously issued credentials",
      type: "reference",
      updated_at: "2025-05-14T09:20:00Z"
    },
    {
      id: "cred-4",
      title: "Credential Templates",
      description: "Creating and managing credential templates",
      type: "guide",
      updated_at: "2025-05-15T16:35:00Z"
    },
    {
      id: "cred-5",
      title: "Selective Disclosure",
      description: "Implementing selective disclosure in credentials",
      type: "guide",
      updated_at: "2025-05-16T11:10:00Z"
    }
  ],
  "wallet-integration": [
    {
      id: "wallet-1",
      title: "OpenID for Verifiable Presentations",
      description: "Implementing OpenID4VP protocol for wallet interactions",
      type: "reference",
      updated_at: "2025-05-10T10:15:00Z"
    },
    {
      id: "wallet-2",
      title: "QR Code Integration",
      description: "Connecting with wallets via QR codes",
      type: "guide",
      updated_at: "2025-05-11T14:30:00Z"
    },
    {
      id: "wallet-3",
      title: "Wallet Session Management",
      description: "Managing wallet sessions and state",
      type: "guide",
      updated_at: "2025-05-12T09:45:00Z"
    },
    {
      id: "wallet-4",
      title: "Cross-Wallet Compatibility",
      description: "Ensuring compatibility with different EU wallet implementations",
      type: "guide",
      updated_at: "2025-05-13T16:20:00Z"
    }
  ],
  "compliance": [
    {
      id: "comp-1",
      title: "eIDAS 2.0 Overview",
      description: "Understanding the eIDAS 2.0 regulation framework",
      type: "guide",
      updated_at: "2025-05-08T10:30:00Z"
    },
    {
      id: "comp-2",
      title: "Compliance Requirements",
      description: "Detailed list of eIDAS 2.0 compliance requirements",
      type: "reference",
      updated_at: "2025-05-09T14:15:00Z"
    },
    {
      id: "comp-3",
      title: "Compliance Scanner Guide",
      description: "Using the EUDI-Connect compliance scanner",
      type: "guide",
      updated_at: "2025-05-10T09:45:00Z"
    },
    {
      id: "comp-4",
      title: "Privacy & Data Protection",
      description: "Implementing privacy-by-design principles",
      type: "guide",
      updated_at: "2025-05-11T16:30:00Z"
    }
  ],
  "sdks": [
    {
      id: "sdk-1",
      title: "JavaScript SDK",
      description: "Client-side JavaScript SDK for web applications",
      type: "reference",
      updated_at: "2025-05-05T10:15:00Z"
    },
    {
      id: "sdk-2",
      title: "React Integration",
      description: "Integrating EUDI-Connect with React applications",
      type: "guide",
      updated_at: "2025-05-06T14:30:00Z"
    },
    {
      id: "sdk-3",
      title: "Node.js SDK",
      description: "Server-side Node.js SDK for backend integration",
      type: "reference",
      updated_at: "2025-05-07T09:45:00Z"
    },
    {
      id: "sdk-4",
      title: "Python SDK",
      description: "Python SDK for backend integration",
      type: "reference",
      updated_at: "2025-05-08T16:20:00Z"
    },
    {
      id: "sdk-5",
      title: "Mobile SDKs (iOS & Android)",
      description: "Native SDKs for mobile app integration",
      type: "reference",
      updated_at: "2025-05-09T11:10:00Z"
    }
  ],
  "webhooks": [
    {
      id: "wh-1",
      title: "Webhook Introduction",
      description: "Understanding webhooks in EUDI-Connect",
      type: "guide",
      updated_at: "2025-05-03T10:30:00Z"
    },
    {
      id: "wh-2",
      title: "Webhook Configuration",
      description: "Setting up and managing webhooks",
      type: "guide",
      updated_at: "2025-05-04T14:15:00Z"
    },
    {
      id: "wh-3",
      title: "Webhook Events",
      description: "List of available webhook events",
      type: "reference",
      updated_at: "2025-05-05T09:45:00Z"
    },
    {
      id: "wh-4",
      title: "Webhook Security",
      description: "Securing webhook endpoints and verifying signatures",
      type: "guide",
      updated_at: "2025-05-06T16:30:00Z"
    }
  ]
}

// Mock code snippets for quick start
const mockCodeSnippets = {
  javascript: `// Install the SDK
npm install @eudi-connect/sdk

// Initialize the client
import { EudiConnectClient } from '@eudi-connect/sdk';

const client = new EudiConnectClient({
  apiKey: 'YOUR_API_KEY',
  environment: 'production'
});

// Issue a credential
async function issueCredential(walletId, credentialData) {
  try {
    const result = await client.credentials.issue({
      walletId,
      type: 'EuropeanDigitalIdentityCredential',
      data: credentialData
    });
    console.log('Credential issued:', result.credentialId);
    return result;
  } catch (error) {
    console.error('Error issuing credential:', error);
  }
}`,
  
  python: `# Install the SDK
# pip install eudi-connect

# Initialize the client
from eudi_connect import Client

client = Client(
    api_key='YOUR_API_KEY',
    environment='production'
)

# Issue a credential
def issue_credential(wallet_id, credential_data):
    try:
        result = client.credentials.issue(
            wallet_id=wallet_id,
            type='EuropeanDigitalIdentityCredential',
            data=credential_data
        )
        print(f"Credential issued: {result.credential_id}")
        return result
    except Exception as e:
        print(f"Error issuing credential: {e}")`,
  
  node: `// Install the SDK
// npm install @eudi-connect/sdk

// Initialize the client
const { EudiConnectClient } = require('@eudi-connect/sdk');

const client = new EudiConnectClient({
  apiKey: 'YOUR_API_KEY',
  environment: 'production'
});

// Issue a credential
async function issueCredential(walletId, credentialData) {
  try {
    const result = await client.credentials.issue({
      walletId,
      type: 'EuropeanDigitalIdentityCredential',
      data: credentialData
    });
    console.log('Credential issued:', result.credentialId);
    return result;
  } catch (error) {
    console.error('Error issuing credential:', error);
  }
}`
}

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  })
}

export default function DocumentationPage() {
  const [activeTab, setActiveTab] = useState("getting-started")
  const [activeSnippet, setActiveSnippet] = useState("javascript")
  const [searchQuery, setSearchQuery] = useState("")
  
  // Filter docs based on search query
  const filteredDocs = searchQuery 
    ? Object.values(mockDocItems).flat().filter(item => 
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
        item.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : mockDocItems[activeTab as keyof typeof mockDocItems]
  
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
          <p className="text-muted-foreground">
            Integration guides and API references for EUDI-Connect
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="outline" className="gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Download SDK
          </Button>
          <Button variant="outline" className="gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
              <path d="M9 18c-4.51 2-5-2-7-2"></path>
            </svg>
            GitHub
          </Button>
        </div>
      </div>
      
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="lg:w-1/4 space-y-6">
          <div className="relative">
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
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            >
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <Input
              placeholder={'Search documentation...'}
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          {!searchQuery && (
            <div className="space-y-1">
              {mockDocCategories.map((category) => (
                <button
                  key={category.id}
                  className={`flex items-center gap-3 w-full rounded-lg px-3 py-2 text-sm font-medium transition-colors
                    ${activeTab === category.id 
                      ? 'bg-muted text-primary' 
                      : 'hover:bg-muted/50 text-muted-foreground hover:text-primary'
                    }`}
                  onClick={() => setActiveTab(category.id)}
                >
                  <span className="text-xl">{category.icon}</span>
                  <span>{category.name}</span>
                </button>
              ))}
            </div>
          )}
          
          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
              <CardDescription>
                Get support from our team
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium">Chat Support</h4>
                  <p className="text-xs text-muted-foreground">Live chat with our support team</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium">FAQ</h4>
                  <p className="text-xs text-muted-foreground">Frequently asked questions</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"></path>
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium">Community Forum</h4>
                  <p className="text-xs text-muted-foreground">Join our developer community</p>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full">Contact Support</Button>
            </CardFooter>
          </Card>
        </div>
        
        <div className="lg:w-3/4 space-y-6">
          {searchQuery ? (
            <>
              <h2 className="text-xl font-semibold">Search Results for &quot;{searchQuery}&quot;</h2>
              {filteredDocs.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">🔍</div>
                  <h3 className="text-lg font-medium mb-1">No results found</h3>
                  <p className="text-muted-foreground">Try adjusting your search terms</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredDocs.map((doc) => (
                    <Card key={doc.id} className="overflow-hidden">
                      <CardHeader className="pb-2">
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-base">{doc.title}</CardTitle>
                          <span className="text-xs font-medium uppercase px-2 py-1 rounded bg-muted">
                            {doc.type}
                          </span>
                        </div>
                        <CardDescription>{doc.description}</CardDescription>
                      </CardHeader>
                      <CardFooter className="flex justify-between border-t bg-muted/50 px-6 py-3">
                        <div className="text-xs text-muted-foreground">
                          Updated {formatDateTime(doc.updated_at)}
                        </div>
                        <Link href={`/dashboard/documentation/${doc.id}`}>
                          <Button variant="ghost" size="sm">Read More</Button>
                        </Link>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{mockDocCategories.find(c => c.id === activeTab)?.icon}</span>
                <div>
                  <h2 className="text-xl font-semibold">{mockDocCategories.find(c => c.id === activeTab)?.name}</h2>
                  <p className="text-muted-foreground">{mockDocCategories.find(c => c.id === activeTab)?.description}</p>
                </div>
              </div>
              
              {activeTab === "getting-started" && (
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Start</CardTitle>
                    <CardDescription>
                      Get up and running with EUDI-Connect in minutes
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeSnippet} onValueChange={setActiveSnippet} className="w-full">
                      <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                        <TabsTrigger value="python">Python</TabsTrigger>
                        <TabsTrigger value="node">Node.js</TabsTrigger>
                      </TabsList>
                      <TabsContent value="javascript" className="mt-4">
                        <div className="relative">
                          <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                            <code>{mockCodeSnippets.javascript}</code>
                          </pre>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="absolute top-2 right-2"
                            onClick={() => navigator.clipboard.writeText(mockCodeSnippets.javascript)}
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                          </Button>
                        </div>
                      </TabsContent>
                      <TabsContent value="python" className="mt-4">
                        <div className="relative">
                          <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                            <code>{mockCodeSnippets.python}</code>
                          </pre>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="absolute top-2 right-2"
                            onClick={() => navigator.clipboard.writeText(mockCodeSnippets.python)}
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                          </Button>
                        </div>
                      </TabsContent>
                      <TabsContent value="node" className="mt-4">
                        <div className="relative">
                          <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                            <code>{mockCodeSnippets.node}</code>
                          </pre>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="absolute top-2 right-2"
                            onClick={() => navigator.clipboard.writeText(mockCodeSnippets.node)}
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                          </Button>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockDocItems[activeTab as keyof typeof mockDocItems].map((doc) => (
                  <Card key={doc.id} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-center">
                        <CardTitle className="text-base">{doc.title}</CardTitle>
                        <span className="text-xs font-medium uppercase px-2 py-1 rounded bg-muted">
                          {doc.type}
                        </span>
                      </div>
                      <CardDescription>{doc.description}</CardDescription>
                    </CardHeader>
                    <CardFooter className="flex justify-between border-t bg-muted/50 px-6 py-3">
                      <div className="text-xs text-muted-foreground">
                        Updated {formatDateTime(doc.updated_at)}
                      </div>
                      <Link href={`/dashboard/documentation/${doc.id}`}>
                        <Button variant="ghost" size="sm">Read More</Button>
                      </Link>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
