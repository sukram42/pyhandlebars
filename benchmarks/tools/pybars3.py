from pybars import Compiler

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{invoice_number}}\n"
        "Customer: {{customer_name}}\n"
        "Address: {{billing_address.street}}, {{billing_address.city}}, {{billing_address.country}}\n"
        "Currency: {{currency}}\n"
        "{{#each line_items}}- {{description}}: {{quantity}} x {{unit_price}}\n{{/each}}"
        "{{#if notes}}Notes: {{notes}}{{/if}}\n"
    )
    return BenchCase(
        prepare=lambda: Compiler().compile(template_str),
        render=lambda t: t(fixture.data.model_dump()),
    )


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{username}} — {{display_name}}\n"
        "{{bio}}\n"
        "Location: {{location}} | Followers: {{follower_count}}\n"
        "Contact: {{email}}\n"
        "{{#each links}}- {{platform}}: {{url}}\n{{/each}}"
        "{{#if verified}}Verified account{{/if}}\n"
    )
    return BenchCase(
        prepare=lambda: Compiler().compile(template_str),
        render=lambda t: t(fixture.data.model_dump()),
    )


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{environment}} ({{region}})\n"
        "Version: {{version}} — commit {{commit_sha}}\n"
        "Deployed by: {{deployed_by}}\n"
        "Services:\n"
        "{{#each services}}- {{name}}: {{status}} ({{latency_ms}}ms)\n{{/each}}"
        "{{#if rollback_available}}Rollback: available\n{{else}}Rollback: NOT available\n{{/if}}"
    )
    return BenchCase(
        prepare=lambda: Compiler().compile(template_str),
        render=lambda t: t(fixture.data.model_dump()),
    )






def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    # pybars3 strips \n that immediately precedes {{/each}} when it follows {{/if}}.
    # Workaround: embed \n inside status_full and remove it from the template line.
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
        "- {{name}}: {{status_full}}"
        "{{/each}}"
    )
    def render(t):
        d = fixture.data.model_dump()
        for env in d["environments"]:
            suffix = f" on {env['deployed_at']}" if env["deployed_at"] else ""
            env["status_full"] = env["status"] + suffix + "\n"
        return t(d)
    return BenchCase(
        prepare=lambda: Compiler().compile(template_str),
        render=render,
    )
