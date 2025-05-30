"""Template version control system."""
from datetime import datetime
from difflib import unified_diff
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union
import json

from pydantic import BaseModel, Field

from .template_config import TemplateConfig
from .template_presets import TemplatePreset


class ChangeType(str, Enum):
    """Type of template change."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    METADATA = "metadata"  # Tags, description, etc.


class TemplateChange(BaseModel):
    """Record of a template change."""
    id: str
    template_id: str
    author: str
    timestamp: datetime
    change_type: ChangeType
    description: str
    previous_version: Optional[int] = None
    new_version: int
    diff: Optional[str] = None
    metadata_changes: Optional[Dict[str, Tuple[str, str]]] = None  # field -> (old, new)


class TemplateVersion(BaseModel):
    """Specific version of a template."""
    template_id: str
    version: int
    content: Union[TemplateConfig, TemplatePreset]
    created_at: datetime
    author: str
    commit_message: str
    tags: Set[str] = Field(default_factory=set)
    is_public: bool = False


class VersionControl:
    """Template version control system."""

    def __init__(self, supabase_client):
        """Initialize version control.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client

    def _get_template_versions(self, template_id: str) -> List[TemplateVersion]:
        """Get all versions of a template.

        Args:
            template_id: Template ID

        Returns:
            List of template versions

        Raises:
            ValueError: If template not found
        """
        result = self.supabase.table("template_versions").select("*").eq(
            "template_id", template_id
        ).order("version").execute()

        if not result.data:
            raise ValueError(f"Template {template_id} not found")

        return [TemplateVersion(**v) for v in result.data]

    def _generate_diff(
        self,
        old_content: Union[TemplateConfig, TemplatePreset],
        new_content: Union[TemplateConfig, TemplatePreset],
    ) -> str:
        """Generate unified diff between template versions.

        Args:
            old_content: Previous template version
            new_content: New template version

        Returns:
            Unified diff string
        """
        # Convert to JSON for diffing
        old_json = json.dumps(old_content.dict(), indent=2).splitlines()
        new_json = json.dumps(new_content.dict(), indent=2).splitlines()

        # Generate unified diff
        diff = list(unified_diff(
            old_json,
            new_json,
            fromfile="previous",
            tofile="current",
            lineterm="",
        ))

        return "\n".join(diff)

    def _detect_metadata_changes(
        self,
        old_version: TemplateVersion,
        new_version: TemplateVersion,
    ) -> Dict[str, Tuple[str, str]]:
        """Detect changes in template metadata.

        Args:
            old_version: Previous version
            new_version: New version

        Returns:
            Dictionary of changed fields with old and new values
        """
        changes = {}

        # Check tag changes
        if old_version.tags != new_version.tags:
            changes["tags"] = (
                ", ".join(sorted(old_version.tags)),
                ", ".join(sorted(new_version.tags)),
            )

        # Check visibility changes
        if old_version.is_public != new_version.is_public:
            changes["visibility"] = (
                "public" if old_version.is_public else "private",
                "public" if new_version.is_public else "private",
            )

        return changes

    def create_version(
        self,
        template_id: str,
        content: Union[TemplateConfig, TemplatePreset],
        author: str,
        commit_message: str,
        tags: Optional[Set[str]] = None,
        is_public: bool = False,
    ) -> TemplateVersion:
        """Create a new version of a template.

        Args:
            template_id: Template ID
            content: Template content
            author: Version author
            commit_message: Commit message
            tags: Optional template tags
            is_public: Whether template is public

        Returns:
            Created version

        Raises:
            ValueError: If version creation fails
        """
        # Get existing versions
        try:
            versions = self._get_template_versions(template_id)
            new_version = versions[-1].version + 1 if versions else 1
        except ValueError:
            # New template
            new_version = 1
            versions = []

        # Create version record
        version = TemplateVersion(
            template_id=template_id,
            version=new_version,
            content=content,
            created_at=datetime.utcnow(),
            author=author,
            commit_message=commit_message,
            tags=tags or set(),
            is_public=is_public,
        )

        # Save to database
        result = self.supabase.table("template_versions").insert(
            version.dict()
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to create version: {result['error']}")

        # Record change
        if versions:
            # Update to existing template
            change_type = ChangeType.MODIFIED
            diff = self._generate_diff(versions[-1].content, content)
            metadata_changes = self._detect_metadata_changes(versions[-1], version)
        else:
            # New template
            change_type = ChangeType.CREATED
            diff = None
            metadata_changes = None

        change = TemplateChange(
            id=f"{template_id}_{new_version}",
            template_id=template_id,
            author=author,
            timestamp=version.created_at,
            change_type=change_type,
            description=commit_message,
            previous_version=versions[-1].version if versions else None,
            new_version=new_version,
            diff=diff,
            metadata_changes=metadata_changes,
        )

        result = self.supabase.table("template_changes").insert(
            change.dict()
        ).execute()

        if "error" in result:
            raise ValueError(f"Failed to record change: {result['error']}")

        return version

    def get_version(
        self,
        template_id: str,
        version: Optional[int] = None,
    ) -> TemplateVersion:
        """Get a specific version of a template.

        Args:
            template_id: Template ID
            version: Optional version number, latest if None

        Returns:
            Template version

        Raises:
            ValueError: If version not found
        """
        query = self.supabase.table("template_versions").select("*").eq(
            "template_id", template_id
        )

        if version is not None:
            query = query.eq("version", version)
        else:
            query = query.order("version", desc=True).limit(1)

        result = query.execute()
        if not result.data:
            raise ValueError(
                f"Template {template_id} version {version or 'latest'} not found"
            )

        return TemplateVersion(**result.data[0])

    def get_changes(
        self,
        template_id: str,
        limit: Optional[int] = None,
    ) -> List[TemplateChange]:
        """Get change history for a template.

        Args:
            template_id: Template ID
            limit: Optional maximum changes to return

        Returns:
            List of template changes

        Raises:
            ValueError: If template not found
        """
        query = self.supabase.table("template_changes").select("*").eq(
            "template_id", template_id
        ).order("timestamp", desc=True)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        if not result.data:
            raise ValueError(f"No changes found for template {template_id}")

        return [TemplateChange(**c) for c in result.data]

    def compare_versions(
        self,
        template_id: str,
        version1: int,
        version2: int,
    ) -> Tuple[str, Dict[str, Tuple[str, str]]]:
        """Compare two versions of a template.

        Args:
            template_id: Template ID
            version1: First version number
            version2: Second version number

        Returns:
            Tuple of (diff string, metadata changes)

        Raises:
            ValueError: If either version not found
        """
        v1 = self.get_version(template_id, version1)
        v2 = self.get_version(template_id, version2)

        diff = self._generate_diff(v1.content, v2.content)
        metadata_changes = self._detect_metadata_changes(v1, v2)

        return diff, metadata_changes

    def rollback(
        self,
        template_id: str,
        version: int,
        author: str,
        commit_message: Optional[str] = None,
    ) -> TemplateVersion:
        """Roll back to a previous version.

        Args:
            template_id: Template ID
            version: Version to roll back to
            author: Rollback author
            commit_message: Optional commit message

        Returns:
            New version created from rollback

        Raises:
            ValueError: If version not found
        """
        # Get target version
        target = self.get_version(template_id, version)

        # Create new version with rolled back content
        return self.create_version(
            template_id=template_id,
            content=target.content,
            author=author,
            commit_message=commit_message or f"Rolled back to version {version}",
            tags=target.tags,
            is_public=target.is_public,
        )
