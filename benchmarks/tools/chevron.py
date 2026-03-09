import chevron as chevron_lib
from chevron.tokenizer import tokenize as chevron_tokenize

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{invoice_number}}\n"
        "Customer: {{customer_name}}\n"
        "Address: {{billing_address.street}}, {{billing_address.city}}, {{billing_address.country}}\n"
        "Currency: {{currency}}\n"
        "{{#line_items}}- {{description}}: {{quantity}} x {{unit_price}}\n{{/line_items}}"
        "{{#notes}}Notes: {{notes}}\n{{/notes}}"
    )
    def prepare() -> list:
        return list(chevron_tokenize(template_str))
    return BenchCase(prepare=prepare, render=lambda tokens: chevron_lib.render(tokens, fixture.data.model_dump()))


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{username}} \u2014 {{display_name}}\n"
        "{{bio}}\n"
        "Location: {{location}} | Followers: {{follower_count}}\n"
        "Contact: {{email}}\n"
        "{{#links}}- {{platform}}: {{url}}\n{{/links}}"
        "{{#verified}}Verified account\n{{/verified}}"
    )
    def prepare() -> list:
        return list(chevron_tokenize(template_str))
    return BenchCase(prepare=prepare, render=lambda tokens: chevron_lib.render(tokens, fixture.data.model_dump()))


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{environment}} ({{region_name}}, {{region_datacenter}})\n"
        "Version: {{version}} \u2014 commit {{commit_sha}}\n"
        "Deployed by: {{deployed_by}}\n"
        "Services:\n"
        "{{#services}}- {{name}}: {{status_label}} ({{latency_ms}}ms)\n{{/services}}"
        "{{#rollback_available}}Rollback: available\n{{/rollback_available}}"
        "{{^rollback_available}}Rollback: NOT available\n{{/rollback_available}}"
    )
    def prepare() -> list:
        return list(chevron_tokenize(template_str))
    def render(tokens: list) -> str:
        d = fixture.data
        data = d.model_dump()
        region = d.region_info[d.region]
        data["region_name"] = region.name
        data["region_datacenter"] = region.datacenter
        for s_dict, s_obj in zip(data["services"], d.services):
            s_dict["status_label"] = d.status_labels[s_obj.status]
        return chevron_lib.render(tokens, data)
    return BenchCase(prepare=prepare, render=render)


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    # Mustache: {{#section}} = truthy/loop, {{^section}} = inverted
    # dot notation for nested access; inner loop changes context to current item
    template_str = (
        "Release v{{version}} \u2014 {{project}}{{#hotfix}} [HOTFIX]{{/hotfix}}\n"
        "Team: {{team.name}} | Lead: {{team.lead.name}} ({{team.lead.email}})\n"
        "Components:\n"
        "{{#components}}"
        "- {{name}} [{{#deployed}}deployed{{/deployed}}{{^deployed}}not deployed{{/deployed}}]"
        " tests: {{tests.passed}}/{{tests.total}} {{tests.pass_label}}\n"
        "{{#dependencies}}  - {{name}}@{{version}} ({{stability}})\n{{/dependencies}}"
        "{{/components}}"
        "Environments:\n"
        "{{#environments}}"
        "- {{name}}: {{status}}{{#deployed_at}} on {{deployed_at}}{{/deployed_at}}\n"
        "{{/environments}}"
    )
    def prepare():
        return list(chevron_tokenize(template_str))
    return BenchCase(prepare=prepare, render=lambda tokens: chevron_lib.render(tokens, fixture.data.model_dump()))
