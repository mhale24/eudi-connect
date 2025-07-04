"""
Notification service for EUDI-Connect.

This service handles sending notifications for various events,
including credential operations like revocation.
"""
import json
import logging
import uuid
from typing import Any, Dict, Optional, List
import asyncio
import httpx
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.core.config import settings
from eudi_connect.models.credential import CredentialLog
from eudi_connect.models.merchant import Webhook

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, session: AsyncSession):
        """Initialize the notification service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.logger = logger

    async def send_webhook(self, url: str, payload: Dict[str, Any], max_retries: int = 3) -> bool:
        """Send a webhook notification.

        Args:
            url: The webhook URL
            payload: The payload to send
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if successful, False otherwise
        """
        retry_count = 0
        while retry_count <= max_retries:
            try:
                self.logger.debug(f"Sending webhook to {url}")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "EUDI-Connect-Notification-Service/1.0",
                            # Add signing headers or other authentication as needed
                        }
                    )
                    response.raise_for_status()
                    self.logger.debug(f"Webhook to {url} succeeded with status {response.status_code}")
                    return True
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    self.logger.error(f"Failed to send webhook to {url} after {max_retries} attempts: {str(e)}")
                    return False
                self.logger.warning(f"Webhook to {url} failed (attempt {retry_count}/{max_retries}): {str(e)}")
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        return False

    async def get_merchant_webhooks(self, merchant_id: uuid.UUID, event_type: str) -> List[Webhook]:
        """Get all webhooks configured for a merchant and event type.

        Args:
            merchant_id: The merchant ID
            event_type: The event type to filter by

        Returns:
            List of webhook configurations
        """
        stmt = select(Webhook).where(
            Webhook.merchant_id == merchant_id,
            Webhook.event_types.contains([event_type]),
            Webhook.is_active.is_(True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def send_revocation_notification(
        self, 
        credential_log: CredentialLog,
        is_batch: bool = False
    ) -> Dict[str, Any]:
        """Send a notification for a credential revocation.

        Args:
            credential_log: The credential log entry for the revocation
            is_batch: Whether this is part of a batch operation

        Returns:
            Dict with notification status information
        """
        try:
            merchant_id = credential_log.merchant_id
            
            # Get webhooks configured for this merchant and event
            webhooks = await self.get_merchant_webhooks(merchant_id, "credential.revoked")
            
            if not webhooks:
                self.logger.debug(f"No webhooks configured for merchant {merchant_id} and event credential.revoked")
                return {"success": True, "message": "No webhooks configured", "sent_count": 0}
            
            # Prepare the notification payload
            payload = {
                "event": "credential.revoked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "merchant_id": str(merchant_id),
                "data": {
                    "log_id": str(credential_log.id),
                    "credential_id": credential_log.log_metadata.get("credential_id"),
                    "revocation_index": credential_log.log_metadata.get("revocation_index"),
                    "reason": credential_log.log_metadata.get("reason"),
                    "subject_did": credential_log.subject_did,
                    "is_batch_operation": is_batch,
                    "revoked_at": credential_log.created_at.isoformat(),
                }
            }
            
            # Send to all configured webhooks
            results = []
            for webhook in webhooks:
                success = await self.send_webhook(webhook.url, payload)
                results.append({
                    "webhook_id": str(webhook.id),
                    "url": webhook.url,
                    "success": success,
                })
            
            # Log the notification results
            successful = sum(1 for r in results if r["success"])
            self.logger.info(
                f"Sent revocation notification for credential {credential_log.log_metadata.get('credential_id')} "
                f"to {successful}/{len(results)} webhooks"
            )
            
            return {
                "success": True,
                "message": f"Notifications sent to {successful}/{len(results)} webhooks",
                "sent_count": successful,
                "total_count": len(results),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send revocation notification: {str(e)}")
            return {"success": False, "message": f"Failed to send notification: {str(e)}"}

    async def send_batch_revocation_notification(
        self,
        merchant_id: uuid.UUID,
        batch_summary: Dict[str, Any],
        log_ids: List[uuid.UUID]
    ) -> Dict[str, Any]:
        """Send a notification for a batch credential revocation.

        Args:
            merchant_id: The merchant ID
            batch_summary: Summary of the batch operation
            log_ids: List of credential log IDs included in the batch

        Returns:
            Dict with notification status information
        """
        try:
            # Get webhooks configured for this merchant and event
            webhooks = await self.get_merchant_webhooks(merchant_id, "credential.batch_revoked")
            
            if not webhooks:
                self.logger.debug(f"No webhooks configured for merchant {merchant_id} and event credential.batch_revoked")
                return {"success": True, "message": "No webhooks configured", "sent_count": 0}
            
            # Prepare the notification payload
            payload = {
                "event": "credential.batch_revoked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "merchant_id": str(merchant_id),
                "data": {
                    "summary": batch_summary,
                    "log_ids": [str(log_id) for log_id in log_ids],
                    "batch_id": str(uuid.uuid4()),  # Generate a unique ID for this batch notification
                }
            }
            
            # Send to all configured webhooks
            results = []
            for webhook in webhooks:
                success = await self.send_webhook(webhook.url, payload)
                results.append({
                    "webhook_id": str(webhook.id),
                    "url": webhook.url,
                    "success": success,
                })
            
            # Log the notification results
            successful = sum(1 for r in results if r["success"])
            self.logger.info(
                f"Sent batch revocation notification for {batch_summary.get('total', 0)} credentials "
                f"to {successful}/{len(results)} webhooks"
            )
            
            return {
                "success": True,
                "message": f"Batch notifications sent to {successful}/{len(results)} webhooks",
                "sent_count": successful,
                "total_count": len(results),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send batch revocation notification: {str(e)}")
            return {"success": False, "message": f"Failed to send batch notification: {str(e)}"}
