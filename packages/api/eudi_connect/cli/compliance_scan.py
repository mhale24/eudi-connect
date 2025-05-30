#!/usr/bin/env python3
"""eIDAS 2 Compliance Scanner CLI.

This command-line tool allows you to run compliance scans on wallet implementations
and view the results. It provides an easy way to test compliance with eIDAS 2
requirements without using the API.

Usage:
    python -m eudi_connect.cli.compliance_scan run --wallet-name "My Wallet" --wallet-version "1.0.0" --wallet-provider "My Company"
    python -m eudi_connect.cli.compliance_scan list-requirements
    python -m eudi_connect.cli.compliance_scan list-scans
    python -m eudi_connect.cli.compliance_scan show-results SCAN_ID
"""
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from eudi_connect.db.session import get_session
from eudi_connect.models.compliance.models import (
    RequirementCategory,
    RequirementLevel,
    ScanStatus,
    ResultStatus,
)
from eudi_connect.services.compliance_scanner import ComplianceScannerService
from eudi_connect.models.compliance.seed_requirements import seed_requirements, INITIAL_REQUIREMENTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create rich console
console = Console()


@click.group()
def cli():
    """eIDAS 2 Compliance Scanner CLI.
    
    Run compliance scans against wallet implementations and view results.
    """
    pass


@cli.command("run")
@click.option("--wallet-name", required=True, help="Name of the wallet to scan")
@click.option("--wallet-version", required=True, help="Version of the wallet")
@click.option("--wallet-provider", required=True, help="Provider of the wallet")
@click.option("--name", default=None, help="Name for this scan (default: auto-generated)")
@click.option("--description", default=None, help="Description for this scan")
@click.option("--merchant-id", default=None, help="Merchant ID (default: test merchant)")
@click.option("--requirement", "-r", multiple=True, help="Specific requirement ID(s) to scan")
@click.option("--category", type=click.Choice([c.value for c in RequirementCategory]), 
              help="Filter requirements by category")
@click.option("--level", type=click.Choice([l.value for l in RequirementLevel]),
              help="Filter requirements by level")
@click.option("--wait/--no-wait", default=True, help="Wait for scan completion")
@click.option("--output", "-o", type=click.File("w"), default="-", 
              help="Output file for results (default: stdout)")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text",
              help="Output format (default: text)")
@click.option("--seed-db/--no-seed-db", default=True, 
              help="Seed database with requirements if empty")
