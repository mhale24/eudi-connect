"""Predefined template presets for report customization."""
from typing import Dict

from .template_config import (
    ChartTheme,
    ColorConfig,
    FontConfig,
    ChartConfig,
    MetricsConfig,
    TableStyle,
    TemplateConfig,
)


class TemplatePreset:
    """Template preset with predefined configurations."""

    def __init__(
        self,
        name: str,
        description: str,
        config: TemplateConfig,
        preview_image: str = None,
    ):
        self.name = name
        self.description = description
        self.config = config
        self.preview_image = preview_image


# Modern Blue
MODERN_BLUE = TemplatePreset(
    name="Modern Blue",
    description="Clean, modern design with blue accents",
    config=TemplateConfig(
        name="Modern Blue",
        description="Modern design with blue accents",
        fonts=FontConfig(
            family="Inter, system-ui, sans-serif",
            size_base=16,
            size_title=32,
            size_heading=24,
            size_subheading=20,
            size_text=16,
        ),
        colors=ColorConfig(
            primary="#3B82F6",
            secondary="#64748B",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444",
            background="#F9FAFB",
            surface="#FFFFFF",
            text="#111827",
            text_secondary="#6B7280",
            border="#E5E7EB",
        ),
        charts=ChartConfig(
            theme=ChartTheme.MODERN,
            height=400,
            show_grid=True,
            interactive=True,
            color_sequence=[
                "#3B82F6",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
            ],
        ),
        metrics=MetricsConfig(
            decimal_places=1,
            compact_numbers=True,
        ),
        table_style=TableStyle.BORDERED,
    ),
)

# Minimal Dark
MINIMAL_DARK = TemplatePreset(
    name="Minimal Dark",
    description="Sleek dark theme with minimalist design",
    config=TemplateConfig(
        name="Minimal Dark",
        description="Sleek dark theme with minimalist design",
        fonts=FontConfig(
            family="system-ui, -apple-system, sans-serif",
            size_base=14,
            size_title=28,
            size_heading=22,
            size_subheading=18,
            size_text=14,
        ),
        colors=ColorConfig(
            primary="#60A5FA",
            secondary="#9CA3AF",
            success="#34D399",
            warning="#FBBF24",
            error="#F87171",
            background="#111827",
            surface="#1F2937",
            text="#F9FAFB",
            text_secondary="#D1D5DB",
            border="#374151",
        ),
        charts=ChartConfig(
            theme=ChartTheme.DARK,
            height=350,
            show_grid=False,
            interactive=True,
            color_sequence=[
                "#60A5FA",
                "#34D399",
                "#FBBF24",
                "#F87171",
                "#A78BFA",
            ],
        ),
        metrics=MetricsConfig(
            decimal_places=0,
            compact_numbers=True,
        ),
        table_style=TableStyle.MINIMAL,
    ),
)

# Corporate Classic
CORPORATE_CLASSIC = TemplatePreset(
    name="Corporate Classic",
    description="Professional design for business reports",
    config=TemplateConfig(
        name="Corporate Classic",
        description="Professional design for business reports",
        fonts=FontConfig(
            family="Georgia, serif",
            size_base=16,
            size_title=36,
            size_heading=28,
            size_subheading=22,
            size_text=16,
        ),
        colors=ColorConfig(
            primary="#1E3A8A",
            secondary="#475569",
            success="#065F46",
            warning="#B45309",
            error="#B91C1C",
            background="#FFFFFF",
            surface="#F8FAFC",
            text="#0F172A",
            text_secondary="#475569",
            border="#CBD5E1",
        ),
        charts=ChartConfig(
            theme=ChartTheme.DEFAULT,
            height=450,
            show_grid=True,
            interactive=True,
            color_sequence=[
                "#1E3A8A",
                "#065F46",
                "#B45309",
                "#B91C1C",
                "#4F46E5",
            ],
        ),
        metrics=MetricsConfig(
            decimal_places=2,
            compact_numbers=False,
        ),
        table_style=TableStyle.STRIPED,
    ),
)

# Tech Vibrant
TECH_VIBRANT = TemplatePreset(
    name="Tech Vibrant",
    description="Modern tech-inspired design with vibrant colors",
    config=TemplateConfig(
        name="Tech Vibrant",
        description="Modern tech-inspired design with vibrant colors",
        fonts=FontConfig(
            family="'SF Pro Display', system-ui, sans-serif",
            size_base=16,
            size_title=40,
            size_heading=32,
            size_subheading=24,
            size_text=16,
        ),
        colors=ColorConfig(
            primary="#7C3AED",
            secondary="#6B7280",
            success="#059669",
            warning="#D97706",
            error="#DC2626",
            background="#F3F4F6",
            surface="#FFFFFF",
            text="#111827",
            text_secondary="#4B5563",
            border="#E5E7EB",
        ),
        charts=ChartConfig(
            theme=ChartTheme.LIGHT,
            height=500,
            show_grid=True,
            interactive=True,
            color_sequence=[
                "#7C3AED",
                "#059669",
                "#D97706",
                "#DC2626",
                "#2563EB",
            ],
        ),
        metrics=MetricsConfig(
            decimal_places=1,
            compact_numbers=True,
        ),
        table_style=TableStyle.DEFAULT,
    ),
)

# Accessible High Contrast
ACCESSIBLE_HIGH_CONTRAST = TemplatePreset(
    name="Accessible High Contrast",
    description="High contrast design optimized for accessibility",
    config=TemplateConfig(
        name="Accessible High Contrast",
        description="High contrast design optimized for accessibility",
        fonts=FontConfig(
            family="'Arial', sans-serif",
            size_base=18,
            size_title=36,
            size_heading=30,
            size_subheading=24,
            size_text=18,
        ),
        colors=ColorConfig(
            primary="#0000EE",
            secondary="#595959",
            success="#006400",
            warning="#B45309",
            error="#CC0000",
            background="#FFFFFF",
            surface="#FFFFFF",
            text="#000000",
            text_secondary="#595959",
            border="#000000",
        ),
        charts=ChartConfig(
            theme=ChartTheme.LIGHT,
            height=400,
            show_grid=True,
            interactive=True,
            color_sequence=[
                "#0000EE",
                "#006400",
                "#B45309",
                "#CC0000",
                "#551A8B",
            ],
        ),
        metrics=MetricsConfig(
            decimal_places=1,
            compact_numbers=False,
        ),
        table_style=TableStyle.BORDERED,
    ),
)

# Collection of all presets
TEMPLATE_PRESETS: Dict[str, TemplatePreset] = {
    "modern_blue": MODERN_BLUE,
    "minimal_dark": MINIMAL_DARK,
    "corporate_classic": CORPORATE_CLASSIC,
    "tech_vibrant": TECH_VIBRANT,
    "accessible_high_contrast": ACCESSIBLE_HIGH_CONTRAST,
}
