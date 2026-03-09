import django
from django.conf import settings

if not settings.configured:
    settings.configure(TEMPLATES=[{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [], "APP_DIRS": False, "OPTIONS": {},
    }])
    django.setup()

from django.template import Context, Template as DjangoTemplate

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
        prepare=lambda: DjangoTemplate(template_str),
        render=lambda t: t.render(Context(fixture.data.model_dump())),
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
        prepare=lambda: DjangoTemplate(template_str),
        render=lambda t: t.render(Context(fixture.data.model_dump())),
    )


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{ environment }} ({{ region_name }}, {{ region_datacenter }})\n"
        "Version: {{ version }} \u2014 commit {{ commit_sha }}\n"
        "Deployed by: {{ deployed_by }}\n"
        "Services:\n"
        "{% for s in services %}- {{ s.name }}: {{ s.status_label }} ({{ s.latency_ms }}ms)\n{% endfor %}"
        "{% if rollback_available %}Rollback: available\n{% else %}Rollback: NOT available\n{% endif %}"
    )
    def render(t: DjangoTemplate) -> str:
        d = fixture.data
        ctx = d.model_dump()
        region = d.region_info[d.region]
        ctx["region_name"] = region.name
        ctx["region_datacenter"] = region.datacenter
        for s_dict, s_obj in zip(ctx["services"], d.services):
            s_dict["status_label"] = d.status_labels[s_obj.status]
        return t.render(Context(ctx))
    return BenchCase(prepare=lambda: DjangoTemplate(template_str), render=render)


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    template_str = (
        "Release v{{ version }} \u2014 {{ project }}{% if hotfix %} [HOTFIX]{% endif %}\n"
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
        prepare=lambda: DjangoTemplate(template_str),
        render=lambda t: t.render(Context(fixture.data.model_dump())),
    )
