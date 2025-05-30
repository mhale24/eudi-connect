"""Template configuration system."""
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ChartTheme(str, Enum):
    """Available chart themes."""
    DEFAULT = "plotly"
    LIGHT = "plotly_white"
    DARK = "plotly_dark"
    MODERN = "seaborn"
    MINIMAL = "simple_white"


class ColorScheme(str, Enum):
    """Available color schemes."""
    DEFAULT = "default"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    GRAY = "gray"
    CUSTOM = "custom"


class TableStyle(str, Enum):
    """Available table styles."""
    DEFAULT = "default"
    COMPACT = "compact"
    MINIMAL = "minimal"
    BORDERED = "bordered"
    STRIPED = "striped"


class FontConfig(BaseModel):
    """Font configuration."""
    family: str = "system-ui, -apple-system, sans-serif"
    size_base: int = 16
    size_title: int = 32
    size_heading: int = 24
    size_subheading: int = 20
    size_text: int = 16
    weight_normal: int = 400
    weight_medium: int = 500
    weight_bold: int = 700


class ColorConfig(BaseModel):
    """Color configuration."""
    primary: str = "#3B82F6"  # Blue
    secondary: str = "#6B7280"  # Gray
    success: str = "#10B981"  # Green
    warning: str = "#F59E0B"  # Yellow
    error: str = "#EF4444"  # Red
    background: str = "#F9FAFB"
    surface: str = "#FFFFFF"
    text: str = "#111827"
    text_secondary: str = "#6B7280"
    border: str = "#E5E7EB"


class ChartConfig(BaseModel):
    """Chart configuration."""
    theme: ChartTheme = ChartTheme.DEFAULT
    height: int = 400
    show_grid: bool = True
    interactive: bool = True
    color_sequence: Optional[List[str]] = None


class MetricsConfig(BaseModel):
    """Metrics display configuration."""
    show_summary: bool = True
    show_rule_metrics: bool = True
    show_scenario_metrics: bool = True
    show_charts: bool = True
    show_tables: bool = True
    decimal_places: int = 1
    compact_numbers: bool = False


class TemplateConfig(BaseModel):
    """Template configuration."""
    name: str
    description: str
    fonts: FontConfig = Field(default_factory=FontConfig)
    colors: ColorConfig = Field(default_factory=ColorConfig)
    charts: ChartConfig = Field(default_factory=ChartConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    table_style: TableStyle = TableStyle.DEFAULT

    def get_css_variables(self) -> Dict[str, str]:
        """Get CSS variables for the template."""
        return {
            # Fonts
            "--font-family": self.fonts.family,
            "--font-size-base": f"{self.fonts.size_base}px",
            "--font-size-title": f"{self.fonts.size_title}px",
            "--font-size-heading": f"{self.fonts.size_heading}px",
            "--font-size-subheading": f"{self.fonts.size_subheading}px",
            "--font-size-text": f"{self.fonts.size_text}px",
            "--font-weight-normal": str(self.fonts.weight_normal),
            "--font-weight-medium": str(self.fonts.weight_medium),
            "--font-weight-bold": str(self.fonts.weight_bold),

            # Colors
            "--color-primary": self.colors.primary,
            "--color-secondary": self.colors.secondary,
            "--color-success": self.colors.success,
            "--color-warning": self.colors.warning,
            "--color-error": self.colors.error,
            "--color-background": self.colors.background,
            "--color-surface": self.colors.surface,
            "--color-text": self.colors.text,
            "--color-text-secondary": self.colors.text_secondary,
            "--color-border": self.colors.border,
        }

    def get_table_classes(self) -> str:
        """Get CSS classes for tables based on style."""
        classes = ["table"]
        if self.table_style == TableStyle.COMPACT:
            classes.append("table-compact")
        elif self.table_style == TableStyle.MINIMAL:
            classes.append("table-minimal")
        elif self.table_style == TableStyle.BORDERED:
            classes.append("table-bordered")
        elif self.table_style == TableStyle.STRIPED:
            classes.append("table-striped")
        return " ".join(classes)

    def format_number(self, value: Union[int, float]) -> str:
        """Format a number according to configuration."""
        if isinstance(value, int):
            return f"{value:,}" if self.metrics.compact_numbers else str(value)
        return (
            f"{value:,.{self.metrics.decimal_places}f}"
            if self.metrics.compact_numbers
            else f"{value:.{self.metrics.decimal_places}f}"
        )


# Predefined templates
DEFAULT_TEMPLATE = TemplateConfig(
    name="Default",
    description="Clean, modern design with essential metrics",
)

MINIMAL_TEMPLATE = TemplateConfig(
    name="Minimal",
    description="Simple, lightweight report format",
    fonts=FontConfig(
        family="system-ui",
        size_base=14,
        size_title=24,
        size_heading=20,
        size_subheading=16,
        size_text=14,
    ),
    colors=ColorConfig(
        primary="#000000",
        secondary="#666666",
        success="#008000",
        warning="#FFA500",
        error="#FF0000",
        background="#FFFFFF",
        surface="#FFFFFF",
        text="#000000",
        text_secondary="#666666",
        border="#CCCCCC",
    ),
    charts=ChartConfig(
        theme=ChartTheme.MINIMAL,
        height=300,
        show_grid=False,
        interactive=False,
    ),
    metrics=MetricsConfig(
        show_summary=True,
        show_rule_metrics=True,
        show_scenario_metrics=True,
        show_charts=True,
        show_tables=True,
        decimal_places=0,
        compact_numbers=True,
    ),
    table_style=TableStyle.MINIMAL,
)

DETAILED_TEMPLATE = TemplateConfig(
    name="Detailed",
    description="Comprehensive report with extended analytics",
    fonts=FontConfig(
        family="Inter, system-ui, sans-serif",
        size_base=16,
        size_title=36,
        size_heading=28,
        size_subheading=22,
        size_text=16,
    ),
    colors=ColorConfig(
        primary="#2563EB",
        secondary="#64748B",
        success="#059669",
        warning="#D97706",
        error="#DC2626",
        background="#F8FAFC",
        surface="#FFFFFF",
        text="#0F172A",
        text_secondary="#64748B",
        border="#E2E8F0",
    ),
    charts=ChartConfig(
        theme=ChartTheme.MODERN,
        height=500,
        show_grid=True,
        interactive=True,
        color_sequence=[
            "#2563EB", "#059669", "#D97706", "#DC2626",
            "#7C3AED", "#DB2777", "#2563EB",
        ],
    ),
    metrics=MetricsConfig(
        show_summary=True,
        show_rule_metrics=True,
        show_scenario_metrics=True,
        show_charts=True,
        show_tables=True,
        decimal_places=2,
        compact_numbers=False,
    ),
    table_style=TableStyle.BORDERED,
)