async def run_scan(
    wallet_name: str,
    wallet_version: str,
    wallet_provider: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    merchant_id: Optional[str] = None,
    requirement: List[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    wait: bool = True,
    output=None,
    format: str = "text",
    seed_db: bool = True,
):
    """Run a compliance scan against a wallet implementation."""
    # Generate scan name if not provided
    if not name:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        name = f"Scan-{wallet_name}-{timestamp}"
        
    # Use test merchant ID if not provided
    if not merchant_id:
        merchant_id = "00000000-0000-0000-0000-000000000001"
    
    # Convert merchant ID to UUID
    try:
        merchant_id_uuid = uuid.UUID(merchant_id)
    except ValueError:
        console.print(f"[bold red]Error:[/] Invalid merchant ID: {merchant_id}")
        sys.exit(1)
        
    # Convert requirement IDs to UUIDs
    requirement_uuids = None
    if requirement:
        try:
            requirement_uuids = [uuid.UUID(r) for r in requirement]
        except ValueError as e:
            console.print(f"[bold red]Error:[/] Invalid requirement ID: {e}")
            sys.exit(1)
    
    # Create config
    config = {
        "cli_generated": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if category:
        config["category_filter"] = category
    if level:
        config["level_filter"] = level
    
    # Get a database session
    async with get_session() as session:
        # Seed database if requested
        if seed_db:
            console.print("Checking if database needs to be seeded with requirements...")
            scanner = ComplianceScannerService(session)
            requirements = await scanner.get_active_requirements()
            
            if not requirements:
                console.print("[yellow]No requirements found in database, seeding...[/]")
                await seed_requirements(session, INITIAL_REQUIREMENTS)
                console.print("[green]Database seeded successfully[/]")
                
        # Create scanner service
        scanner = ComplianceScannerService(session)
        
        # Create scan
        console.print(f"Creating compliance scan: [bold]{name}[/]")
        scan = await scanner.create_scan(
            merchant_id=merchant_id_uuid,
            name=name,
            wallet_name=wallet_name,
            wallet_version=wallet_version,
            wallet_provider=wallet_provider,
            description=description,
            config=config,
        )
        
        console.print(f"Scan created with ID: [bold cyan]{scan.id}[/]")
        
        # Run scan
        console.print("Starting scan...")
        
        if wait:
            with Progress() as progress:
                task = progress.add_task("[cyan]Running scan...", total=None)
                
                # Run scan
                scan = await scanner.run_scan(scan.id, requirement_uuids)
                
                # Mark task as complete
                progress.update(task, completed=100)
            
            console.print(f"[bold green]Scan completed:[/] {scan.status}")
            console.print(f"Results: {scan.passed_requirements} passed, "
                         f"{scan.failed_requirements} failed, "
                         f"{scan.warning_requirements} warnings, "
                         f"{scan.manual_check_requirements} manual checks")
            
            # Show results
            await _display_scan_results(scanner, scan.id, format, output)
        else:
            console.print(f"[bold yellow]Scan started in background[/]")
            console.print(f"Use the following command to check results later:")
            console.print(f"  python -m eudi_connect.cli.compliance_scan show-results {scan.id}")


@cli.command("list-requirements")
@click.option("--category", type=click.Choice([c.value for c in RequirementCategory]), 
              help="Filter by category")
@click.option("--level", type=click.Choice([l.value for l in RequirementLevel]),
              help="Filter by level")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text",
              help="Output format (default: text)")
@click.option("--output", "-o", type=click.File("w"), default="-",
              help="Output file (default: stdout)")
async def list_requirements(
    category: Optional[str] = None,
    level: Optional[str] = None,
    format: str = "text",
    output=None,
):
    """List compliance requirements."""
    # Convert string enum values to enum instances
    category_enum = RequirementCategory(category) if category else None
    level_enum = RequirementLevel(level) if level else None
    
    async with get_session() as session:
        scanner = ComplianceScannerService(session)
        requirements = await scanner.get_active_requirements(category_enum, level_enum)
        
        if not requirements:
            console.print("[yellow]No requirements found[/]")
            return
        
        if format == "json":
            # Convert to dict for JSON serialization
            result = []
            for req in requirements:
                req_dict = {
                    "id": str(req.id),
                    "code": req.code,
                    "name": req.name,
                    "description": req.description,
                    "category": req.category.value,
                    "level": req.level.value,
                    "validation_method": req.validation_method,
                    "legal_reference": req.legal_reference,
                }
                result.append(req_dict)
                
            # Write JSON to output
            json.dump(result, output, indent=2)
        else:
            # Create table for text output
            table = Table(title="eIDAS 2 Compliance Requirements")
            table.add_column("Code", style="cyan")
            table.add_column("Name")
            table.add_column("Category", style="green")
            table.add_column("Level", style="yellow")
            table.add_column("Legal Reference", style="blue")
            
            for req in requirements:
                table.add_row(
                    req.code,
                    req.name,
                    req.category.value,
                    req.level.value,
                    req.legal_reference or "",
                )
                
            console = Console(file=output)
            console.print(table)


@cli.command("list-scans")
@click.option("--merchant-id", default=None, help="Merchant ID (default: test merchant)")
@click.option("--status", type=click.Choice([s.value for s in ScanStatus]), 
              help="Filter by status")
@click.option("--limit", type=int, default=10, help="Maximum number of scans to show")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text",
              help="Output format (default: text)")
@click.option("--output", "-o", type=click.File("w"), default="-",
              help="Output file (default: stdout)")
