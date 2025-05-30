"""Collaborative filtering for template recommendations."""
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel

from .template_analytics import TemplateAnalytics, EventType, TimeRange


class UserProfile(BaseModel):
    """User interaction profile."""
    merchant_id: str
    template_interactions: Dict[str, float]  # template_id -> interaction score
    tag_preferences: Dict[str, float]  # tag -> preference score
    last_active: datetime


class TemplateProfile(BaseModel):
    """Template profile for recommendations."""
    template_id: str
    interaction_score: float
    similarity_score: float
    tag_match_score: float
    final_score: float


class CollaborativeFilter:
    """Collaborative filtering system for templates."""

    def __init__(
        self,
        analytics: TemplateAnalytics,
        time_window: TimeRange = TimeRange.LAST_30D,
        min_interactions: int = 3,
    ):
        """Initialize collaborative filter.

        Args:
            analytics: Template analytics instance
            time_window: Time window for considering interactions
            min_interactions: Minimum interactions for recommendations
        """
        self.analytics = analytics
        self.time_window = time_window
        self.min_interactions = min_interactions

        # Cached data
        self._user_profiles: Dict[str, UserProfile] = {}
        self._template_matrix = None
        self._user_similarity = None
        self._template_similarity = None
        self._last_update = None

        # Event weights for scoring
        self.event_weights = {
            EventType.VIEW: 1.0,
            EventType.EDIT: 3.0,
            EventType.EXPORT: 2.0,
            EventType.SHARE: 2.5,
            EventType.FAVORITE: 4.0,
            EventType.COPY: 2.0,
        }

    def _build_user_profiles(self) -> None:
        """Build user interaction profiles."""
        # Get all events in time window
        events = self.analytics.get_events(self.time_window)
        
        # Group events by user
        user_events: Dict[str, List] = {}
        for event in events:
            if event.merchant_id not in user_events:
                user_events[event.merchant_id] = []
            user_events[event.merchant_id].append(event)

        # Build profiles
        self._user_profiles = {}
        for merchant_id, events in user_events.items():
            # Skip users with too few interactions
            if len(events) < self.min_interactions:
                continue

            # Calculate template interaction scores
            template_scores = {}
            for event in events:
                if event.template_id not in template_scores:
                    template_scores[event.template_id] = 0.0
                template_scores[event.template_id] += self.event_weights.get(
                    event.event_type, 1.0
                )

            # Calculate tag preferences
            tag_scores = {}
            for event in events:
                if not event.metadata or "tags" not in event.metadata:
                    continue
                tags = event.metadata["tags"].split(",")
                weight = self.event_weights.get(event.event_type, 1.0)
                for tag in tags:
                    tag = tag.strip()
                    if not tag:
                        continue
                    if tag not in tag_scores:
                        tag_scores[tag] = 0.0
                    tag_scores[tag] += weight

            # Normalize scores
            if template_scores:
                max_template = max(template_scores.values())
                for tid in template_scores:
                    template_scores[tid] /= max_template

            if tag_scores:
                max_tag = max(tag_scores.values())
                for tag in tag_scores:
                    tag_scores[tag] /= max_tag

            # Create profile
            self._user_profiles[merchant_id] = UserProfile(
                merchant_id=merchant_id,
                template_interactions=template_scores,
                tag_preferences=tag_scores,
                last_active=max(e.timestamp for e in events),
            )

    def _build_similarity_matrices(self) -> None:
        """Build user and template similarity matrices."""
        if not self._user_profiles:
            return

        # Get all template IDs
        template_ids = set()
        for profile in self._user_profiles.values():
            template_ids.update(profile.template_interactions.keys())
        template_id_map = {tid: i for i, tid in enumerate(sorted(template_ids))}
        
        # Build interaction matrix (users x templates)
        matrix_shape = (len(self._user_profiles), len(template_ids))
        if matrix_shape[1] == 0:  # No templates
            return

        rows, cols, data = [], [], []
        for uid, profile in enumerate(self._user_profiles.values()):
            for tid, score in profile.template_interactions.items():
                rows.append(uid)
                cols.append(template_id_map[tid])
                data.append(score)

        self._template_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=matrix_shape,
        )

        # Calculate similarities if we have enough data
        if self._template_matrix.shape[1] >= 2:
            # SVD for dimensionality reduction
            n_factors = min(self._template_matrix.shape[1] - 1, 10)
            U, S, Vt = svds(self._template_matrix, k=n_factors)

            # Normalize user and template factors
            user_factors = U * np.sqrt(S)
            template_factors = (np.sqrt(S) * Vt).T

            # Calculate similarities
            self._user_similarity = cosine_similarity(user_factors)
            self._template_similarity = cosine_similarity(template_factors)

    def update(self) -> None:
        """Update recommendation models."""
        self._build_user_profiles()
        self._build_similarity_matrices()
        self._last_update = datetime.utcnow()

    def _needs_update(self) -> bool:
        """Check if models need updating."""
        if not self._last_update:
            return True
        return (datetime.utcnow() - self._last_update) > timedelta(hours=1)

    def _get_similar_users(
        self,
        merchant_id: str,
        limit: int = 10,
    ) -> List[Tuple[str, float]]:
        """Get similar users based on template interactions.

        Args:
            merchant_id: Target merchant ID
            limit: Maximum number of similar users

        Returns:
            List of (merchant_id, similarity) tuples
        """
        if merchant_id not in self._user_profiles:
            return []

        if self._user_similarity is None:
            return []

        # Get user index
        user_ids = list(self._user_profiles.keys())
        user_idx = user_ids.index(merchant_id)

        # Get similarities
        similarities = self._user_similarity[user_idx]
        similar_indices = np.argsort(similarities)[::-1][1:limit + 1]

        return [
            (user_ids[idx], float(similarities[idx]))
            for idx in similar_indices
            if similarities[idx] > 0
        ]

    def _get_similar_templates(
        self,
        template_id: str,
        limit: int = 10,
    ) -> List[Tuple[str, float]]:
        """Get similar templates based on user interactions.

        Args:
            template_id: Target template ID
            limit: Maximum number of similar templates

        Returns:
            List of (template_id, similarity) tuples
        """
        if self._template_similarity is None:
            return []

        # Get template index
        template_ids = []
        for profile in self._user_profiles.values():
            template_ids.extend(profile.template_interactions.keys())
        template_ids = sorted(set(template_ids))

        try:
            template_idx = template_ids.index(template_id)
        except ValueError:
            return []

        # Get similarities
        similarities = self._template_similarity[template_idx]
        similar_indices = np.argsort(similarities)[::-1][1:limit + 1]

        return [
            (template_ids[idx], float(similarities[idx]))
            for idx in similar_indices
            if similarities[idx] > 0
        ]

    def _calculate_tag_match_score(
        self,
        template_tags: Set[str],
        user_preferences: Dict[str, float],
    ) -> float:
        """Calculate tag match score.

        Args:
            template_tags: Template tags
            user_preferences: User tag preferences

        Returns:
            Match score between 0 and 1
        """
        if not template_tags or not user_preferences:
            return 0.0

        # Calculate weighted match
        matches = []
        for tag in template_tags:
            if tag in user_preferences:
                matches.append(user_preferences[tag])

        return np.mean(matches) if matches else 0.0

    def get_recommendations(
        self,
        merchant_id: str,
        current_template_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[TemplateProfile]:
        """Get personalized template recommendations.

        Args:
            merchant_id: Target merchant ID
            current_template_id: Optional current template for context
            limit: Maximum recommendations to return

        Returns:
            List of template recommendations with scores
        """
        if self._needs_update():
            self.update()

        if not self._user_profiles:
            return []

        recommendations = {}

        # Get user profile
        user = self._user_profiles.get(merchant_id)
        if not user:
            return []

        # Get similar users
        similar_users = self._get_similar_users(merchant_id)
        
        # Collaborative filtering recommendations
        for similar_id, similarity in similar_users:
            similar_user = self._user_profiles[similar_id]
            for tid, score in similar_user.template_interactions.items():
                # Skip templates user has already interacted with
                if tid in user.template_interactions:
                    continue
                
                if tid not in recommendations:
                    recommendations[tid] = TemplateProfile(
                        template_id=tid,
                        interaction_score=0.0,
                        similarity_score=0.0,
                        tag_match_score=0.0,
                        final_score=0.0,
                    )
                
                # Weight score by user similarity
                recommendations[tid].interaction_score += score * similarity

        # Content-based recommendations from current template
        if current_template_id:
            similar_templates = self._get_similar_templates(current_template_id)
            for tid, similarity in similar_templates:
                if tid in user.template_interactions:
                    continue
                
                if tid not in recommendations:
                    recommendations[tid] = TemplateProfile(
                        template_id=tid,
                        interaction_score=0.0,
                        similarity_score=similarity,
                        tag_match_score=0.0,
                        final_score=0.0,
                    )
                else:
                    recommendations[tid].similarity_score = similarity

        # Calculate tag match scores
        for tid in recommendations:
            template = self.analytics.get_template(tid)
            if template and template.metadata and "tags" in template.metadata:
                tags = set(
                    t.strip()
                    for t in template.metadata["tags"].split(",")
                    if t.strip()
                )
                recommendations[tid].tag_match_score = (
                    self._calculate_tag_match_score(tags, user.tag_preferences)
                )

        # Calculate final scores
        weights = {
            "interaction": 0.4,  # Collaborative filtering weight
            "similarity": 0.3,   # Content-based similarity weight
            "tags": 0.3,        # Tag preference weight
        }

        for rec in recommendations.values():
            rec.final_score = (
                weights["interaction"] * rec.interaction_score +
                weights["similarity"] * rec.similarity_score +
                weights["tags"] * rec.tag_match_score
            )

        # Sort and return top recommendations
        return sorted(
            recommendations.values(),
            key=lambda x: x.final_score,
            reverse=True,
        )[:limit]
