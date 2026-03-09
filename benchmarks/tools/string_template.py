from string import Template as StdTemplate

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile

# string.Template has no loop support — lists are pre-rendered in the render function.


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #${invoice_number}\n"
        "Customer: ${customer_name}\n"
        "Address: ${street}, ${city}, ${country}\n"
        "Currency: ${currency}\n"
        "${items_block}"
        "${notes_line}"
    )
    def prepare() -> StdTemplate:
        return StdTemplate(template_str)
    def render(t: StdTemplate) -> str:
        d = fixture.data
        items_block = "".join(f"- {i.description}: {i.quantity} x {i.unit_price}\n" for i in d.line_items)
        return t.substitute(
            invoice_number=d.invoice_number,
            customer_name=d.customer_name,
            street=d.billing_address.street,
            city=d.billing_address.city,
            country=d.billing_address.country,
            currency=d.currency,
            items_block=items_block,
            notes_line=f"Notes: {d.notes}\n" if d.notes else "",
        )
    return BenchCase(prepare=prepare, render=render)


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@${username} \u2014 ${display_name}\n"
        "${bio}\n"
        "Location: ${location} | Followers: ${follower_count}\n"
        "Contact: ${email}\n"
        "${links_block}"
        "${verified_line}"
    )
    def prepare() -> StdTemplate:
        return StdTemplate(template_str)
    def render(t: StdTemplate) -> str:
        d = fixture.data
        links_block = "".join(f"- {l.platform}: {l.url}\n" for l in d.links)
        return t.substitute(
            username=d.username,
            display_name=d.display_name,
            bio=d.bio,
            location=d.location,
            follower_count=d.follower_count,
            email=d.email,
            links_block=links_block,
            verified_line="Verified account\n" if d.verified else "",
        )
    return BenchCase(prepare=prepare, render=render)


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: ${environment} (${region_name}, ${region_datacenter})\n"
        "Version: ${version} \u2014 commit ${commit_sha}\n"
        "Deployed by: ${deployed_by}\n"
        "Services:\n"
        "${services_block}"
        "${rollback_line}"
    )
    def prepare() -> StdTemplate:
        return StdTemplate(template_str)
    def render(t: StdTemplate) -> str:
        d = fixture.data
        region = d.region_info[d.region]
        services_block = "".join(
            f"- {s.name}: {d.status_labels[s.status]} ({s.latency_ms}ms)\n" for s in d.services
        )
        rollback = "Rollback: available" if d.rollback_available else "Rollback: NOT available"
        return t.substitute(
            environment=d.environment,
            region_name=region.name,
            region_datacenter=region.datacenter,
            version=d.version,
            commit_sha=d.commit_sha,
            deployed_by=d.deployed_by,
            services_block=services_block,
            rollback_line=f"{rollback}\n",
        )
    return BenchCase(prepare=prepare, render=render)


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    # string.Template has no loops/conditions — build the dynamic parts manually
    template_str = (
        "Release v${version} \u2014 ${project}${hotfix_tag}\n"
        "Team: ${team_name} | Lead: ${lead_name} (${lead_email})\n"
        "Components:\n"
        "${components_block}"
        "Environments:\n"
        "${environments_block}"
    )
    def prepare():
        return StdTemplate(template_str)
    def render(t):
        d = fixture.data
        components_block = ""
        for comp in d.components:
            status = "deployed" if comp.deployed else "not deployed"
            components_block += (
                f"- {comp.name} [{status}]"
                f" tests: {comp.tests.passed}/{comp.tests.total} {comp.tests.pass_label}\n"
            )
            for dep in comp.dependencies:
                components_block += f"  - {dep.name}@{dep.version} ({dep.stability})\n"
        environments_block = ""
        for env in d.environments:
            suffix = f" on {env.deployed_at}" if env.deployed_at else ""
            environments_block += f"- {env.name}: {env.status}{suffix}\n"
        return t.substitute(
            version=d.version,
            project=d.project,
            hotfix_tag=" [HOTFIX]" if d.hotfix else "",
            team_name=d.team.name,
            lead_name=d.team.lead.name,
            lead_email=d.team.lead.email,
            components_block=components_block,
            environments_block=environments_block,
        )
    return BenchCase(prepare=prepare, render=render)
