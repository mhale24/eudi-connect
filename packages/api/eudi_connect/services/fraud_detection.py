"""
AI-powered fraud detection service.
"""
import asyncio
import json
import logging
import pickle
import base64
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import numpy as np
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.fraud_detection import (
    FraudAlert, FraudPattern, UserRiskProfile, MLModel, 
    FraudDetectionMetrics, RiskLevel, FraudDetectionRule
)
from eudi_connect.models.analytics import AnalyticsEvent, EventType
from eudi_connect.services.analytics import get_analytics_service

logger = logging.getLogger(__name__)


class FraudDetectionEngine:
    """Core fraud detection engine with AI capabilities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = get_analytics_service(db)
        
        # Rule thresholds (configurable per merchant)
        self.default_thresholds = {
            "velocity_max_requests_per_minute": 10,
            "velocity_max_requests_per_hour": 100,
            "geolocation_max_distance_km": 1000,
            "behavioral_deviation_threshold": 0.7,
            "ml_anomaly_threshold": 0.8,
            "ip_reputation_min_score": 0.3,
            "time_pattern_deviation_hours": 6
        }
    
    async def analyze_event(
        self,
        merchant_id: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[FraudAlert]:
        """
        Analyze an event for fraud indicators.
        
        Returns a FraudAlert if fraud is detected, None otherwise.
        """
        try:
            # Get user risk profile
            risk_profile = await self._get_or_create_user_risk_profile(
                merchant_id, user_id
            )
            
            # Run all detection rules
            detection_results = await self._run_detection_rules(
                merchant_id=merchant_id,
                event_data=event_data,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                risk_profile=risk_profile
            )
            
            # Calculate overall risk score
            risk_score, triggered_rules = self._calculate_risk_score(detection_results)
            
            # Determine if alert should be created
            # Update user risk profile
            is_flagged = risk_score >= 0.5  # Configurable threshold
            await self._update_user_risk_profile(risk_profile, risk_score, is_flagged)
            
            if is_flagged:
                alert = await self._create_fraud_alert(
                    merchant_id=merchant_id,
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    risk_score=risk_score,
                    triggered_rules=triggered_rules,
                    detection_data=detection_results,
                    event_data=event_data
                )
                
                return {
                    "risk_score": risk_score,
                    "is_flagged": True,
                    "triggered_rules": triggered_rules,
                    "alert_id": alert.id if alert else None,
                    "detection_results": detection_results
                }
            else:
                return {
                    "risk_score": risk_score,
                    "is_flagged": False,
                    "triggered_rules": triggered_rules,
                    "alert_id": None,
                    "detection_results": detection_results
                }
            
        except Exception as e:
            logger.error(f"Error in fraud detection analysis: {e}", exc_info=True)
            return None
    
    async def _run_detection_rules(
        self,
        merchant_id: str,
        event_data: Dict[str, Any],
        user_id: Optional[str],
        session_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Run all fraud detection rules and return results."""
        results = {}
        
        # Velocity checks
        results["velocity"] = await self._check_velocity_anomalies(
            merchant_id, user_id, ip_address
        )
        
        # Geolocation anomalies
        if ip_address:
            results["geolocation"] = await self._check_geolocation_anomalies(
                merchant_id, user_id, ip_address, risk_profile
            )
        
        # Device fingerprinting
        if user_agent:
            results["device"] = await self._check_device_anomalies(
                user_id, user_agent, risk_profile
            )
        
        # Behavioral pattern analysis
        results["behavioral"] = await self._check_behavioral_anomalies(
            merchant_id, user_id, event_data, risk_profile
        )
        
        # Credential reuse detection
        results["credential_reuse"] = await self._check_credential_reuse(
            merchant_id, event_data
        )
        
        # Time pattern anomalies
        results["time_pattern"] = await self._check_time_pattern_anomalies(
            user_id, risk_profile
        )
        
        # IP reputation check
        if ip_address:
            results["ip_reputation"] = await self._check_ip_reputation(ip_address)
        
        # ML-based anomaly detection
        results["ml_anomaly"] = await self._run_ml_anomaly_detection(
            merchant_id, user_id, event_data, risk_profile
        )
        
        return results
    
    async def _check_velocity_anomalies(
        self, merchant_id: str, user_id: Optional[str], ip_address: Optional[str]
    ) -> Dict[str, Any]:
        """Check for velocity-based anomalies."""
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        # Count recent events
        filters = [AnalyticsEvent.merchant_id == merchant_id]
        
        if user_id:
            filters.append(AnalyticsEvent.user_id == user_id)
        elif ip_address:
            filters.append(AnalyticsEvent.ip_address == ip_address)
        
        # Events in last minute
        minute_query = select(func.count(AnalyticsEvent.id)).where(
            and_(
                *filters,
                AnalyticsEvent.created_at >= one_minute_ago
            )
        )
        minute_result = await self.db.execute(minute_query)
        minute_count = minute_result.scalar() or 0
        
        # Events in last hour
        hour_query = select(func.count(AnalyticsEvent.id)).where(
            and_(
                *filters,
                AnalyticsEvent.created_at >= one_hour_ago
            )
        )
        hour_result = await self.db.execute(hour_query)
        hour_count = hour_result.scalar() or 0
        
        # Calculate risk scores
        minute_risk = min(minute_count / self.default_thresholds["velocity_max_requests_per_minute"], 1.0)
        hour_risk = min(hour_count / self.default_thresholds["velocity_max_requests_per_hour"], 1.0)
        
        return {
            "risk_score": max(minute_risk, hour_risk),
            "minute_count": minute_count,
            "hour_count": hour_count,
            "triggered": minute_risk > 0.8 or hour_risk > 0.8
        }
    
    async def _check_geolocation_anomalies(
        self, merchant_id: str, user_id: Optional[str], ip_address: str, risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Check for geolocation-based anomalies."""
        # This would integrate with a geolocation service
        # For now, we'll simulate the logic
        
        current_location = await self._get_ip_location(ip_address)
        if not current_location:
            return {"risk_score": 0.0, "triggered": False}
        
        # Get user's typical locations from risk profile
        location_patterns = risk_profile.location_patterns or {}
        typical_locations = location_patterns.get("typical_locations", [])
        
        if not typical_locations:
            # First time seeing this user, low risk
            return {
                "risk_score": 0.1,
                "triggered": False,
                "current_location": current_location,
                "is_new_location": True
            }
        
        # Calculate distance to nearest typical location
        min_distance = float('inf')
        for location in typical_locations:
            distance = self._calculate_distance(current_location, location)
            min_distance = min(min_distance, distance)
        
        # Risk increases with distance
        max_distance = self.default_thresholds["geolocation_max_distance_km"]
        risk_score = min(min_distance / max_distance, 1.0)
        
        return {
            "risk_score": risk_score,
            "triggered": risk_score > 0.7,
            "current_location": current_location,
            "min_distance_km": min_distance,
            "is_anomalous": min_distance > max_distance * 0.5
        }
    
    async def _check_device_anomalies(
        self, user_id: Optional[str], user_agent: str, risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Check for device fingerprinting anomalies."""
        if not user_id:
            return {"risk_score": 0.0, "triggered": False}
        
        device_fingerprints = risk_profile.device_fingerprints or {}
        known_devices = device_fingerprints.get("known_user_agents", [])
        
        # Simple user agent matching (could be enhanced with more sophisticated fingerprinting)
        device_hash = hash(user_agent)
        is_known_device = any(hash(ua) == device_hash for ua in known_devices)
        
        if is_known_device:
            return {
                "risk_score": 0.0,
                "triggered": False,
                "is_known_device": True
            }
        else:
            # New device - moderate risk
            risk_score = 0.3 if len(known_devices) > 0 else 0.1
            return {
                "risk_score": risk_score,
                "triggered": risk_score > 0.5,
                "is_known_device": False,
                "device_hash": str(device_hash)
            }
    
    async def _check_behavioral_anomalies(
        self, merchant_id: str, user_id: Optional[str], event_data: Dict[str, Any], risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Check for behavioral pattern anomalies."""
        if not user_id:
            return {"risk_score": 0.0, "triggered": False}
        
        behavioral_profile = risk_profile.behavioral_profile or {}
        
        # Analyze current behavior vs baseline
        current_behavior = self._extract_behavioral_features(event_data)
        baseline_behavior = behavioral_profile.get("baseline", {})
        
        if not baseline_behavior:
            return {
                "risk_score": 0.0,
                "triggered": False,
                "is_baseline_available": False
            }
        
        # Calculate behavioral deviation
        deviation_score = self._calculate_behavioral_deviation(
            current_behavior, baseline_behavior
        )
        
        threshold = self.default_thresholds["behavioral_deviation_threshold"]
        
        return {
            "risk_score": deviation_score,
            "triggered": deviation_score > threshold,
            "deviation_score": deviation_score,
            "current_behavior": current_behavior
        }
    
    async def _check_credential_reuse(
        self, merchant_id: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for credential reuse patterns."""
        # Look for patterns that might indicate credential stuffing or reuse
        credential_type = event_data.get("credential_type")
        subject_did = event_data.get("subject_did")
        
        if not credential_type or not subject_did:
            return {"risk_score": 0.0, "triggered": False}
        
        # Check for recent similar credential requests
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = select(func.count(AnalyticsEvent.id)).where(
            and_(
                AnalyticsEvent.merchant_id == merchant_id,
                AnalyticsEvent.event_type == EventType.CREDENTIAL_ISSUED,
                AnalyticsEvent.created_at >= one_hour_ago,
                AnalyticsEvent.event_data.contains(f'"credential_type": "{credential_type}"')
            )
        )
        
        result = await self.db.execute(query)
        recent_count = result.scalar() or 0
        
        # Risk increases with frequency
        risk_score = min(recent_count / 10.0, 1.0)  # Max risk at 10+ requests
        
        return {
            "risk_score": risk_score,
            "triggered": risk_score > 0.6,
            "recent_count": recent_count,
            "credential_type": credential_type
        }
    
    async def _check_time_pattern_anomalies(
        self, user_id: Optional[str], risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Check for time-based pattern anomalies."""
        if not user_id:
            return {"risk_score": 0.0, "triggered": False}
        
        current_hour = datetime.utcnow().hour
        time_patterns = risk_profile.time_patterns or {}
        typical_hours = time_patterns.get("typical_hours", [])
        
        if not typical_hours:
            return {
                "risk_score": 0.1,
                "triggered": False,
                "is_baseline_available": False
            }
        
        # Calculate deviation from typical usage hours
        min_deviation = min(abs(current_hour - hour) for hour in typical_hours)
        max_deviation = self.default_thresholds["time_pattern_deviation_hours"]
        
        risk_score = min(min_deviation / max_deviation, 1.0)
        
        return {
            "risk_score": risk_score,
            "triggered": risk_score > 0.7,
            "current_hour": current_hour,
            "min_deviation": min_deviation,
            "typical_hours": typical_hours
        }
    
    async def _check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP reputation against threat intelligence."""
        # This would integrate with threat intelligence services
        # For now, we'll simulate basic checks
        
        # Simple heuristics for demo
        reputation_score = 0.8  # Default good reputation
        
        # Check for common suspicious patterns
        if ip_address.startswith("10.") or ip_address.startswith("192.168."):
            reputation_score = 0.9  # Private IPs are generally safe
        elif ip_address.startswith("127."):
            reputation_score = 1.0  # Localhost
        
        risk_score = 1.0 - reputation_score
        min_score = self.default_thresholds["ip_reputation_min_score"]
        
        return {
            "risk_score": risk_score,
            "triggered": reputation_score < min_score,
            "reputation_score": reputation_score,
            "ip_address": ip_address
        }
    
    async def _run_ml_anomaly_detection(
        self, merchant_id: str, user_id: Optional[str], event_data: Dict[str, Any], risk_profile: UserRiskProfile
    ) -> Dict[str, Any]:
        """Run ML-based anomaly detection."""
        try:
            # Get active ML model for this merchant
            model = await self._get_active_ml_model(merchant_id)
            if not model:
                return {"risk_score": 0.0, "triggered": False, "model_available": False}
            
            # Extract features for ML model
            features = await self._extract_ml_features(
                merchant_id, user_id, event_data, risk_profile
            )
            
            # Run prediction
            anomaly_score = await self._predict_anomaly(model, features)
            
            threshold = self.default_thresholds["ml_anomaly_threshold"]
            
            return {
                "risk_score": anomaly_score,
                "triggered": anomaly_score > threshold,
                "model_name": model.model_name,
                "model_version": model.model_version,
                "features_used": list(features.keys())
            }
            
        except Exception as e:
            logger.error(f"ML anomaly detection error: {e}")
            return {"risk_score": 0.0, "triggered": False, "error": str(e)}
    
    def _calculate_risk_score(self, detection_results: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate overall risk score from individual rule results."""
        total_score = 0.0
        triggered_rules = []
        rule_count = 0
        
        # Weight different rules
        rule_weights = {
            "velocity": 0.2,
            "geolocation": 0.15,
            "device": 0.1,
            "behavioral": 0.2,
            "credential_reuse": 0.15,
            "time_pattern": 0.1,
            "ip_reputation": 0.1,
            "ml_anomaly": 0.3
        }
        
        for rule_name, result in detection_results.items():
            if isinstance(result, dict) and "risk_score" in result:
                weight = rule_weights.get(rule_name, 0.1)
                total_score += result["risk_score"] * weight
                rule_count += 1
                
                if result.get("triggered", False):
                    triggered_rules.append(rule_name)
        
        # Normalize score
        if rule_count > 0:
            # Don't divide by rule_count since weights should sum to 1
            pass
        
        return min(total_score, 1.0), triggered_rules
    
    async def _create_fraud_alert(
        self,
        merchant_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        risk_score: float,
        triggered_rules: List[str],
        detection_data: Dict[str, Any],
        event_data: Dict[str, Any]
    ) -> FraudAlert:
        """Create a fraud alert."""
        
        # Determine risk level
        if risk_score >= 0.9:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.5:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Determine alert type based on triggered rules
        alert_type = "general_fraud"
        if "velocity" in triggered_rules:
            alert_type = "velocity_anomaly"
        elif "ml_anomaly" in triggered_rules:
            alert_type = "ml_detected_anomaly"
        elif "geolocation" in triggered_rules:
            alert_type = "geolocation_anomaly"
        
        alert = FraudAlert(
            merchant_id=merchant_id,
            user_id=user_id,
            alert_type=alert_type,
            risk_level=risk_level,
            confidence_score=risk_score,
            triggered_rules=triggered_rules,
            detection_data=detection_data,
            context_data=event_data,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(alert)
        await self.db.commit()
        
        logger.warning(
            f"Fraud alert created: {alert_type} (risk: {risk_level}, score: {risk_score:.2f}) "
            f"for merchant {merchant_id}, user {user_id}"
        )
        
        return alert
    
    async def _get_or_create_user_risk_profile(
        self, merchant_id: str, user_id: Optional[str]
    ) -> UserRiskProfile:
        """Get or create user risk profile."""
        if not user_id:
            # Create temporary profile for anonymous users
            return UserRiskProfile(
                merchant_id=merchant_id,
                user_id="anonymous",
                current_risk_score=0.0,
                risk_level=RiskLevel.LOW
            )
        
        query = select(UserRiskProfile).where(
            and_(
                UserRiskProfile.merchant_id == merchant_id,
                UserRiskProfile.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = UserRiskProfile(
                merchant_id=merchant_id,
                user_id=user_id,
                current_risk_score=0.0,
                risk_level=RiskLevel.LOW
            )
            self.db.add(profile)
            await self.db.commit()
        
        return profile
    
    async def _update_user_risk_profile(
        self, profile: UserRiskProfile, risk_score: float, is_alert: bool
    ) -> None:
        """Update user risk profile with new activity."""
        # Update risk score (exponential moving average)
        alpha = 0.3  # Learning rate
        profile.current_risk_score = (
            alpha * risk_score + (1 - alpha) * profile.current_risk_score
        )
        
        # Update risk level
        if profile.current_risk_score >= 0.7:
            profile.risk_level = RiskLevel.HIGH
        elif profile.current_risk_score >= 0.5:
            profile.risk_level = RiskLevel.MEDIUM
        else:
            profile.risk_level = RiskLevel.LOW
        
        # Update activity counters (handle None values)
        profile.total_sessions = (profile.total_sessions or 0) + 1
        
        if is_alert:
            profile.recent_alerts_count = (profile.recent_alerts_count or 0) + 1
            profile.last_alert_date = datetime.utcnow()
        
        profile.updated_at = datetime.utcnow()
        await self.db.commit()
    
    # Helper methods
    
    async def _get_ip_location(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get geolocation for IP address."""
        # This would integrate with a geolocation service like MaxMind
        # For now, return mock data
        return {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "US"
        }
    
    def _calculate_distance(self, loc1: Dict[str, Any], loc2: Dict[str, Any]) -> float:
        """Calculate distance between two locations in kilometers."""
        # Haversine formula
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = radians(loc1["latitude"]), radians(loc1["longitude"])
        lat2, lon2 = radians(loc2["latitude"]), radians(loc2["longitude"])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r
    
    def _extract_behavioral_features(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral features from event data."""
        return {
            "event_type": event_data.get("event_type", "unknown"),
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "has_credential_type": "credential_type" in event_data,
            "data_complexity": len(str(event_data))
        }
    
    def _calculate_behavioral_deviation(
        self, current: Dict[str, Any], baseline: Dict[str, Any]
    ) -> float:
        """Calculate behavioral deviation score."""
        # Simple deviation calculation
        # In practice, this would use more sophisticated ML techniques
        
        deviations = []
        
        for key in baseline:
            if key in current:
                if isinstance(baseline[key], (int, float)) and isinstance(current[key], (int, float)):
                    baseline_val = baseline[key]
                    current_val = current[key]
                    if baseline_val != 0:
                        deviation = abs(current_val - baseline_val) / baseline_val
                        deviations.append(min(deviation, 1.0))
        
        return sum(deviations) / len(deviations) if deviations else 0.0
    
    async def _get_active_ml_model(self, merchant_id: str) -> Optional[MLModel]:
        """Get active ML model for merchant."""
        query = select(MLModel).where(
            and_(
                or_(MLModel.merchant_id == merchant_id, MLModel.merchant_id.is_(None)),
                MLModel.is_active == True,
                MLModel.is_production == True
            )
        ).order_by(desc(MLModel.created_at))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _extract_ml_features(
        self, merchant_id: str, user_id: Optional[str], event_data: Dict[str, Any], risk_profile: UserRiskProfile
    ) -> Dict[str, float]:
        """Extract features for ML model."""
        features = {
            "hour_of_day": float(datetime.utcnow().hour),
            "day_of_week": float(datetime.utcnow().weekday()),
            "user_risk_score": risk_profile.current_risk_score,
            "account_age_days": float(risk_profile.account_age_days or 0),
            "total_sessions": float(risk_profile.total_sessions),
            "recent_alerts": float(risk_profile.recent_alerts_count),
            "success_rate": (
                risk_profile.successful_authentications / 
                max(risk_profile.total_sessions, 1)
            )
        }
        
        return features
    
    async def _predict_anomaly(self, model: MLModel, features: Dict[str, float]) -> float:
        """Run ML model prediction."""
        try:
            # In a real implementation, this would load and run the actual ML model
            # For now, we'll simulate with a simple heuristic
            
            # Simulate anomaly detection based on features
            risk_factors = [
                features.get("user_risk_score", 0.0),
                1.0 if features.get("recent_alerts", 0) > 0 else 0.0,
                1.0 if features.get("success_rate", 1.0) < 0.8 else 0.0
            ]
            
            return sum(risk_factors) / len(risk_factors)
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return 0.0


class FraudDetectionService:
    """Service wrapper for fraud detection functionality."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = FraudDetectionEngine(db)
    
    async def analyze_event(
        self,
        merchant_id: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[FraudAlert]:
        """Analyze an event for fraud indicators."""
        return await self.engine.analyze_event(
            merchant_id=merchant_id,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_fraud_alerts(
        self,
        merchant_id: str,
        limit: int = 100,
        offset: int = 0,
        risk_level: Optional[RiskLevel] = None
    ) -> List[FraudAlert]:
        """Get fraud alerts for a merchant."""
        query = select(FraudAlert).where(FraudAlert.merchant_id == merchant_id)
        
        if risk_level:
            query = query.where(FraudAlert.risk_level == risk_level)
        
        query = query.order_by(desc(FraudAlert.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_risk_profile(
        self, merchant_id: str, user_id: str
    ) -> Optional[UserRiskProfile]:
        """Get user risk profile."""
        query = select(UserRiskProfile).where(
            and_(
                UserRiskProfile.merchant_id == merchant_id,
                UserRiskProfile.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


def get_fraud_detection_engine(db: AsyncSession) -> FraudDetectionEngine:
    """Get fraud detection engine instance."""
    return FraudDetectionEngine(db)


def get_fraud_detection_service(db: AsyncSession) -> FraudDetectionService:
    """Get fraud detection service instance."""
    return FraudDetectionService(db)