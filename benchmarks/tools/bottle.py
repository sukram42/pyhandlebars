import bottle as bottle_lib

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{invoice_number}}\n"
        "Customer: {{customer_name}}\n"
        "Address: {{billing_address['street']}}, {{billing_address['city']}}, {{billing_address['country']}}\n"
        "Currency: {{currency}}\n"
        "%for item in line_items:\n"
        "- {{item['description']}}: {{item['quantity']}} x {{item['unit_price']}}\n"
        "%end\n"
        "%if notes:\n"
        "Notes: {{notes}}\n"
        "%end\n"
    )
    def prepare() -> bottle_lib.SimpleTemplate:
        return bottle_lib.SimpleTemplate(template_str)
    return BenchCase(prepare=prepare, render=lambda t: t.render(**fixture.data.model_dump()))


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{username}} \u2014 {{display_name}}\n"
        "{{bio}}\n"
        "Location: {{location}} | Followers: {{follower_count}}\n"
        "Contact: {{email}}\n"
        "%for link in links:\n"
        "- {{link['platform']}}: {{link['url']}}\n"
        "%end\n"
        "%if verified:\n"
        "Verified account\n"
        "%end\n"
    )
    def prepare() -> bottle_lib.SimpleTemplate:
        return bottle_lib.SimpleTemplate(template_str)
    return BenchCase(prepare=prepare, render=lambda t: t.render(**fixture.data.model_dump()))


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{environment}} ({{region_info[region]['name']}}, {{region_info[region]['datacenter']}})\n"
        "Version: {{version}} \u2014 commit {{commit_sha}}\n"
        "Deployed by: {{deployed_by}}\n"
        "Services:\n"
        "%for s in services:\n"
        "- {{s['name']}}: {{status_labels[s['status']]}} ({{s['latency_ms']}}ms)\n"
        "%end\n"
        "%if rollback_available:\n"
        "Rollback: available\n"
        "%else:\n"
        "Rollback: NOT available\n"
        "%end\n"
    )
    def prepare() -> bottle_lib.SimpleTemplate:
        return bottle_lib.SimpleTemplate(template_str)
    return BenchCase(prepare=prepare, render=lambda t: t.render(**fixture.data.model_dump()))




def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    template_str = (
        "Release v{{version}} \u2014 {{project}}{{' [HOTFIX]' if hotfix else ''}}\n"
        "Team: {{team['name']}} | Lead: {{team['lead']['name']}} ({{team['lead']['email']}})\n"
        "Components:\n"
        "%for comp in components:\n"
        "- {{comp['name']}} [{{'deployed' if comp['deployed'] else 'not deployed'}}]"
        " tests: {{comp['tests']['passed']}}/{{comp['tests']['total']}} {{comp['tests']['pass_label']}}\n"
        "%for dep in comp['dependencies']:\n"
        "  - {{dep['name']}}@{{dep['version']}} ({{dep['stability']}})\n"
        "%end\n"
        "%end\n"
        "Environments:\n"
        "%for env in environments:\n"
        "- {{env['name']}}: {{env['status']}}{{' on ' + env['deployed_at'] if env['deployed_at'] else ''}}\n"
        "%end\n"
    )
    def prepare():
        return bottle_lib.SimpleTemplate(template_str)
    return BenchCase(prepare=prepare, render=lambda t: t.render(**fixture.data.model_dump()))
