import types
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    from Cheetah.Template import Template as CheetahTemplate

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def _ns(obj):
    """Recursively convert dicts/lists to SimpleNamespace so Cheetah's
    NameMapper can resolve attributes in loops."""
    if isinstance(obj, list):
        return [_ns(item) for item in obj]
    if isinstance(obj, dict):
        return types.SimpleNamespace(**{k: _ns(v) for k, v in obj.items()})
    return obj


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #${invoice_number}\n"
        "Customer: ${customer_name}\n"
        "Address: ${billing_address.street}, ${billing_address.city}, ${billing_address.country}\n"
        "Currency: ${currency}\n"
        "#for item in $line_items\n"
        "- ${item.description}: ${item.quantity} x ${item.unit_price}\n"
        "#end for\n"
        "#if $notes\n"
        "Notes: ${notes}\n"
        "#end if\n"
    )
    def prepare():
        return CheetahTemplate.compile(template_str)
    def render(cls) -> str:
        return str(cls(searchList=[_ns(fixture.data.model_dump())]))
    return BenchCase(prepare=prepare, render=render)


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@${username} \u2014 ${display_name}\n"
        "${bio}\n"
        "Location: ${location} | Followers: ${follower_count}\n"
        "Contact: ${email}\n"
        "#for link in $links\n"
        "- ${link.platform}: ${link.url}\n"
        "#end for\n"
        "#if $verified\n"
        "Verified account\n"
        "#end if\n"
    )
    def prepare():
        return CheetahTemplate.compile(template_str)
    def render(cls) -> str:
        return str(cls(searchList=[_ns(fixture.data.model_dump())]))
    return BenchCase(prepare=prepare, render=render)


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    # Cheetah's NameMapper only resolves the outermost name in ${expr}, so
    # dict[variable] subscript with a Cheetah variable doesn't work. Pre-resolve lookups.
    template_str = (
        "Deployment Report\n"
        "Environment: ${environment} (${region_name}, ${region_datacenter})\n"
        "Version: ${version} \u2014 commit ${commit_sha}\n"
        "Deployed by: ${deployed_by}\n"
        "Services:\n"
        "#for s in $services\n"
        "- ${s.name}: ${s.status_label} (${s.latency_ms}ms)\n"
        "#end for\n"
        "#if $rollback_available\n"
        "Rollback: available\n"
        "#else\n"
        "Rollback: NOT available\n"
        "#end if\n"
    )
    def prepare():
        return CheetahTemplate.compile(template_str)
    def render(cls) -> str:
        d = fixture.data
        ns = _ns(d.model_dump())
        region = d.region_info[d.region]
        ns.region_name = region.name
        ns.region_datacenter = region.datacenter
        for s_ns, s_obj in zip(ns.services, d.services):
            s_ns.status_label = d.status_labels[s_obj.status]
        return str(cls(searchList=[ns]))
    return BenchCase(prepare=prepare, render=render)








def bench_release_report(fixture):
    import types
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    # Cheetah evaluates ${expr} as Python code; variables from searchList are NOT
    # in scope for inline expressions. Precompute all conditional strings instead.
    template_str = (
        "Release v${version} \u2014 ${project}${hotfix_tag}\n"
        "Team: ${team.name} | Lead: ${team.lead.name} (${team.lead.email})\n"
        "Components:\n"
        "#for comp in $augmented_components\n"
        "- ${comp.name} [${comp.deploy_status}]"
        " tests: ${comp.tests.passed}/${comp.tests.total} ${comp.tests.pass_label}\n"
        "#for dep in comp.dependencies\n"
        "  - ${dep.name}@${dep.version} (${dep.stability})\n"
        "#end for\n"
        "#end for\n"
        "Environments:\n"
        "#for env in $augmented_environments\n"
        "- ${env.name}: ${env.status_full}\n"
        "#end for\n"
    )
    def prepare():
        return CheetahTemplate.compile(template_str)
    def render(cls):
        d = fixture.data
        ns = _ns(d.model_dump())
        ns.hotfix_tag = " [HOTFIX]" if d.hotfix else ""
        augmented_components = []
        for comp in d.components:
            cns = _ns(comp.model_dump())
            cns.deploy_status = "deployed" if comp.deployed else "not deployed"
            augmented_components.append(cns)
        augmented_environments = []
        for env in d.environments:
            ens = _ns(env.model_dump())
            ens.status_full = env.status + (f" on {env.deployed_at}" if env.deployed_at else "")
            augmented_environments.append(ens)
        ns.augmented_components = augmented_components
        ns.augmented_environments = augmented_environments
        return str(cls(searchList=[ns]))
    return BenchCase(prepare=prepare, render=render)
