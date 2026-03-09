from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension
from wheezy.template.loader import DictLoader

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile

# wheezy passes __dict__ so nested Pydantic model objects retain attribute access.


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "@require(invoice_number, customer_name, billing_address, currency, line_items, notes)\n"
        "Invoice #@invoice_number\n"
        "Customer: @customer_name\n"
        "Address: @billing_address.street, @billing_address.city, @billing_address.country\n"
        "Currency: @currency\n"
        "@for item in line_items:\n"
        "- @item.description: @str(item.quantity) x @str(item.unit_price)\n"
        "@end\n"
        "@if notes:\n"
        "Notes: @notes\n"
        "@end\n"
    )
    def prepare() -> Engine:
        return Engine(loader=DictLoader({"t": template_str}), extensions=[CoreExtension()])
    return BenchCase(prepare=prepare, render=lambda e: e.get_template("t").render(fixture.data.__dict__))


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    # @@ is a literal @; pre-compute handle = "@username" and pass it in context
    template_str = (
        "@require(handle, display_name, bio, location, follower_count, email, links, verified)\n"
        "@handle \u2014 @display_name\n"
        "@bio\n"
        "Location: @location | Followers: @str(follower_count)\n"
        "Contact: @email\n"
        "@for link in links:\n"
        "- @link.platform: @link.url\n"
        "@end\n"
        "@if verified:\n"
        "Verified account\n"
        "@end\n"
    )
    def prepare() -> Engine:
        return Engine(loader=DictLoader({"t": template_str}), extensions=[CoreExtension()])
    def render(e: Engine) -> str:
        ctx = {**fixture.data.__dict__, "handle": "@" + fixture.data.username}
        return e.get_template("t").render(ctx)
    return BenchCase(prepare=prepare, render=render)


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "@require(environment, region, region_info, status_labels, version, commit_sha, deployed_by, services, rollback_available)\n"
        "Deployment Report\n"
        "Environment: @environment (@region_info[region].name, @region_info[region].datacenter)\n"
        "Version: @version \u2014 commit @commit_sha\n"
        "Deployed by: @deployed_by\n"
        "Services:\n"
        "@for s in services:\n"
        "- @s.name: @status_labels[s.status] (@str(s.latency_ms)ms)\n"
        "@end\n"
        "@if rollback_available:\n"
        "Rollback: available\n"
        "@else:\n"
        "Rollback: NOT available\n"
        "@end\n"
    )
    def prepare() -> Engine:
        return Engine(loader=DictLoader({"t": template_str}), extensions=[CoreExtension()])
    return BenchCase(prepare=prepare, render=lambda e: e.get_template("t").render(fixture.data.__dict__))






def bench_release_report(fixture):
    import types
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    # wheezy can't output literal @ followed immediately by a variable.
    # Precompute dep lines and env status strings in render().
    template_str = (
        "@require(version, project, hotfix_tag, team, augmented_components, augmented_environments)\n"
        "Release v@version \u2014 @project@hotfix_tag\n"
        "Team: @team.name | Lead: @team.lead.name (@team.lead.email)\n"
        "Components:\n"
        "@for comp in augmented_components:\n"
        "- @comp.name [@comp.deploy_status] tests: @str(comp.tests.passed)/@str(comp.tests.total) @comp.tests.pass_label\n"
        "@comp.dep_block"
        "@end\n"
        "Environments:\n"
        "@for env in augmented_environments:\n"
        "- @env.name: @env.status_full\n"
        "@end\n"
    )
    def prepare():
        return Engine(loader=DictLoader({"t": template_str}), extensions=[CoreExtension()])
    def render(e):
        d = fixture.data
        augmented_components = []
        for comp in d.components:
            ns = types.SimpleNamespace(**comp.__dict__)
            ns.deploy_status = "deployed" if comp.deployed else "not deployed"
            ns.dep_block = "".join(
                f"  - {dep.name}@{dep.version} ({dep.stability})\n"
                for dep in comp.dependencies
            )
            augmented_components.append(ns)
        augmented_environments = []
        for env in d.environments:
            ns = types.SimpleNamespace(**env.__dict__)
            ns.status_full = env.status + (f" on {env.deployed_at}" if env.deployed_at else "")
            augmented_environments.append(ns)
        ctx = {
            **d.__dict__,
            "hotfix_tag": " [HOTFIX]" if d.hotfix else "",
            "augmented_components": augmented_components,
            "augmented_environments": augmented_environments,
        }
        return e.get_template("t").render(ctx)
    return BenchCase(prepare=prepare, render=render)