async def list_scans(
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    format: str = "text",
    output=None,
):
    """List compliance scans."""
    # Use test merchant ID if not provided
    if not merchant_id:
        merchant_id = "00000000-0000-0000-0000-000000000001"
        
    # Convert merchant ID to UUID
    try:
        merchant_id_uuid = uuid.UUID(merchant_id)
    except ValueError:
        console.print(f"[bold red]Error:[/] Invalid merchant ID: {merchant_id}")
        sys.exit(1)
        
    # Convert status string to enum instance
    status_enum = ScanStatus(status) if status else None
    
    async with get_session() as session:
        # Create query to get scans
        from sqlalchemy import select, desc
        from eudi_connect.models.compliance.models import ComplianceScan
        
        stmt = select(ComplianceScan).where(
            ComplianceScan.merchant_id == merchant_id_uuid
        )
        
        if status_enum:
            stmt = stmt.where(ComplianceScan.status == status_enum)
            
        stmt = stmt.order_by(desc(ComplianceScan.created_at)).limit(limit)
        
        result = await session.execute(stmt)
        scans = result.scalars().all()
        
        if not scans:
            console.print("[yellow]No scans found[/]")
            return
            
        if format == "json":
            # Convert to dict for JSON serialization
            result = []
            for scan in scans:
                scan_dict = {
                    "id": str(scan.id),
                    "name": scan.name,
                    "status": scan.status.value,
                    "wallet_name": scan.wallet_name,
                    "wallet_version": scan.wallet_version,
                    "wallet_provider": scan.wallet_provider,
                    "total_requirements": scan.total_requirements,
                    "passed_requirements": scan.passed_requirements,
                    "failed_requirements": scan.failed_requirements,
                    "warning_requirements": scan.warning_requirements,
                    "created_at": scan.created_at.isoformat(),
                    "started_at": scan.started_at.isoformat() if scan.started_at else None,
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                }
                result.append(scan_dict)
                
            # Write JSON to output
            json.dump(result, output, indent=2)
        else:
            # Create table for text output
            table = Table(title="Compliance Scans")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Status", style="green")
            table.add_column("Wallet")
            table.add_column("Results", style="yellow")
            table.add_column("Created", style="blue")
            
            for scan in scans:
                status_style = {
                    ScanStatus.PENDING: "yellow",
                    ScanStatus.IN_PROGRESS: "blue",
                    ScanStatus.COMPLETED: "green",
                    ScanStatus.FAILED: "red",
                }.get(scan.status, "")
                
                results = ""
                if scan.status == ScanStatus.COMPLETED:
                    results = f"{scan.passed_requirements}/{scan.total_requirements} passed"
                
                table.add_row(
                    str(scan.id),
                    scan.name,
                    f"[{status_style}]{scan.status.value}[/]",
                    f"{scan.wallet_name} {scan.wallet_version}",
                    results,
                    scan.created_at.strftime("%Y-%m-%d %H:%M"),
                )
                
            console = Console(file=output)
            console.print(table)


@cli.command("show-results")
@click.argument("scan_id")
@click.option("--status", type=click.Choice([s.value for s in ResultStatus]), 
              help="Filter by result status")
@click.option("--format", "-f", type=click.Choice(["text", "json", "html"]), default="text",
              help="Output format (default: text)")
@click.option("--output", "-o", type=click.File("w"), default="-",
              help="Output file (default: stdout)")
