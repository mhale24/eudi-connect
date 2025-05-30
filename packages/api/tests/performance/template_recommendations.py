"""Template recommendation engine with collaborative filtering."""
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from pydantic import BaseModel

from .template_config import TemplateConfig
from .template_presets import TemplatePreset
from .template_collaborative import CollaborativeFilter, TemplateProfileorizer
from sklearn.metrics.pairwise import cosine_similarity

from .template_cloud import CloudTemplate
from .template_config import TemplateConfig


class TemplateUsage(BaseModel):
    """Template usage statistics."""
    template_id: str
    user_id: str
    timestamp: datetime
    duration: Optional[int] = None  # seconds used
    exported: bool = False
    favorited: bool = False


class TemplateRecommendation(BaseModel):
    """Template recommendation with explanation."""
    template: CloudTemplate
    score: float
    reason: str
    tags: List[str]
    similar_to: Optional[str] = None


class RecommendationEngine:
    """Smart template recommendation engine with collaborative filtering."""

    def __init__(self, analytics=None):
        """Initialize recommendation engine.
        
        Args:
            analytics: Optional analytics instance for collaborative filtering
        """
        self.collaborative = None
        if analytics:
            self.collaborative = CollaborativeFilter(analytics)
        
        # Template metadata
        self.templates: Dict[str, CloudTemplate] = {}
        self.template_tags: Dict[str, Set[str]] = {}
        
        # Usage tracking
        self.usage_history: Dict[str, List[TemplateUsage]] = {}

    def _calculate_similarity(
        self,
        templates: List[CloudTemplate]
    ) -> Tuple[np.ndarray, List[str]]:
        """Calculate template similarity matrix.

        Args:
            templates: List of templates

        Returns:
            Tuple of similarity matrix and template IDs
        """
        # Prepare text content
        texts = []
        template_ids = []
        for template in templates:
            content = f"{template.name} {template.description} {' '.join(template.tags)}"
            texts.append(content.lower())
            template_ids.append(template.id)

        # Calculate TF-IDF and similarity
        if not texts:
            return np.array([]), []
        
        tfidf_matrix = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),
            min_df=2,
            stop_words='english'
        ).fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)

        return similarity_matrix, template_ids

    def _get_popular_templates(
        self,
        templates: List[CloudTemplate],
        usage_data: List[TemplateUsage],
        days: int = 30,
        limit: int = 5,
    ) -> List[Tuple[CloudTemplate, float]]:
        """Get popular templates based on recent usage.

        Args:
            templates: List of templates
            usage_data: List of usage records
            days: Days to consider
            limit: Maximum templates to return

        Returns:
            List of (template, score) tuples
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_usage = [u for u in usage_data if u.timestamp >= cutoff]

        # Calculate template scores
        scores: Dict[str, float] = {}
        for usage in recent_usage:
            # Base score
            score = 1.0
            
            # Bonus for exports and favorites
            if usage.exported:
                score += 0.5
            if usage.favorited:
                score += 1.0
                
            # Bonus for longer usage duration
            if usage.duration:
                score += min(usage.duration / 3600, 1.0)  # Max 1 point for 1+ hour
                
            # Apply time decay
            days_old = (datetime.utcnow() - usage.timestamp).days
            time_factor = max(0.1, 1.0 - (days_old / days))
            score *= time_factor
            
            scores[usage.template_id] = scores.get(usage.template_id, 0) + score

        # Sort templates by score
        scored_templates = [
            (t, scores.get(t.id, 0))
            for t in templates
            if t.id in scores
        ]
        return sorted(
            scored_templates,
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def _get_similar_templates(
        self,
        template: CloudTemplate,
        templates: List[CloudTemplate],
        limit: int = 3,
        min_similarity: float = 0.3,
    ) -> List[Tuple[CloudTemplate, float]]:
        """Get templates similar to a given template.

        Args:
            template: Reference template
            templates: List of templates to compare
            limit: Maximum templates to return
            min_similarity: Minimum similarity score

        Returns:
            List of (template, similarity) tuples
        """
        # Calculate similarity matrix
        similarity_matrix, template_ids = self._calculate_similarity(templates)
        if not template_ids:
            return []

        # Find reference template index
        try:
            template_idx = template_ids.index(template.id)
        except ValueError:
            return []

        # Get similar templates
        similarities = similarity_matrix[template_idx]
        similar_templates = [
            (templates[i], float(similarities[i]))
            for i in range(len(templates))
            if i != template_idx and similarities[i] >= min_similarity
        ]

        return sorted(
            similar_templates,
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def _get_tag_based_templates(
        self,
        user_tags: Set[str],
        templates: List[CloudTemplate],
        limit: int = 3,
        min_tags: int = 2,
    ) -> List[Tuple[CloudTemplate, float]]:
        """Get templates matching user's preferred tags.

        Args:
            user_tags: Set of user's preferred tags
            templates: List of templates
            limit: Maximum templates to return
            min_tags: Minimum matching tags required

        Returns:
            List of (template, score) tuples
        """
        user_tags = {t.lower() for t in user_tags}
        
        # Score templates by tag matches
        scored_templates = []
        for template in templates:
            template_tags = {t.lower() for t in template.tags}
            matching_tags = user_tags.intersection(template_tags)
            
            if len(matching_tags) >= min_tags:
                score = len(matching_tags) / max(len(user_tags), len(template_tags))
                scored_templates.append((template, score))

        return sorted(
            scored_templates,
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def get_user_recommendations(
        self,
        merchant_id: str,
        current_template: Optional[CloudTemplate] = None,
        limit: int = 5,
    ) -> List[TemplateRecommendation]:
        """Get personalized template recommendations.

        Args:
            merchant_id: Merchant ID requesting recommendations
            current_template: Optional current template for context
            limit: Maximum recommendations to return

        Returns:
            List of recommendations with explanations
        """
        recommendations: List[TemplateRecommendation] = []
        seen_templates: Set[str] = set()

        # Try collaborative filtering first
        if self.collaborative:
            collab_recs = self.collaborative.get_recommendations(
                merchant_id=merchant_id,
                current_template_id=current_template.id if current_template else None,
                limit=limit,
            )
            
            for rec in collab_recs:
                if rec.template_id in self.templates and rec.template_id not in seen_templates:
                    template = self.templates[rec.template_id]
                    
                    # Build reason string
                    reasons = []
                    if rec.interaction_score > 0:
                        reasons.append("similar users liked this template")
                    if rec.similarity_score > 0:
                        reasons.append("similar to your current template")
                    if rec.tag_match_score > 0:
                        reasons.append("matches your preferred tags")
                    
                    recommendations.append(
                        TemplateRecommendation(
                            template=template,
                            score=rec.final_score * 100,  # Scale to 0-100
                            reason=f"Recommended because {' and '.join(reasons)}",
                            tags=list(self.template_tags.get(template.id, set()))
                        )
                    )
                    seen_templates.add(template.id)

        # Fall back to popularity-based if needed
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            
            # Get popular templates
            popular = self._get_popular_templates(
                list(self.templates.values()),
                self.usage_history.get(merchant_id, []),
            )
            
            for template, score in popular:
                if template.id not in seen_templates:
                    recommendations.append(
                        TemplateRecommendation(
                            template=template,
                            score=min(score * 100, 100),
                            reason="Popular template with high user engagement",
                            tags=list(self.template_tags.get(template.id, set()))
                        )
                    )
                    seen_templates.add(template.id)
                    
                    if len(recommendations) >= limit:
                        break

        # Sort by score and return
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations

    def get_trending_tags(
        self,
        usage_data: List[TemplateUsage],
        templates: List[CloudTemplate],
        days: int = 7,
        limit: int = 5,
    ) -> List[Tuple[str, int]]:
        """Get trending tags based on recent template usage.

        Args:
            usage_data: Usage history
            templates: Available templates
            days: Days to consider
            limit: Maximum tags to return

        Returns:
            List of (tag, usage_count) tuples
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_usage = [u for u in usage_data if u.timestamp >= cutoff]

        # Get templates used recently
        template_ids = {u.template_id for u in recent_usage}
        recent_templates = [t for t in templates if t.id in template_ids]

        # Count tag usage
        tag_counts: Counter = Counter()
        for template in recent_templates:
            tag_counts.update(template.tags)

        return tag_counts.most_common(limit)

    def get_user_tags(
        self,
        user_id: str,
        usage_data: List[TemplateUsage],
        templates: List[CloudTemplate],
        min_uses: int = 2,
    ) -> Set[str]:
        """Get user's preferred tags based on usage history.

        Args:
            user_id: User to analyze
            usage_data: Usage history
            templates: Available templates
            min_uses: Minimum template uses to consider a tag preferred

        Returns:
            Set of preferred tags
        """
        # Get user's template usage
        user_usage = [u for u in usage_data if u.user_id == user_id]
        template_counts: Counter = Counter(u.template_id for u in user_usage)

        # Get tags from frequently used templates
        preferred_tags: Set[str] = set()
        for template in templates:
            if template_counts[template.id] >= min_uses:
                preferred_tags.update(template.tags)

        return preferred_tags
