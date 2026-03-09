from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    def render(_: None) -> str:
        d = fixture.data
        items = "".join(f"- {i.description}: {i.quantity} x {i.unit_price}\n" for i in d.line_items)
        notes = f"Notes: {d.notes}\n" if d.notes else ""
        return (
            f"Invoice #{d.invoice_number}\n"
            f"Customer: {d.customer_name}\n"
            f"Address: {d.billing_address.street}, {d.billing_address.city}, {d.billing_address.country}\n"
            f"Currency: {d.currency}\n"
            f"{items}"
            f"{notes}"
        )
    return BenchCase(prepare=lambda: None, render=render)


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    def render(_: None) -> str:
        d = fixture.data
        links = "".join(f"- {l.platform}: {l.url}\n" for l in d.links)
        verified = "Verified account\n" if d.verified else ""
        return (
            f"@{d.username} — {d.display_name}\n"
            f"{d.bio}\n"
            f"Location: {d.location} | Followers: {d.follower_count}\n"
            f"Contact: {d.email}\n"
            f"{links}"
            f"{verified}"
        )
    return BenchCase(prepare=lambda: None, render=render)


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    def render(_: None) -> str:
        d = fixture.data
        region = d.region_info[d.region]
        services = "".join(f"- {s.name}: {d.status_labels[s.status]} ({s.latency_ms}ms)\n" for s in d.services)
        rollback = "Rollback: available" if d.rollback_available else "Rollback: NOT available"
        return (
            f"Deployment Report\n"
            f"Environment: {d.environment} ({region.name}, {region.datacenter})\n"
            f"Version: {d.version} \u2014 commit {d.commit_sha}\n"
            f"Deployed by: {d.deployed_by}\n"
            f"Services:\n"
            f"{services}"
            f"{rollback}\n"
        )
    return BenchCase(prepare=lambda: None, render=render)


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    def render(_):
        d = fixture.data
        hotfix = " [HOTFIX]" if d.hotfix else ""
        components = ""
        for comp in d.components:
            status = "deployed" if comp.deployed else "not deployed"
            components += (
                f"- {comp.name} [{status}]"
                f" tests: {comp.tests.passed}/{comp.tests.total} {comp.tests.pass_label}\n"
            )
            for dep in comp.dependencies:
                components += f"  - {dep.name}@{dep.version} ({dep.stability})\n"
        environments = ""
        for env in d.environments:
            suffix = f" on {env.deployed_at}" if env.deployed_at else ""
            environments += f"- {env.name}: {env.status}{suffix}\n"
        return (
            f"Release v{d.version} \u2014 {d.project}{hotfix}\n"
            f"Team: {d.team.name} | Lead: {d.team.lead.name} ({d.team.lead.email})\n"
            f"Components:\n"
            f"{components}"
            f"Environments:\n"
            f"{environments}"
        )
    return BenchCase(prepare=lambda: None, render=render)