async def show_results(
    scan_id: str,
    status: Optional[str] = None,
    format: str = "text",
    output=None,
):
    """Show results for a specific compliance scan."""
    # Convert scan ID to UUID
    try:
        scan_id_uuid = uuid.UUID(scan_id)
    except ValueError:
        console.print(f"[bold red]Error:[/] Invalid scan ID: {scan_id}")
        sys.exit(1)
        
    # Convert status string to enum instance
    status_enum = ResultStatus(status) if status else None
    
    async with get_session() as session:
        scanner = ComplianceScannerService(session)
        
        try:
            # Generate report
            report_format = "json" if format == "json" else "json"  # Use JSON for all formats
            report = await scanner.generate_report(scan_id_uuid, report_format)
            
            # Filter by status if specified
            if status_enum:
                report["results"] = [r for r in report["results"] 
                                    if r.get("status") == status_enum.value]
            
            if format == "json":
                # Write JSON to output
                json.dump(report, output, indent=2)
            elif format == "html":
                # For HTML, we would generate HTML in the scanner service
                # For now, just use a simple template
                html = f"""
                <html>
                <head>
                    <title>Compliance Scan Report: {report['name']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        h1 {{ color: #2c3e50; }}
                        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                        .result {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
                        .pass {{ background: #d4edda; }}
                        .fail {{ background: #f8d7da; }}
                        .warning {{ background: #fff3cd; }}
                        .manual {{ background: #e2e3e5; }}
                        .na {{ background: #f8f9fa; }}
                    </style>
                </head>
                <body>
                    <h1>Compliance Scan Report</h1>
                    <div class="summary">
                        <h2>{report['name']}</h2>
                        <p><strong>Wallet:</strong> {report['wallet']['name']} {report['wallet']['version']}</p>
                        <p><strong>Provider:</strong> {report['wallet']['provider']}</p>
                        <p><strong>Status:</strong> {report['status']}</p>
                        <p><strong>Results:</strong> {report['summary']['passed']}/{report['summary']['total']} passed
                           ({report['summary']['compliance_score']:.1f}% compliance)</p>
                    </div>
                    
                    <h2>Detailed Results</h2>
                """
                
                # Add results
                for result in report["results"]:
                    req = result.get("requirement", {})
                    status_class = {
                        "pass": "pass",
                        "fail": "fail",
                        "warning": "warning",
                        "manual_check_required": "manual",
                        "not_applicable": "na",
                    }.get(result.get("status"), "")
                    
                    html += f"""
                    <div class="result {status_class}">
                        <h3>{req.get('code', 'Unknown')} - {req.get('name', 'Unknown')}</h3>
                        <p><strong>Category:</strong> {req.get('category', 'Unknown')}</p>
                        <p><strong>Level:</strong> {req.get('level', 'Unknown')}</p>
                        <p><strong>Status:</strong> {result.get('status', 'Unknown')}</p>
                        <p><strong>Message:</strong> {result.get('message', '')}</p>
                    </div>
                    """
                
                html += """
                </body>
                </html>
                """
                
                output.write(html)
            else:
                # Create tables for text output
                console = Console(file=output)
                
                # Summary table
                summary = Table(title=f"Compliance Scan: {report['name']}")
                summary.add_column("Wallet")
                summary.add_column("Status", style="cyan")
                summary.add_column("Results", style="green")
                summary.add_column("Score", style="yellow")
                summary.add_column("Started", style="blue")
                summary.add_column("Completed", style="blue")
                
                status_style = {
                    "pending": "yellow",
                    "in_progress": "blue",
                    "completed": "green",
                    "failed": "red",
                }.get(report["status"], "")
                
                summary.add_row(
                    f"{report['wallet']['name']} {report['wallet']['version']}",
                    f"[{status_style}]{report['status']}[/]",
                    f"{report['summary']['passed']}/{report['summary']['total']} passed",
                    f"{report['summary']['compliance_score']:.1f}%",
                    report["started_at"] or "N/A",
                    report["completed_at"] or "N/A",
                )
                
                console.print(summary)
                console.print()
                
                # Results table
                results_table = Table(title="Detailed Results")
                results_table.add_column("Code", style="cyan")
                results_table.add_column("Name")
                results_table.add_column("Category", style="blue")
                results_table.add_column("Level", style="magenta")
                results_table.add_column("Status", style="green")
                results_table.add_column("Message")
                
                for result in report["results"]:
                    req = result.get("requirement", {})
                    
                    status_style = {
                        "pass": "green",
                        "fail": "red",
                        "warning": "yellow",
                        "manual_check_required": "blue",
                        "not_applicable": "dim",
                    }.get(result.get("status"), "")
                    
                    results_table.add_row(
                        req.get("code", "Unknown"),
                        req.get("name", "Unknown"),
                        req.get("category", "Unknown"),
                        req.get("level", "Unknown"),
                        f"[{status_style}]{result.get('status', 'Unknown')}[/]",
                        result.get("message", ""),
                    )
                
                console.print(results_table)
                
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            sys.exit(1)


async def _display_scan_results(
    scanner: ComplianceScannerService,
    scan_id: uuid.UUID,
    format: str,
    output,
):
    """Display scan results."""
    # Redirect to show-results command functionality
    await show_results(str(scan_id), None, format, output)


def main():
    """Run the CLI application."""
    try:
        cli(_anyio_backend="asyncio")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
