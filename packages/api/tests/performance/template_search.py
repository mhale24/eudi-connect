"""Template search functionality with fuzzy matching and tag filtering."""
from typing import Dict, List, Optional, Set, Tuple

from fuzzywuzzy import fuzz
from pydantic import BaseModel

from .template_cloud import CloudTemplate
from .template_sharing import TemplateLibrary


class SearchResult(BaseModel):
    """Template search result with relevance score."""
    template: CloudTemplate
    score: float
    matched_fields: Set[str]
    matched_tags: Set[str]


class TemplateSearch:
    """Template search engine."""

    @staticmethod
    def search_templates(
        templates: List[CloudTemplate],
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_score: float = 60.0,
    ) -> List[SearchResult]:
        """Search templates using fuzzy matching and tag filtering.

        Args:
            templates: List of templates to search
            query: Optional search query for fuzzy matching
            tags: Optional list of tags to filter by
            min_score: Minimum relevance score (0-100)

        Returns:
            List of search results sorted by relevance
        """
        results: List[SearchResult] = []

        # Convert tags to lowercase for case-insensitive matching
        search_tags = {t.lower() for t in (tags or [])}

        for template in templates:
            # Skip if tags don't match
            if tags:
                template_tags = {t.lower() for t in template.tags}
                if not search_tags.intersection(template_tags):
                    continue

            # Calculate relevance if query provided
            if query:
                # Get best match scores for each field
                field_scores: Dict[str, float] = {
                    "name": fuzz.partial_ratio(query.lower(), template.name.lower()),
                    "description": fuzz.partial_ratio(
                        query.lower(), template.description.lower()
                    ),
                    "author": fuzz.partial_ratio(query.lower(), template.author.lower()),
                }

                # Get matched fields above threshold
                matched_fields = {
                    field
                    for field, score in field_scores.items()
                    if score >= min_score
                }

                # Skip if no fields match well enough
                if not matched_fields:
                    continue

                # Calculate overall score as weighted average
                weights = {"name": 1.0, "description": 0.7, "author": 0.3}
                total_weight = sum(weights[f] for f in matched_fields)
                score = sum(
                    field_scores[f] * weights[f]
                    for f in matched_fields
                ) / total_weight

            else:
                # If no query, score based on tag matches
                if tags:
                    score = 100.0 * len(search_tags.intersection({t.lower() for t in template.tags})) / len(search_tags)
                    matched_fields = set()
                else:
                    # No search criteria, include all with max score
                    score = 100.0
                    matched_fields = {"name", "description", "author"}

            # Add to results if score meets threshold
            if score >= min_score:
                results.append(
                    SearchResult(
                        template=template,
                        score=score,
                        matched_fields=matched_fields,
                        matched_tags={
                            t for t in template.tags
                            if t.lower() in search_tags
                        } if tags else set()
                    )
                )

        # Sort by score descending
        return sorted(results, key=lambda x: x.score, reverse=True)

    @staticmethod
    def extract_popular_tags(templates: List[CloudTemplate], limit: int = 10) -> List[Tuple[str, int]]:
        """Extract most popular tags from templates.

        Args:
            templates: List of templates to analyze
            limit: Maximum number of tags to return

        Returns:
            List of (tag, count) tuples, sorted by count descending
        """
        # Count tag occurrences
        tag_counts: Dict[str, int] = {}
        for template in templates:
            for tag in template.tags:
                tag = tag.lower()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count descending
        sorted_tags = sorted(
            tag_counts.items(),
            key=lambda x: (-x[1], x[0])  # Sort by count desc, then tag name
        )

        return sorted_tags[:limit]

    @staticmethod
    def suggest_tags(
        partial: str,
        templates: List[CloudTemplate],
        limit: int = 5,
        min_score: float = 60.0,
    ) -> List[Tuple[str, int]]:
        """Suggest tags based on partial input.

        Args:
            partial: Partial tag input
            templates: List of templates to get suggestions from
            limit: Maximum number of suggestions
            min_score: Minimum fuzzy match score

        Returns:
            List of (tag, count) tuples matching partial input
        """
        # Get all unique tags with counts
        tag_counts: Dict[str, int] = {}
        for template in templates:
            for tag in template.tags:
                tag = tag.lower()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Find matching tags
        matches: List[Tuple[str, Tuple[int, float]]] = []
        partial = partial.lower()
        for tag, count in tag_counts.items():
            score = fuzz.partial_ratio(partial, tag)
            if score >= min_score:
                matches.append((tag, (count, score)))

        # Sort by score desc, then count desc
        sorted_matches = sorted(
            matches,
            key=lambda x: (-x[1][1], -x[1][0], x[0])
        )

        # Return top matches with counts
        return [(tag, count) for tag, (count, _) in sorted_matches[:limit]]
