"""
Template library benchmark evaluation script.

Usage:  python benchmarks/run.py
        python benchmarks/run.py --iterations 5000
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import timeit
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.fixtures import BenchCase, Fixture, invoice, profile, release, report

FIXTURES: list[Fixture] = [invoice, profile, report, release]

TOOLS: list[str] = [
    "benchmarks.tools.pyhandlebars",
    "benchmarks.tools.pybars3",
    "benchmarks.tools.python_handlebars",
    "benchmarks.tools.jinja2",
    "benchmarks.tools.mako",
    "benchmarks.tools.ashes",
    "benchmarks.tools.django",
    "benchmarks.tools.tenjin",
    "benchmarks.tools.wheezy",
    "benchmarks.tools.string_template",
    "benchmarks.tools.chevron",
    "benchmarks.tools.pystache",
    "benchmarks.tools.cheetah",
    "benchmarks.tools.tornado",
    "benchmarks.tools.bottle",
    "benchmarks.tools.python",
]

BenchFn = Callable[[Fixture], BenchCase]


def _fn_name(fixture: Fixture) -> str:
    return "bench_" + fixture.label.replace(" ", "_")


@dataclass
class PhaseMs:
    prepare: float
    render: float

    @property
    def total(self) -> float:
        return self.prepare + self.render


@dataclass
class CaseResult:
    fixture_label: str
    ms: PhaseMs
    correct: bool
    raw_prepare_ms: list[float]
    raw_render_ms: list[float]


@dataclass
class ToolResult:
    tool: str
    cases: list[CaseResult]

    def avg(self) -> PhaseMs:
        n = len(self.cases)
        return PhaseMs(
            prepare=sum(c.ms.prepare for c in self.cases) / n,
            render=sum(c.ms.render for c in self.cases) / n,
        )

    def case(self, label: str) -> CaseResult:
        return next(c for c in self.cases if c.fixture_label == label)

    def std(self) -> PhaseMs:
        if len(self.cases) < 2:
            return PhaseMs(prepare=0.0, render=0.0)
        return PhaseMs(
            prepare=statistics.stdev(c.ms.prepare for c in self.cases),
            render=statistics.stdev(c.ms.render for c in self.cases),
        )

    def all_correct(self) -> bool:
        return all(c.correct for c in self.cases)


def run_tool(module_name: str, n: int, warmup: int) -> ToolResult:
    mod = importlib.import_module(module_name)
    tool_label = module_name.split(".")[-1]
    cases: list[CaseResult] = []

    for fixture in FIXTURES:
        fn: BenchFn = getattr(mod, _fn_name(fixture))
        bench = fn(fixture)

        # Warm-up: prime Python's inline caches, branch predictor, and any
        # lazy internal caching inside the template engine before timing starts.
        for _ in range(warmup):
            bench.prepare()

        raw_prepare_ms = [t * 1000 for t in timeit.repeat(bench.prepare, number=1, repeat=n)]

        state = bench.prepare()
        for _ in range(warmup):
            bench.render(state)

        raw_render_ms = [t * 1000 for t in timeit.repeat(lambda: bench.render(state), number=1, repeat=n)]

        actual = bench.render(state)
        cases.append(
            CaseResult(
                fixture_label=fixture.label,
                ms=PhaseMs(
                    prepare=statistics.mean(raw_prepare_ms),
                    render=statistics.mean(raw_render_ms),
                ),
                correct=actual == fixture.expected,
                raw_prepare_ms=raw_prepare_ms,
                raw_render_ms=raw_render_ms,
            )
        )

    return ToolResult(tool=tool_label, cases=cases)


def _ranking_table(
    results: list[ToolResult],
    col_tool: int,
    col_n: int,
    get_ms: Callable[[ToolResult], PhaseMs],
    label: str,
    get_std: Callable[[ToolResult], PhaseMs] | None = None,
) -> None:
    ranked = sorted(results, key=lambda r: get_ms(r).render)
    print(f"\n  [{label}]")
    std_header = f"  {'Render std':>{col_n}}" if get_std else ""
    print(
        f"  {'Tool':<{col_tool}} {'Prepare (ms)':>{col_n}}  {'Render (ms)':>{col_n}}  {'Total (ms)':>{col_n}}{std_header}"
    )
    sep_width = col_tool + col_n * 3 + 6 + (col_n + 2 if get_std else 0)
    print("  " + "-" * sep_width)
    for r in ranked:
        ms = get_ms(r)
        std_col = f"  {get_std(r).render:>{col_n}.4f}" if get_std else ""
        print(
            f"  {r.tool:<{col_tool}} {ms.prepare:>{col_n}.4f}  {ms.render:>{col_n}.4f}  {ms.total:>{col_n}.4f}{std_col}"
        )
    fastest, slowest = ranked[0], ranked[-1]
    ratio = (
        slowest_render / fastest_render
        if (fastest_render := get_ms(fastest).render) > 0 and (slowest_render := get_ms(slowest).render)
        else float("inf")
    )  # noqa: E501
    # simpler version:
    f_ms = get_ms(fastest).render
    s_ms = get_ms(slowest).render
    ratio = s_ms / f_ms if f_ms > 0 else float("inf")
    print(
        f"  fastest render: {fastest.tool} ({f_ms:.4f} ms)  |  slowest: {slowest.tool} ({s_ms:.4f} ms)  |  ratio: {ratio:.1f}x"
    )

def print_report(results: list[ToolResult], n: int) -> None:
    col_case = max(len(f.label) for f in FIXTURES) + 2
    col_n = 11
    width = col_case + col_n * 3 + 20

    def sep(char: str = "=") -> str:
        return char * width

    header_row = (
        f"  {'Case':<{col_case}} {'Prepare (ms)':>{col_n}}  {'Render (ms)':>{col_n}}  {'Total (ms)':>{col_n}}  Output"
    )

    print()
    print(sep())
    print(f"  Benchmark report  —  {n:,} iterations per phase")
    print(sep())

    for tool_result in results:
        print(f"\n  Tool: {tool_result.tool}\n")
        print(header_row)
        print("  " + sep("-")[: width - 2])
        for c in tool_result.cases:
            status = "OK" if c.correct else "MISMATCH"
            print(
                f"  {c.fixture_label:<{col_case}}"
                f" {c.ms.prepare:>{col_n}.4f}"
                f"  {c.ms.render:>{col_n}.4f}"
                f"  {c.ms.total:>{col_n}.4f}"
                f"  {status}"
            )
        avg = tool_result.avg()
        std = tool_result.std()
        print(f"  {'avg':<{col_case}} {avg.prepare:>{col_n}.4f}  {avg.render:>{col_n}.4f}  {avg.total:>{col_n}.4f}")
        print(f"  {'std':<{col_case}} {std.prepare:>{col_n}.4f}  {std.render:>{col_n}.4f}  {std.total:>{col_n}.4f}")

    if len(results) > 1:
        col_tool = max(len(r.tool) for r in results) + 2
        print()
        print(sep())
        print("\n  Summary — ranked by render time (fastest first)\n")

        # One table per fixture case
        for fixture in FIXTURES:
            _ranking_table(
                results,
                col_tool,
                col_n,
                lambda r, lbl=fixture.label: r.case(lbl).ms,
                fixture.label,
            )

        # Overall average
        _ranking_table(results, col_tool, col_n, lambda r: r.avg(), "overall average", get_std=lambda r: r.std())

    print()
    print(sep())
    print()

    if any(not r.all_correct() for r in results):
        print("  WARNING: one or more cases produced unexpected output.")
        sys.exit(1)

def _grouped_boxplot(
    ax,
    series_data: list[list[list[float]]],
    series_labels: list[str],
    series_colors: list[str],
    group_labels: list[str],
    title: str,
    log_scale: bool = False,
    group_separators: bool = False,
    bold_labels: set[str] | None = None,
) -> None:
    """Draw grouped boxplots: one group per tool, one box per series within each group.

    series_data[series_idx][group_idx] → list[float]
    """
    n_groups = len(group_labels)
    n_series = len(series_labels)
    group_width = 0.75
    box_width = group_width / n_series

    legend_patches = []
    for s_idx, (s_label, color) in enumerate(zip(series_labels, series_colors)):
        offset = (s_idx - (n_series - 1) / 2.0) * box_width
        positions = [i + offset for i in range(n_groups)]
        bp = ax.boxplot(
            series_data[s_idx],
            positions=positions,
            widths=box_width * 0.85,
            showfliers=False,
            patch_artist=True,
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(linewidth=1.0),
            capprops=dict(linewidth=1.0),
        )
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(0.70)
        legend_patches.append(bp["boxes"][0])

    ax.set_xticks(range(n_groups))
    ax.set_xticklabels(group_labels, rotation=45, ha="right", fontsize=8)
    if bold_labels:
        for tick in ax.get_xticklabels():
            if tick.get_text() in bold_labels:
                tick.set_fontweight("bold")
    ax.set_xlim(-0.5, n_groups - 0.5)
    if group_separators:
        for i in range(n_groups - 1):
            ax.axvline(i + 0.5, color="gray", linewidth=0.6, linestyle="--", alpha=0.5)
    scale_suffix = " (log scale)" if log_scale else ""
    ax.set_title(f"{title}{scale_suffix}", fontweight="bold", fontsize=11)
    ax.set_ylabel("ms")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if log_scale:
        ax.set_yscale("log")
    ax.legend(legend_patches, series_labels, loc="upper left", fontsize=8, framealpha=0.7)


def plot_diagrams(results: list[ToolResult], output_dir: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib not installed — skipping plots (pip install matplotlib)")
        return

    PHASE_COLORS = ["#4C72B0", "#DD8452", "#55A868"]   # prepare / render / total
    FIXTURE_COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fixtures = [c.fixture_label for c in results[0].cases]

    phase_configs = [
        ("Prepare", lambda c: c.raw_prepare_ms),
        ("Render", lambda c: c.raw_render_ms),
        ("Total", lambda c: [p + rn for p, rn in zip(c.raw_prepare_ms, c.raw_render_ms)]),
    ]

    # ── Per-fixture: grouped boxplot (prepare / render / total per tool) ─────
    # Layout: 2 rows (linear / log), 1 wide grouped plot each
    for fixture_label in fixtures:
        # Sort tools by median render time
        render_medians = [
            statistics.median(r.case(fixture_label).raw_render_ms) for r in results
        ]
        order = sorted(range(len(results)), key=lambda i: render_medians[i])
        sorted_results = [results[i] for i in order]
        sorted_tool_labels = [r.tool for r in sorted_results]

        # series_data[phase][tool] = raw values
        series_data = [
            [get_data(r.case(fixture_label)) for r in sorted_results]
            for _, get_data in phase_configs
        ]
        series_labels = [name for name, _ in phase_configs]

        fig, axes = plt.subplots(2, 1, figsize=(22, 14))
        fig.suptitle(f"Template Benchmark — {fixture_label}", fontsize=14, fontweight="bold")
        for ax, log_scale in zip(axes, [False, True]):
            _grouped_boxplot(
                ax,
                series_data,
                series_labels,
                PHASE_COLORS,
                sorted_tool_labels,
                fixture_label,
                log_scale=log_scale,
            )

        plt.tight_layout()
        slug = fixture_label.replace(" ", "_")
        path = out / f"benchmark_{slug}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Plot: {path}")

    # ── README summary: render time for all fixtures, grouped by tool ─────────
    # Sort tools by mean render time across all fixtures
    avg_render = [
        statistics.mean(
            statistics.median(r.case(f).raw_render_ms) for f in fixtures
        )
        for r in results
    ]
    order = sorted(range(len(results)), key=lambda i: avg_render[i])
    sorted_results = [results[i] for i in order]
    sorted_tool_labels = [r.tool for r in sorted_results]

    # series_data[fixture][tool] = raw render values
    series_data = [
        [r.case(fixture_label).raw_render_ms for r in sorted_results]
        for fixture_label in fixtures
    ]

    fig, axes = plt.subplots(2, 1, figsize=(22, 14))
    fig.suptitle(
        "Template Benchmark — Render Time (all examples)",
        fontsize=15,
        fontweight="bold",
    )
    for ax, log_scale in zip(axes, [False, True]):
        _grouped_boxplot(
            ax,
            series_data,
            fixtures,
            FIXTURE_COLORS,
            sorted_tool_labels,
            "Render time per example",
            log_scale=log_scale,
            group_separators=True,
            bold_labels={"pyhandlebars"},
        )

    plt.tight_layout()
    path = out / "benchmark_summary.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot: {path}")


def _load_results_from_json(path: str) -> tuple[list[ToolResult], int, int]:
    data = json.loads(Path(path).read_text())
    results = []
    for t in data["tools"]:
        cases = [
            CaseResult(
                fixture_label=c["fixture"],
                ms=PhaseMs(prepare=c["prepare_ms"], render=c["render_ms"]),
                correct=c["correct"],
                raw_prepare_ms=c["raw_prepare_ms"],
                raw_render_ms=c["raw_render_ms"],
            )
            for c in t["cases"]
        ]
        results.append(ToolResult(tool=t["tool"], cases=cases))
    return results, data.get("iterations", 0), data.get("warmup", 0)


def _phase_dict(ms: PhaseMs) -> dict:
    return {"prepare_ms": ms.prepare, "render_ms": ms.render, "total_ms": ms.total}


def _summary_ranking(results: list[ToolResult], get_ms: Callable[[ToolResult], PhaseMs]) -> list[dict]:
    ranked = sorted(results, key=lambda r: get_ms(r).render)
    fastest_render = get_ms(ranked[0]).render
    return [
        {
            "rank": i + 1,
            "tool": r.tool,
            **_phase_dict(get_ms(r)),
            "ratio_to_fastest": round(get_ms(r).render / fastest_render, 2) if fastest_render > 0 else None,
        }
        for i, r in enumerate(ranked)
    ]


def export_json(results: list[ToolResult], path: str, n: int, warmup: int) -> None:
    data = {
        "iterations": n,
        "warmup": warmup,
        "tools": [
            {
                "tool": r.tool,
                "cases": [
                    {
                        "fixture": c.fixture_label,
                        **_phase_dict(c.ms),
                        "correct": c.correct,
                        "raw_prepare_ms": c.raw_prepare_ms,
                        "raw_render_ms": c.raw_render_ms,
                    }
                    for c in r.cases
                ],
                "avg": _phase_dict(r.avg()),
                "std": _phase_dict(r.std()),
            }
            for r in results
        ],
        "summary": {
            "overall_avg": _summary_ranking(results, lambda r: r.avg()),
            "per_fixture": [
                {
                    "fixture": fixture.label,
                    "ranked": _summary_ranking(results, lambda r, lbl=fixture.label: r.case(lbl).ms),
                }
                for fixture in FIXTURES
            ],
        },
    }
    Path(path).write_text(json.dumps(data, indent=2))
    print(f"  Results written to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run template library benchmarks.")
    parser.add_argument("--iterations", "-n", type=int, default=1_000)
    parser.add_argument(
        "--warmup", "-w", type=int, default=5, metavar="N", help="Warm-up iterations before timing (default: 3)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="report.json", metavar="FILE", help="Export results to JSON file"
    )
    parser.add_argument(
        "--plots", "-p", type=str, default=None, metavar="DIR",
        help="Generate boxplot diagrams into DIR (requires matplotlib)",
    )
    parser.add_argument(
        "--from-json", type=str, default=None, metavar="FILE",
        help="Load results from an existing JSON report instead of running benchmarks",
    )
    args = parser.parse_args()

    if args.from_json:
        results, n, warmup = _load_results_from_json(args.from_json)
        print(f"  Loaded results from {args.from_json} ({n:,} iterations, warmup {warmup})")
    else:
        n = args.iterations
        print(
            f"Running {len(TOOLS)} tool(s) × {len(FIXTURES)} cases × {n:,} iterations per phase (warmup: {args.warmup}) …"
        )
        results = []
        for tool in TOOLS:
            print(f"--- Tool: {tool}")
            results.append(run_tool(tool, n, args.warmup))
        print_report(results, n)
        if args.output:
            export_json(results, args.output, n, args.warmup)

    if args.plots:
        plot_diagrams(results, args.plots)


if __name__ == "__main__":
    main()
