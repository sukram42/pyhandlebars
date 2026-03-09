from __future__ import annotations

from benchmarks.fixtures import (
    BenchCase, DeploymentReport, Fixture, Invoice, ReleaseReport, UserProfile,
)
from pyhandlebars import PyHandlebars, Template


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{invoice_number}}\n"
        "Customer: {{customer_name}}\n"
        "Address: {{billing_address.street}}, {{billing_address.city}}, {{billing_address.country}}\n"
        "Currency: {{currency}}\n"
        "{{#each line_items}}- {{description}}: {{quantity}} x {{unit_price}}\n{{/each}}"
        "{{#if notes}}Notes: {{notes}}\n{{/if}}"
    )
    def prepare() -> Template[Invoice]:
        return Template(template_str, client=PyHandlebars())
    return BenchCase(prepare=prepare, render=lambda t: t.format(fixture.data))


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{username}} — {{display_name}}\n"
        "{{bio}}\n"
        "Location: {{location}} | Followers: {{follower_count}}\n"
        "Contact: {{email}}\n"
        "{{#each links}}- {{platform}}: {{url}}\n{{/each}}"
        "{{#if verified}}Verified account\n{{/if}}"
    )
    def prepare() -> Template[UserProfile]:
        return Template(template_str, client=PyHandlebars())
    return BenchCase(prepare=prepare, render=lambda t: t.format(fixture.data))


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{environment}} ({{#with (lookup region_info region)}}{{name}}, {{datacenter}}{{/with}})\n"
        "Version: {{version}} \u2014 commit {{commit_sha}}\n"
        "Deployed by: {{deployed_by}}\n"
        "Services:\n"
        "{{#each services}}- {{name}}: {{lookup ../status_labels status}} ({{latency_ms}}ms)\n{{/each}}"
        "{{#if rollback_available}}Rollback: available\n{{else}}Rollback: NOT available\n{{/if}}"
    )
    def prepare() -> Template[DeploymentReport]:
        return Template(template_str, client=PyHandlebars())
    return BenchCase(prepare=prepare, render=lambda t: t.format(fixture.data))


def bench_release_report(fixture: Fixture[ReleaseReport]) -> BenchCase:
    template_str = (
        "Release v{{version}} — {{project}}{{#if hotfix}} [HOTFIX]{{/if}}\n"
        "Team: {{team.name}} | Lead: {{team.lead.name}} ({{team.lead.email}})\n"
        "Components:\n"
        "{{#each components}}"
        "- {{name}} [{{#if deployed}}deployed{{else}}not deployed{{/if}}]"
        " tests: {{tests.passed}}/{{tests.total}} {{tests.pass_label}}\n"
        "{{#each dependencies}}  - {{name}}@{{version}} ({{stability}})\n{{/each}}"
        "{{/each}}"
        "Environments:\n"
        "{{#each environments}}"
        "- {{name}}: {{status}}{{#if deployed_at}} on {{deployed_at}}{{/if}}\n"
        "{{/each}}"
    )
    def prepare() -> Template[ReleaseReport]:
        return Template(template_str, client=PyHandlebars())
    return BenchCase(prepare=prepare, render=lambda t: t.format(fixture.data))
