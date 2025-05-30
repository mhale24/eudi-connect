"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  AnalyticsIcon,
  ComplianceIcon,
  CredentialIcon,
  EUFlagIcon,
  LogoIcon,
  SettingsIcon,
  WalletIcon
} from "@/components/ui/icons"

interface NavItemProps {
  href: string
  icon: React.ReactNode
  title: string
  isActive?: boolean
}

function NavItem({ href, icon, title, isActive }: NavItemProps) {
  return (
    <Link 
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all hover:bg-accent",
        isActive ? "bg-accent text-accent-foreground font-medium" : "text-muted-foreground"
      )}
    >
      {icon}
      <span>{title}</span>
    </Link>
  )
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(true)
  
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b bg-background px-6">
        <button 
          className="lg:hidden"
          onClick={() => setIsOpen(!isOpen)}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-6 w-6"
          >
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </svg>
          <span className="sr-only">Toggle Menu</span>
        </button>
        <div className="flex items-center gap-2">
          <EUFlagIcon className="h-6 w-6" />
          <span className="font-semibold">EUDI-Connect</span>
        </div>
        <div className="flex-1" />
        <nav className="flex items-center gap-4">
          <div className="relative">
            <button className="h-8 w-8 rounded-full bg-primary text-xs text-primary-foreground">
              JD
            </button>
          </div>
        </nav>
      </header>
      
      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className={cn(
          "fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r bg-background pt-16 transition-transform lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}>
          <nav className="flex flex-1 flex-col gap-1 p-4">
            <NavItem
              href="/dashboard"
              icon={<LogoIcon className="h-5 w-5" />}
              title="Overview"
              isActive={pathname === "/dashboard"}
            />
            <NavItem
              href="/dashboard/credentials"
              icon={<CredentialIcon className="h-5 w-5" />}
              title="Credentials"
              isActive={pathname.startsWith("/dashboard/credentials")}
            />
            <NavItem
              href="/dashboard/wallets"
              icon={<WalletIcon className="h-5 w-5" />}
              title="Wallets"
              isActive={pathname.startsWith("/dashboard/wallets")}
            />
            <NavItem
              href="/dashboard/compliance"
              icon={<ComplianceIcon className="h-5 w-5" />}
              title="Compliance Scanner"
              isActive={pathname.startsWith("/dashboard/compliance")}
            />
            <NavItem
              href="/dashboard/analytics"
              icon={<AnalyticsIcon className="h-5 w-5" />}
              title="Analytics"
              isActive={pathname.startsWith("/dashboard/analytics")}
            />
            <NavItem
              href="/dashboard/settings"
              icon={<SettingsIcon className="h-5 w-5" />}
              title="Settings"
              isActive={pathname.startsWith("/dashboard/settings")}
            />
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2">
              <div className="flex flex-col">
                <span className="text-xs font-medium">Free Plan</span>
                <span className="text-xs text-muted-foreground">100 credentials/mo</span>
              </div>
              <div className="flex-1" />
              <Link 
                href="/dashboard/billing"
                className="text-xs text-primary hover:underline"
              >
                Upgrade
              </Link>
            </div>
          </div>
        </aside>
        
        {/* Main Content */}
        <main className="flex flex-1 flex-col px-4 py-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  )
}
