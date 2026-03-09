import tornado.template

from benchmarks.fixtures import BenchCase, DeploymentReport, Fixture, Invoice, UserProfile

_loader = tornado.template.BaseLoader()


def bench_invoice(fixture: Fixture[Invoice]) -> BenchCase:
    template_str = (
        "Invoice #{{ invoice_number }}\n"
        "Customer: {{ customer_name }}\n"
        "Address: {{ billing_address['street'] }}, {{ billing_address['city'] }}, {{ billing_address['country'] }}\n"
        "Currency: {{ currency }}\n"
        "{% for item in line_items %}- {{ item['description'] }}: {{ item['quantity'] }} x {{ item['unit_price'] }}\n{% end %}"
        "{% if notes %}Notes: {{ notes }}\n{% end %}"
    )
    def prepare() -> tornado.template.Template:
        return tornado.template.Template(template_str, loader=_loader)
    return BenchCase(prepare=prepare, render=lambda t: t.generate(**fixture.data.model_dump()).decode())


def bench_user_profile(fixture: Fixture[UserProfile]) -> BenchCase:
    template_str = (
        "@{{ username }} \u2014 {{ display_name }}\n"
        "{{ bio }}\n"
        "Location: {{ location }} | Followers: {{ follower_count }}\n"
        "Contact: {{ email }}\n"
        "{% for link in links %}- {{ link['platform'] }}: {{ link['url'] }}\n{% end %}"
        "{% if verified %}Verified account\n{% end %}"
    )
    def prepare() -> tornado.template.Template:
        return tornado.template.Template(template_str, loader=_loader)
    return BenchCase(prepare=prepare, render=lambda t: t.generate(**fixture.data.model_dump()).decode())


def bench_deployment_report(fixture: Fixture[DeploymentReport]) -> BenchCase:
    template_str = (
        "Deployment Report\n"
        "Environment: {{ environment }} ({{ region_info[region]['name'] }}, {{ region_info[region]['datacenter'] }})\n"
        "Version: {{ version }} \u2014 commit {{ commit_sha }}\n"
        "Deployed by: {{ deployed_by }}\n"
        "Services:\n"
        "{% for s in services %}- {{ s['name'] }}: {{ status_labels[s['status']] }} ({{ s['latency_ms'] }}ms)\n{% end %}"
        "{% if rollback_available %}Rollback: available\n{% else %}Rollback: NOT available\n{% end %}"
    )
    def prepare() -> tornado.template.Template:
        return tornado.template.Template(template_str, loader=_loader)
    return BenchCase(prepare=prepare, render=lambda t: t.generate(**fixture.data.model_dump()).decode())


def bench_release_report(fixture):
    from benchmarks.fixtures import ReleaseReport  # noqa: F401
    template_str = (
        "Release v{{ version }} \u2014 {{ project }}{% if hotfix %} [HOTFIX]{% end %}\n"
        "Team: {{ team['name'] }} | Lead: {{ team['lead']['name'] }} ({{ team['lead']['email'] }})\n"
        "Components:\n"
        "{% for comp in components %}"
        "- {{ comp['name'] }} [{% if comp['deployed'] %}deployed{% else %}not deployed{% end %}]"
        " tests: {{ comp['tests']['passed'] }}/{{ comp['tests']['total'] }} {{ comp['tests']['pass_label'] }}\n"
        "{% for dep in comp['dependencies'] %}  - {{ dep['name'] }}@{{ dep['version'] }} ({{ dep['stability'] }})\n{% end %}"
        "{% end %}"
        "Environments:\n"
        "{% for env in environments %}"
        "- {{ env['name'] }}: {{ env['status'] }}{% if env['deployed_at'] %} on {{ env['deployed_at'] }}{% end %}\n"
        "{% end %}"
    )
    def prepare():
        return tornado.template.Template(template_str, loader=_loader)
    return BenchCase(prepare=prepare, render=lambda t: t.generate(**fixture.data.model_dump()).decode())
