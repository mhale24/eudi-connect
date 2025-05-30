# EUDI-Connect

[![EUDI-Connect API Tests](https://github.com/yourusername/eudi-connect/actions/workflows/api-tests.yml/badge.svg)](https://github.com/yourusername/eudi-connect/actions/workflows/api-tests.yml)
[![codecov](https://codecov.io/gh/yourusername/eudi-connect/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/eudi-connect)

EUDI-Connect is an API layer and merchant dashboard for EU Digital Identity Wallet integration, built to comply with the eIDAS 2 mandate.

## Core Components

1. **Credential Core Engine**: Issues/verifies W3C Verifiable Credentials
2. **Merchant Integration SDK**: Drop-in integration for merchants
3. **No-Code Merchant Dashboard**: Next.js 15 based management interface
4. **eIDAS 2 Compliance Scanner**: Automated compliance testing
5. **Tiered Billing & Analytics**: Stripe-based billing system

## Tech Stack

- **Frontend**: Next.js 15, shadcn/ui
- **Backend**: FastAPI, Cloudflare Workers
- **Database**: Supabase (PostgreSQL + Vector)
- **Infrastructure**: Cloudflare, OpenTelemetry
- **Key Dependencies**: DIDKit, WebCrypto API, OpenID4VP

## Project Structure

```
eudi-connect/
├── packages/
│   ├── api/          # FastAPI backend
│   ├── dashboard/    # Next.js 15 admin dashboard
│   └── sdk/          # Merchant SDK
├── .github/
│   └── workflows/    # CI/CD pipelines
```

## Development

### Setup Environment

```bash
# Install API dependencies
cd packages/api
pip install -r requirements.txt

# Install dashboard dependencies
cd ../dashboard
npm install
```

### Run Tests

```bash
# Run API tests
cd packages/api
pytest --cov=eudi_connect

# View HTML coverage report
pytest --cov=eudi_connect --cov-report=html
open htmlcov/index.html
```

### Install Pre-Commit Hook

```bash
cd eudi-connect
cp packages/api/tools/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

## Database Schema

The system is built around these core tables:

1. **Merchant Management**
   - `merchants`: Core merchant account info
   - `merchant_users`: Team member management
   - `api_keys`: API key management
   - `webhooks`: Webhook configurations

2. **Credential Management**
   - `credential_types`: Available credential types
   - `credential_logs`: Audit trail of operations
   - `credential_embeddings`: Vector embeddings for search

3. **Wallet Integration**
   - `wallet_sessions`: Manages wallet interaction flows

4. **Compliance**
   - `compliance_requirements`: eIDAS 2 requirements
   - `compliance_scans`: Scan execution records
   - `compliance_scan_results`: Detailed scan findings

5. **Billing**
   - `billing_plans`: Available subscription tiers
   - `merchant_subscriptions`: Active subscriptions
   - `usage_records`: Usage tracking for billing

## Performance Targets

- **MVP**: ≤800ms P95 credential exchange latency
- **Future**: ≤300ms performance target
