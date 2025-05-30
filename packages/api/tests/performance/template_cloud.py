"""Cloud synchronization for templates using Supabase."""
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel
from supabase import Client, create_client

from .template_config import TemplateConfig
from .template_presets import TemplatePreset
from .template_sharing import TemplateShare


class CloudTemplate(BaseModel):
    """Cloud template metadata."""
    id: str
    name: str
    description: str
    author: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    tags: List[str]
    version: int
    share_string: str


class TemplateCloud:
    """Cloud synchronization for templates."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        merchant_id: str,
    ):
        """Initialize cloud sync.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            merchant_id: Current merchant ID
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.merchant_id = merchant_id

    def upload_template(
        self,
        template: Union[TemplateConfig, TemplatePreset],
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        tags: Optional[List[str]] = None,
    ) -> CloudTemplate:
        """Upload a template to the cloud.

        Args:
            template: Template to upload
            name: Optional name override
            description: Optional description
            is_public: Whether template is public
            tags: Optional tags

        Returns:
            Uploaded template metadata

        Raises:
            ValueError: If upload fails
        """
        # Generate share string
        share_string = TemplateShare.export_template(template)

        # Prepare metadata
        template_name = name or (
            template.name if isinstance(template, TemplatePreset)
            else template.name
        )
        template_desc = description or (
            template.description if isinstance(template, TemplatePreset)
            else "Custom template"
        )

        # Upload to Supabase
        data = {
            "name": template_name,
            "description": template_desc,
            "author": self.merchant_id,
            "is_public": is_public,
            "tags": tags or [],
            "version": 1,
            "share_string": share_string,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = self.supabase.table("template_library").insert(data).execute()
        if "error" in result:
            raise ValueError(f"Upload failed: {result['error']}")

        return CloudTemplate(**result.data[0])

    def update_template(
        self,
        template_id: str,
        template: Union[TemplateConfig, TemplatePreset],
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> CloudTemplate:
        """Update a cloud template.

        Args:
            template_id: ID of template to update
            template: New template version
            name: Optional new name
            description: Optional new description
            is_public: Optional new visibility
            tags: Optional new tags

        Returns:
            Updated template metadata

        Raises:
            ValueError: If update fails
        """
        # Get current template
        result = self.supabase.table("template_library").select("*").eq("id", template_id).execute()
        if not result.data:
            raise ValueError(f"Template {template_id} not found")

        current = result.data[0]
        if current["author"] != self.merchant_id:
            raise ValueError("Cannot update template: not the owner")

        # Generate new share string
        share_string = TemplateShare.export_template(template)

        # Prepare update data
        data = {
            "name": name or current["name"],
            "description": description or current["description"],
            "is_public": is_public if is_public is not None else current["is_public"],
            "tags": tags or current["tags"],
            "version": current["version"] + 1,
            "share_string": share_string,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = self.supabase.table("template_library").update(data).eq("id", template_id).execute()
        if "error" in result:
            raise ValueError(f"Update failed: {result['error']}")

        return CloudTemplate(**result.data[0])

    def download_template(
        self,
        template_id: str,
        as_preset: bool = False,
    ) -> Union[TemplateConfig, TemplatePreset]:
        """Download a template from the cloud.

        Args:
            template_id: ID of template to download
            as_preset: Whether to download as preset

        Returns:
            Downloaded template

        Raises:
            ValueError: If download fails or template not found
        """
        # Get template
        result = self.supabase.table("template_library").select("*").eq("id", template_id).execute()
        if not result.data:
            raise ValueError(f"Template {template_id} not found")

        template = result.data[0]
        if not template["is_public"] and template["author"] != self.merchant_id:
            raise ValueError("Cannot download template: not public and not the owner")

        # Import from share string
        return TemplateShare.import_template(template["share_string"], as_preset=as_preset)

    def list_templates(
        self,
        owned_only: bool = False,
        public_only: bool = False,
        tags: Optional[List[str]] = None,
    ) -> List[CloudTemplate]:
        """List available cloud templates.

        Args:
            owned_only: Only show owned templates
            public_only: Only show public templates
            tags: Filter by tags

        Returns:
            List of template metadata
        """
        query = self.supabase.table("template_library").select("*")

        if owned_only:
            query = query.eq("author", self.merchant_id)
        if public_only:
            query = query.eq("is_public", True)
        if tags:
            query = query.contains("tags", tags)

        result = query.execute()
        return [CloudTemplate(**item) for item in result.data]

    def delete_template(self, template_id: str) -> None:
        """Delete a cloud template.

        Args:
            template_id: ID of template to delete

        Raises:
            ValueError: If deletion fails or not authorized
        """
        # Check ownership
        result = self.supabase.table("template_library").select("author").eq("id", template_id).execute()
        if not result.data:
            raise ValueError(f"Template {template_id} not found")

        if result.data[0]["author"] != self.merchant_id:
            raise ValueError("Cannot delete template: not the owner")

        # Delete template
        result = self.supabase.table("template_library").delete().eq("id", template_id).execute()
        if "error" in result:
            raise ValueError(f"Delete failed: {result['error']}")

    def sync_local(
        self,
        library_dir: str,
        download_public: bool = True,
    ) -> Dict[str, str]:
        """Sync templates with local library.

        Args:
            library_dir: Local library directory
            download_public: Whether to download public templates

        Returns:
            Dictionary mapping template IDs to sync status
        """
        from pathlib import Path
        from .template_sharing import TemplateLibrary

        # Initialize libraries
        local_lib = TemplateLibrary(library_dir)
        sync_status = {}

        # List templates
        cloud_templates = self.list_templates(public_only=download_public)
        local_templates = local_lib.list_templates()

        # Download new templates
        for template in cloud_templates:
            local_path = local_templates.get(template.name)
            if not local_path or Path(local_path).stat().st_mtime < template.updated_at.timestamp():
                try:
                    downloaded = self.download_template(template.id)
                    local_lib.save_template(downloaded, template.name)
                    sync_status[template.id] = "downloaded"
                except Exception as e:
                    sync_status[template.id] = f"download_failed: {str(e)}"

        # Upload local templates
        for name, path in local_templates.items():
            try:
                template = local_lib.load_template(name)
                # Check if template exists in cloud
                cloud_match = next(
                    (t for t in cloud_templates if t.name == name),
                    None
                )
                if cloud_match:
                    # Update if local is newer
                    if Path(path).stat().st_mtime > cloud_match.updated_at.timestamp():
                        self.update_template(cloud_match.id, template)
                        sync_status[cloud_match.id] = "updated"
                else:
                    # Upload new template
                    uploaded = self.upload_template(template, name)
                    sync_status[uploaded.id] = "uploaded"
            except Exception as e:
                sync_status[name] = f"upload_failed: {str(e)}"

        return sync_status
