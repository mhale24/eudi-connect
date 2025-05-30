"""Seed the database with eIDAS 2 compliance requirements.

This module provides utilities to create initial compliance requirements
based on the eIDAS 2 regulation. Run this script to populate the database
with a set of predefined requirements.
"""
import asyncio
import logging
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.db.session import get_session
from eudi_connect.models.compliance.models import (
    ComplianceRequirement,
    RequirementCategory,
    RequirementLevel,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define initial requirements
INITIAL_REQUIREMENTS = [
    # Security requirements
    {
        "code": "SEC-001",
        "name": "Secure Communication Channels",
        "description": "Wallet must establish secure channels for communication using TLS 1.3 or higher.",
        "category": RequirementCategory.SECURITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "security_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)",
        "metadata": {
            "standards": ["TLS 1.3", "HTTPS"],
            "risk_level": "high",
        },
    },
    {
        "code": "SEC-002",
        "name": "Cryptographic Algorithm Support",
        "description": "Wallet must support specified cryptographic algorithms for signing operations.",
        "category": RequirementCategory.SECURITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "security_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)",
        "metadata": {
            "algorithms": ["ES256", "EdDSA", "RS256"],
        },
    },
    {
        "code": "SEC-003",
        "name": "Key Protection",
        "description": "Private keys must be protected using secure hardware or software-based key storage.",
        "category": RequirementCategory.SECURITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "security_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)",
        "metadata": {
            "storage_options": ["secure element", "TEE", "software keystore"],
        },
    },
    
    # Privacy requirements
    {
        "code": "PRV-001",
        "name": "Data Minimization",
        "description": "Wallet must implement data minimization principles and only request necessary data.",
        "category": RequirementCategory.PRIVACY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "privacy_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(e), GDPR Article 5(1)(c)",
        "metadata": {
            "gdpr_principles": ["data_minimization"],
        },
    },
    {
        "code": "PRV-002",
        "name": "Selective Disclosure",
        "description": "Wallet must support selective disclosure of credential attributes.",
        "category": RequirementCategory.PRIVACY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "privacy_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(e)",
        "metadata": {
            "disclosure_protocols": ["ZKP", "selective_disclosure"],
        },
    },
    {
        "code": "PRV-003",
        "name": "User Consent",
        "description": "Wallet must obtain explicit user consent before sharing credentials.",
        "category": RequirementCategory.PRIVACY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "privacy_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(e), GDPR Article 7",
        "metadata": {
            "consent_requirements": ["explicit", "informed", "specific"],
        },
    },
    
    # Interoperability requirements
    {
        "code": "INT-001",
        "name": "W3C Verifiable Credentials Support",
        "description": "Wallet must support W3C Verifiable Credentials data model.",
        "category": RequirementCategory.INTEROPERABILITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "schema_validation",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(c)",
        "metadata": {
            "standards": ["W3C-VC-DATA-MODEL-1.0"],
        },
    },
    {
        "code": "INT-002",
        "name": "OpenID for Verifiable Presentations Support",
        "description": "Wallet must support OpenID for Verifiable Presentations protocol.",
        "category": RequirementCategory.INTEROPERABILITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "api_verification",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(c)",
        "metadata": {
            "standards": ["OPENID4VP"],
        },
    },
    {
        "code": "INT-003",
        "name": "DID Method Support",
        "description": "Wallet must support specified DID methods.",
        "category": RequirementCategory.INTEROPERABILITY,
        "level": RequirementLevel.RECOMMENDED,
        "validation_method": "api_verification",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(c)",
        "metadata": {
            "did_methods": ["did:key", "did:web", "did:ebsi"],
        },
    },
    
    # Usability requirements
    {
        "code": "USA-001",
        "name": "User Interface Accessibility",
        "description": "Wallet interface must be accessible according to WCAG 2.1 AA standards.",
        "category": RequirementCategory.USABILITY,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "manual",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(d)",
        "metadata": {
            "standards": ["WCAG-2.1-AA"],
        },
    },
    {
        "code": "USA-002",
        "name": "Multiple Language Support",
        "description": "Wallet must support multiple EU languages.",
        "category": RequirementCategory.USABILITY,
        "level": RequirementLevel.RECOMMENDED,
        "validation_method": "manual",
        "legal_reference": "eIDAS 2.0 Article 6a(4)(d)",
        "metadata": {
            "language_requirements": ["multilingual_support"],
        },
    },
    
    # Technical requirements
    {
        "code": "TEC-001",
        "name": "Offline Operation",
        "description": "Wallet must support offline credential presentation.",
        "category": RequirementCategory.TECHNICAL,
        "level": RequirementLevel.RECOMMENDED,
        "validation_method": "manual",
        "legal_reference": "eIDAS 2.0 Article 6a(4)",
        "metadata": {
            "offline_capabilities": ["presentation", "verification"],
        },
    },
    {
        "code": "TEC-002",
        "name": "Performance Requirements",
        "description": "Wallet must complete credential operations within acceptable time limits.",
        "category": RequirementCategory.TECHNICAL,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "performance_check",
        "legal_reference": "eIDAS 2.0 Article 6a(4)",
        "metadata": {
            "timing_requirements": {
                "credential_verification_ms": 1000,
                "credential_presentation_ms": 1500,
            },
        },
    },
    
    # Legal requirements
    {
        "code": "LEG-001",
        "name": "Terms and Conditions",
        "description": "Wallet must provide clear terms and conditions that comply with EU law.",
        "category": RequirementCategory.LEGAL,
        "level": RequirementLevel.MANDATORY,
        "validation_method": "manual",
        "legal_reference": "eIDAS 2.0 Article 6a(4), GDPR Article 13",
        "metadata": {
            "legal_documents": ["terms_of_service", "privacy_policy"],
        },
    },
]


async def seed_requirements(
    session: AsyncSession,
    requirements: List[Dict[str, Any]],
    force_update: bool = False,
) -> None:
    """Seed the database with compliance requirements.
    
    Args:
        session: Database session
        requirements: List of requirement data
        force_update: If True, update existing requirements
    """
    for req_data in requirements:
        code = req_data["code"]
        
        # Check if requirement already exists
        result = await session.execute(
            select(ComplianceRequirement).where(ComplianceRequirement.code == code)
        )
        existing = result.scalar_one_or_none()
        
        if existing and not force_update:
            logger.info(f"Requirement {code} already exists, skipping")
            continue
            
        if existing and force_update:
            logger.info(f"Updating existing requirement: {code}")
            
            # Update fields
            for key, value in req_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
                    
            await session.commit()
        else:
            logger.info(f"Creating new requirement: {code}")
            
            # Create new requirement
            requirement = ComplianceRequirement(
                code=req_data["code"],
                name=req_data["name"],
                description=req_data["description"],
                category=req_data["category"],
                level=req_data["level"],
                validation_method=req_data["validation_method"],
                legal_reference=req_data.get("legal_reference"),
                metadata=req_data.get("metadata", {}),
                version="1.0.0",
                is_active=True,
            )
            
            session.add(requirement)
            await session.commit()


async def main(force_update: bool = False) -> None:
    """Seed the database with initial requirements.
    
    Args:
        force_update: If True, update existing requirements
    """
    logger.info("Seeding database with eIDAS 2 compliance requirements")
    
    async with get_session() as session:
        await seed_requirements(session, INITIAL_REQUIREMENTS, force_update)
        
    logger.info("Seeding completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
