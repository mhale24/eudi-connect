"""Template sharing utilities for exporting and importing templates."""
import base64
import json
from pathlib import Path
from typing import Dict, Optional, Union

from pydantic import ValidationError

from .template_config import TemplateConfig
from .template_presets import TemplatePreset


class TemplateShare:
    """Utilities for sharing templates."""

    @staticmethod
    def export_template(
        template: Union[TemplateConfig, TemplatePreset],
        include_preview: bool = True,
    ) -> str:
        """Export a template to a shareable string.

        Args:
            template: Template or preset to export
            include_preview: Whether to include preview image in export

        Returns:
            Base64 encoded JSON string of the template
        """
        if isinstance(template, TemplatePreset):
            template_dict = {
                "name": template.name,
                "description": template.description,
                "config": template.config.dict(),
            }
            if include_preview and template.preview_image:
                template_dict["preview_image"] = template.preview_image
        else:
            template_dict = template.dict()

        # Convert to JSON and encode
        json_str = json.dumps(template_dict)
        return base64.b64encode(json_str.encode()).decode()

    @staticmethod
    def import_template(
        share_string: str,
        as_preset: bool = False,
    ) -> Union[TemplateConfig, TemplatePreset]:
        """Import a template from a share string.

        Args:
            share_string: Base64 encoded template string
            as_preset: Whether to import as a preset

        Returns:
            Imported template or preset

        Raises:
            ValueError: If share string is invalid
            ValidationError: If template data is invalid
        """
        try:
            # Decode and parse JSON
            json_str = base64.b64decode(share_string).decode()
            template_dict = json.loads(json_str)

            if as_preset:
                # Import as preset
                config = TemplateConfig(**template_dict.pop("config", {}))
                return TemplatePreset(config=config, **template_dict)
            else:
                # Import as template config
                return TemplateConfig(**template_dict)

        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Invalid share string")


class TemplateLibrary:
    """Local template library for storing shared templates."""

    def __init__(self, library_dir: Union[str, Path]):
        """Initialize template library.

        Args:
            library_dir: Directory to store templates
        """
        self.library_dir = Path(library_dir)
        self.library_dir.mkdir(parents=True, exist_ok=True)

    def save_template(
        self,
        template: Union[TemplateConfig, TemplatePreset],
        name: Optional[str] = None,
    ) -> Path:
        """Save a template to the library.

        Args:
            template: Template to save
            name: Optional name override

        Returns:
            Path to saved template file
        """
        # Generate filename from template name
        template_name = name or (
            template.name if isinstance(template, TemplatePreset)
            else template.name
        )
        safe_name = "".join(c if c.isalnum() else "_" for c in template_name.lower())
        file_path = self.library_dir / f"{safe_name}.json"

        # Export and save
        share_string = TemplateShare.export_template(template)
        file_path.write_text(share_string)

        return file_path

    def load_template(
        self,
        name: str,
        as_preset: bool = False,
    ) -> Union[TemplateConfig, TemplatePreset]:
        """Load a template from the library.

        Args:
            name: Name of template to load
            as_preset: Whether to load as a preset

        Returns:
            Loaded template or preset

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        file_path = self.library_dir / f"{safe_name}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found")

        share_string = file_path.read_text()
        return TemplateShare.import_template(share_string, as_preset=as_preset)

    def list_templates(self) -> Dict[str, Path]:
        """List all templates in the library.

        Returns:
            Dictionary of template names to file paths
        """
        return {
            path.stem: path
            for path in self.library_dir.glob("*.json")
        }

    def delete_template(self, name: str) -> None:
        """Delete a template from the library.

        Args:
            name: Name of template to delete

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        file_path = self.library_dir / f"{safe_name}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found")

        file_path.unlink()
