from jinja2 import Environment

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{ invoice_number }}\n"
        "Customer: {{ customer_name }}\n"
        "Address: {{ billing_address.street }}, {{ billing_address.city }}, {{ billing_address.country }}\n"
        "Currency: {{ currency }}\n"
        "{% for item in line_items %}- {{ item.description }}: {{ item.quantity }} x {{ item.unit_price }}\n{% endfor %}"
        "{% if notes %}Notes: {{ notes }}\n{% endif %}"
    )
    return BenchCase(
        prepare=lambda: Environment().from_string(template_str),
        render=lambda t: t.render(fixture.data.model_dump()),
    )


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{ username }} \u2014 {{ display_name }}\n"
        "{{ bio }}\n"
        "Location: {{ location }} | Followers: {{ follower_count }}\n"
        "Contact: {{ email }}\n"
        "{% for link in links %}- {{ link.platform }}: {{ link.url }}\n{% endfor %}"
        "{% if verified %}Verified account\n{% endif %}"
    )
    return BenchCase(
        prepare=lambda: Environment().from_string(template_str),
        render=lambda t: t.render(fixture.data.model_dump()),
    )


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{ environment }} ({{ region_info[region]['name'] }}, {{ region_info[region]['datacenter'] }})\n"
        "Version: {{ version }} \u2014 commit {{ commit_sha }}\n"
        "Deployed by: {{ deployed_by }}\n"
        "Services:\n"
        "{% for s in services %}- {{ s['name'] }}: {{ status_labels[s['status']] }} ({{ s['latency_ms'] }}ms)\n{% endfor %}"
        "{% if rollback_available %}Rollback: available\n{% else %}Rollback: NOT available\n{% endif %}"
    )
    return BenchCase(
        prepare=lambda: Environment().from_string(template_str),
        render=lambda t: t.render(fixture.data.model_dump()),
    )


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    template_str = (
        "Release v{{ version }} — {{ project }}{% if hotfix %} [HOTFIX]{% endif %}\n"
        "Team: {{ team.name }} | Lead: {{ team.lead.name }} ({{ team.lead.email }})\n"
        "Components:\n"
        "{% for comp in components %}"
        "- {{ comp.name }} [{% if comp.deployed %}deployed{% else %}not deployed{% endif %}]"
        " tests: {{ comp.tests.passed }}/{{ comp.tests.total }} {{ comp.tests.pass_label }}\n"
        "{% for dep in comp.dependencies %}  - {{ dep.name }}@{{ dep.version }} ({{ dep.stability }})\n{% endfor %}"
        "{% endfor %}"
        "Environments:\n"
        "{% for env in environments %}"
        "- {{ env.name }}: {{ env.status }}{% if env.deployed_at %} on {{ env.deployed_at }}{% endif %}\n"
        "{% endfor %}"
    )
    return BenchCase(
        prepare=lambda: Environment().from_string(template_str),
        render=lambda t: t.render(fixture.data.model_dump()),
    )
