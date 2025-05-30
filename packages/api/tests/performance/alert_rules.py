"""Alert rules management system."""
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

# Constants
DEFAULT_RULES_FILE = Path("config/alert_rules.json")
DEFAULT_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)


class MetricCategory(str, Enum):
    """Categories of metrics that can be monitored."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE = "resource"
    CUSTOM = "custom"


class ComparisonOperator(str, Enum):
    """Comparison operators for alert conditions."""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"
    NOT_EQUAL_TO = "not_equal_to"


class AlertAction(str, Enum):
    """Actions to take when alert is triggered."""
    NOTIFY = "notify"
    SCALE = "scale"
    RESTART = "restart"
    CUSTOM = "custom"


class AlertRule(BaseModel):
    """Alert rule configuration."""
    id: str = Field(default_factory=lambda: f"rule_{datetime.utcnow().timestamp()}")
    name: str
    description: str
    metric: str
    category: MetricCategory
    operator: ComparisonOperator
    warning_threshold: float
    critical_threshold: float
    duration: int = 1  # Number of consecutive violations
    cooldown: int = 300  # Seconds between alerts
    enabled: bool = True
    actions: List[AlertAction] = [AlertAction.NOTIFY]
    custom_action: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("critical_threshold")
    def validate_thresholds(cls, v, values):
        """Validate that critical threshold is more severe than warning."""
        warning = values.get("warning_threshold")
        if warning is not None:
            if values.get("operator") == ComparisonOperator.GREATER_THAN:
                assert v > warning, "Critical threshold must be greater than warning threshold"
            elif values.get("operator") == ComparisonOperator.LESS_THAN:
                assert v < warning, "Critical threshold must be less than warning threshold"
        return v

    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class RuleTemplate(BaseModel):
    """Template for creating alert rules."""
    name: str
    description: str
    category: MetricCategory
    suggested_warning: float
    suggested_critical: float
    suggested_operator: ComparisonOperator
    suggested_duration: int
    suggested_cooldown: int


class RuleManager:
    """Manages alert rules configuration."""

    def __init__(self, rules_file: Path = DEFAULT_RULES_FILE):
        """Initialize rule manager."""
        self.rules_file = rules_file
        self.rules: Dict[str, AlertRule] = {}
        self._load_rules()
        self._init_templates()

    def _load_rules(self):
        """Load rules from file."""
        if self.rules_file.exists():
            try:
                with open(self.rules_file) as f:
                    data = json.load(f)
                    self.rules = {
                        k: AlertRule(**v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"Error loading rules: {e}")
                self._create_default_rules()
        else:
            self._create_default_rules()

    def _save_rules(self):
        """Save rules to file."""
        try:
            with open(self.rules_file, "w") as f:
                json.dump(
                    {k: v.dict() for k, v in self.rules.items()},
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            print(f"Error saving rules: {e}")

    def _create_default_rules(self):
        """Create default alert rules."""
        default_rules = [
            AlertRule(
                name="High P95 Latency",
                description="Alert when P95 latency exceeds thresholds",
                metric="p95_latency",
                category=MetricCategory.LATENCY,
                operator=ComparisonOperator.GREATER_THAN,
                warning_threshold=700,
                critical_threshold=800,
                duration=2,
                cooldown=300,
            ),
            AlertRule(
                name="Low Throughput",
                description="Alert when throughput drops below thresholds",
                metric="throughput",
                category=MetricCategory.THROUGHPUT,
                operator=ComparisonOperator.LESS_THAN,
                warning_threshold=10,
                critical_threshold=5,
                duration=2,
                cooldown=300,
            ),
            AlertRule(
                name="High Error Rate",
                description="Alert when error rate exceeds thresholds",
                metric="error_rate",
                category=MetricCategory.ERROR_RATE,
                operator=ComparisonOperator.GREATER_THAN,
                warning_threshold=0.01,
                critical_threshold=0.05,
                duration=1,
                cooldown=300,
            ),
            AlertRule(
                name="High CPU Usage",
                description="Alert when CPU usage exceeds thresholds",
                metric="cpu_usage",
                category=MetricCategory.RESOURCE,
                operator=ComparisonOperator.GREATER_THAN,
                warning_threshold=70,
                critical_threshold=85,
                duration=3,
                cooldown=300,
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule
        self._save_rules()

    def _init_templates(self):
        """Initialize rule templates."""
        self.templates = {
            MetricCategory.LATENCY: [
                RuleTemplate(
                    name="API Endpoint Latency",
                    description="Monitor endpoint response time",
                    category=MetricCategory.LATENCY,
                    suggested_warning=500,
                    suggested_critical=1000,
                    suggested_operator=ComparisonOperator.GREATER_THAN,
                    suggested_duration=2,
                    suggested_cooldown=300,
                ),
                RuleTemplate(
                    name="Database Query Latency",
                    description="Monitor database query performance",
                    category=MetricCategory.LATENCY,
                    suggested_warning=100,
                    suggested_critical=200,
                    suggested_operator=ComparisonOperator.GREATER_THAN,
                    suggested_duration=2,
                    suggested_cooldown=300,
                ),
            ],
            MetricCategory.THROUGHPUT: [
                RuleTemplate(
                    name="API Throughput",
                    description="Monitor requests per second",
                    category=MetricCategory.THROUGHPUT,
                    suggested_warning=10,
                    suggested_critical=5,
                    suggested_operator=ComparisonOperator.LESS_THAN,
                    suggested_duration=2,
                    suggested_cooldown=300,
                ),
            ],
            MetricCategory.ERROR_RATE: [
                RuleTemplate(
                    name="Error Rate",
                    description="Monitor error percentage",
                    category=MetricCategory.ERROR_RATE,
                    suggested_warning=1,
                    suggested_critical=5,
                    suggested_operator=ComparisonOperator.GREATER_THAN,
                    suggested_duration=1,
                    suggested_cooldown=300,
                ),
            ],
            MetricCategory.RESOURCE: [
                RuleTemplate(
                    name="CPU Usage",
                    description="Monitor CPU utilization",
                    category=MetricCategory.RESOURCE,
                    suggested_warning=70,
                    suggested_critical=85,
                    suggested_operator=ComparisonOperator.GREATER_THAN,
                    suggested_duration=3,
                    suggested_cooldown=300,
                ),
                RuleTemplate(
                    name="Memory Usage",
                    description="Monitor memory utilization",
                    category=MetricCategory.RESOURCE,
                    suggested_warning=512,
                    suggested_critical=768,
                    suggested_operator=ComparisonOperator.GREATER_THAN,
                    suggested_duration=3,
                    suggested_cooldown=300,
                ),
            ],
        }

    def get_rules(self, category: Optional[MetricCategory] = None) -> List[AlertRule]:
        """Get all rules, optionally filtered by category."""
        if category:
            return [r for r in self.rules.values() if r.category == category]
        return list(self.rules.values())

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific rule by ID."""
        return self.rules.get(rule_id)

    def add_rule(self, rule: AlertRule) -> str:
        """Add a new alert rule."""
        self.rules[rule.id] = rule
        self._save_rules()
        return rule.id

    def update_rule(self, rule_id: str, updates: Dict) -> Optional[AlertRule]:
        """Update an existing rule."""
        if rule_id not in self.rules:
            return None

        rule = self.rules[rule_id]
        updated_data = rule.dict()
        updated_data.update(updates)
        updated_data["updated_at"] = datetime.utcnow()

        updated_rule = AlertRule(**updated_data)
        self.rules[rule_id] = updated_rule
        self._save_rules()
        return updated_rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_rules()
            return True
        return False

    def get_templates(self, category: Optional[MetricCategory] = None) -> List[RuleTemplate]:
        """Get rule templates, optionally filtered by category."""
        if category:
            return self.templates.get(category, [])
        return [t for templates in self.templates.values() for t in templates]

    def create_rule_from_template(
        self,
        template: RuleTemplate,
        metric: str,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
    ) -> AlertRule:
        """Create a new rule from a template."""
        return AlertRule(
            name=template.name,
            description=template.description,
            metric=metric,
            category=template.category,
            operator=template.suggested_operator,
            warning_threshold=warning_threshold or template.suggested_warning,
            critical_threshold=critical_threshold or template.suggested_critical,
            duration=template.suggested_duration,
            cooldown=template.suggested_cooldown,
        )
