import Link from "next/link"
import { Button } from "@/components/ui/button"
import { EUFlagIcon } from "@/components/ui/icons"

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <EUFlagIcon className="h-8 w-8" />
            <span className="text-lg font-bold">EUDI-Connect</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Log in</Button>
            </Link>
            <Link href="/register">
              <Button>Sign up</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container flex flex-1 flex-col items-center justify-center gap-6 py-12 md:py-20">
        <div className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-3xl font-bold leading-tight tracking-tighter md:text-5xl lg:text-6xl lg:leading-[1.1]">
            EU Digital Identity Wallet Integration
          </h1>
          <p className="max-w-[700px] text-lg text-muted-foreground md:text-xl">
            Connect your business to the EU Digital Identity ecosystem 
            with our eIDAS 2 compliant platform.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link href="/dashboard">
            <Button size="lg">Go to Dashboard</Button>
          </Link>
          <Link href="/documentation">
            <Button variant="outline" size="lg">Documentation</Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-12 md:py-20">
        <div className="grid gap-8 md:grid-cols-3">
          <div className="flex flex-col gap-2">
            <h3 className="text-xl font-bold">Credential Core Engine</h3>
            <p className="text-muted-foreground">
              Issue and verify W3C Verifiable Credentials with our robust API.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-xl font-bold">eIDAS 2 Compliance Scanner</h3>
            <p className="text-muted-foreground">
              Validate your wallet implementation against eIDAS 2 requirements.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-xl font-bold">Tiered Billing & Analytics</h3>
            <p className="text-muted-foreground">
              Pay only for what you use with transparent usage analytics.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-6 md:py-8">
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} EUDI-Connect. All rights reserved.
          </p>
          <nav className="flex gap-4">
            <Link href="/privacy" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
              Privacy
            </Link>
            <Link href="/terms" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
              Terms
            </Link>
            <Link href="/contact" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
              Contact
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
