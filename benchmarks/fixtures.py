from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float


class Address(BaseModel):
    street: str
    city: str
    country: str


class Invoice(BaseModel):
    invoice_number: str
    customer_name: str
    billing_address: Address
    line_items: list[LineItem]
    currency: str
    notes: Optional[str] = None


class SocialLink(BaseModel):
    platform: str
    url: str


class UserProfile(BaseModel):
    username: str
    display_name: str
    bio: str
    location: str
    email: str
    verified: bool
    follower_count: int
    links: list[SocialLink]


class ServiceHealth(BaseModel):
    name: str
    status: str
    latency_ms: float


class RegionInfo(BaseModel):
    name: str
    datacenter: str


class DeploymentReport(BaseModel):
    environment: str
    version: str
    deployed_by: str
    commit_sha: str
    region: str
    services: list[ServiceHealth]
    rollback_available: bool
    region_info: dict[str, RegionInfo]
    status_labels: dict[str, str]

class Dependency(BaseModel):
    name: str
    version: str
    stability: str


class TestSuite(BaseModel):
    passed: int
    total: int
    all_passing: bool
    pass_label: str


class Component(BaseModel):
    name: str
    deployed: bool
    tests: TestSuite
    dependencies: list[Dependency]


class TeamLead(BaseModel):
    name: str
    email: str

class Team(BaseModel):
    name: str
    lead: TeamLead
class EnvDeployment(BaseModel):
    name: str
    status: str
    deployed_at: Optional[str] = None  # falsy when None → conditional in all engines

class ReleaseReport(BaseModel):
    project: str
    version: str
    hotfix: bool
    team: Team
    components: list[Component]
    environments: list[EnvDeployment]


@dataclass
class Fixture[T: BaseModel]:
    label: str
    data: T
    expected: str


@dataclass
class BenchCase:
    """Splits a benchmark into a preparation phase and a render phase.

    - prepare() → state   (e.g. compile a template)
    - render(state) → str (e.g. fill the template with data)
    """
    prepare: Callable[[], Any]
    render: Callable[[Any], str]


invoice = Fixture(
    label="invoice",
    data=Invoice(
        invoice_number="INV-2024-001",
        customer_name="Acme Corp",
        billing_address=Address(street="123 Main St", city="Berlin", country="Germany"),
        line_items=[
            LineItem(description="Widget A", quantity=10, unit_price=9.99),
            LineItem(description="Widget B", quantity=5, unit_price=19.99),
        ],
        currency="EUR",
        notes="Net 30",
    ),
    expected=(
        "Invoice #INV-2024-001\n"
        "Customer: Acme Corp\n"
        "Address: 123 Main St, Berlin, Germany\n"
        "Currency: EUR\n"
        "- Widget A: 10 x 9.99\n"
        "- Widget B: 5 x 19.99\n"
        "Notes: Net 30\n"
    ),
)

profile = Fixture(
    label="user profile",
    data=UserProfile(
        username="rustacean",
        display_name="Ferris the Crab",
        bio="Systems programmer. Memory safety enthusiast.",
        location="Internet",
        email="ferris@rust-lang.org",
        verified=True,
        follower_count=42_000,
        links=[
            SocialLink(platform="GitHub", url="https://github.com/rust-lang"),
            SocialLink(platform="Twitter", url="https://twitter.com/rustlang"),
        ],
    ),
    expected=(
        "@rustacean — Ferris the Crab\n"
        "Systems programmer. Memory safety enthusiast.\n"
        "Location: Internet | Followers: 42000\n"
        "Contact: ferris@rust-lang.org\n"
        "- GitHub: https://github.com/rust-lang\n"
        "- Twitter: https://twitter.com/rustlang\n"
        "Verified account\n"
    ),
)

report = Fixture(
    label="deployment report",
    data=DeploymentReport(
        environment="production",
        version="v3.14.1",
        deployed_by="ci-bot",
        commit_sha="a1b2c3d",
        region="eu-west-1",
        services=[
            ServiceHealth(name="api", status="healthy", latency_ms=12.4),
            ServiceHealth(name="worker", status="healthy", latency_ms=8.1),
            ServiceHealth(name="db", status="degraded", latency_ms=210.0),
        ],
        rollback_available=True,
        region_info={
            "eu-west-1": RegionInfo(name="EU West", datacenter="Dublin"),
            "us-east-1": RegionInfo(name="US East", datacenter="Virginia"),
        },
        status_labels={
            "healthy": "OK",
            "degraded": "WARN",
            "down": "ERR",
        },
    ),
    expected=(
        "Deployment Report\n"
        "Environment: production (EU West, Dublin)\n"
        "Version: v3.14.1 — commit a1b2c3d\n"
        "Deployed by: ci-bot\n"
        "Services:\n"
        "- api: OK (12.4ms)\n"
        "- worker: OK (8.1ms)\n"
        "- db: WARN (210.0ms)\n"
        "Rollback: available\n"
    ),
)

release = Fixture(
    label="release report",
    data=ReleaseReport(
        project="MyApp",
        version="2.0.0",
        hotfix=True,
        team=Team(
            name="Backend",
            lead=TeamLead(name="Alice Smith", email="alice@company.com"),
        ),
        components=[
            Component(
                name="api-gateway",
                deployed=True,
                tests=TestSuite(passed=42, total=42, all_passing=True, pass_label="PASS"),
                dependencies=[
                    Dependency(name="express", version="4.18.2", stability="stable"),
                    Dependency(name="typescript", version="5.0.0", stability="stable"),
                ],
            ),
            Component(
                name="auth-service",
                deployed=True,
                tests=TestSuite(passed=38, total=40, all_passing=False, pass_label="FAIL"),
                dependencies=[
                    Dependency(name="passport", version="0.6.0", stability="stable"),
                    Dependency(name="jsonwebtoken", version="9.0.0", stability="stable"),
                ],
            ),
        ],
        environments=[
            EnvDeployment(name="staging", status="deployed", deployed_at="2024-01-15"),
            EnvDeployment(name="production", status="pending"),
        ],
    ),
    expected=(
        "Release v2.0.0 — MyApp [HOTFIX]\n"
        "Team: Backend | Lead: Alice Smith (alice@company.com)\n"
        "Components:\n"
        "- api-gateway [deployed] tests: 42/42 PASS\n"
        "  - express@4.18.2 (stable)\n"
        "  - typescript@5.0.0 (stable)\n"
        "- auth-service [deployed] tests: 38/40 FAIL\n"
        "  - passport@0.6.0 (stable)\n"
        "  - jsonwebtoken@9.0.0 (stable)\n"
        "Environments:\n"
        "- staging: deployed on 2024-01-15\n"
        "- production: pending\n"
    ),
)
