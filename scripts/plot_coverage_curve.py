#!/usr/bin/env python3
"""
Plot the JDart coverage-over-time curve from a ``coverage-curve.tsv`` file and
report the area under the curve (AUC).

The TSV is produced alongside every evaluation run (see
``master-thesis-obsidian-vault/Evaluation/.../coverage-curve.tsv``). Each row is
one ``jdart.evaluation`` telemetry line:

    path_index  elapsed_ms  branch_coverage  path_type

AUC is computed as a right-continuous step-function integral from ``t=0``
(assumed ``0 %`` coverage) to ``T = --end-time`` (defaults to the last
``elapsed_ms`` in the file). Between consecutive samples ``t_{i-1}`` and
``t_i`` the coverage is held at ``cov_{i-1}`` — i.e. the coverage "jumps" at
the moment a path completes. This matches the convention used by the
evaluation notes and is a conservative lower bound on true achieved coverage
(mid-path progress is invisible to us).

Usage::

    python3 scripts/plot_coverage_curve.py <tsv> [<tsv2> ...] \\
        [-o output.{png,svg,pdf}] [--end-time MS] [--title TITLE] \\
        [--labels LABEL1,LABEL2,...] [--no-shade] [--dpi N]

With multiple TSVs, curves are overlaid so different strategies can be
compared on the same axes. ``--labels`` overrides the legend entries; by
default the parent directory name of each TSV is used (which matches the
``dynamic-coverage-guided`` / ``dfs`` / ``bfs`` folder layout produced by the
evaluation workflow).
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class Curve:
    label: str
    times_ms: List[int]  # includes leading 0
    coverage: List[float]  # includes leading 0.0
    path_types: List[str]  # length == len(times_ms) - 1 (no type for the synthetic 0-point)
    end_time_ms: int

    @property
    def final_coverage(self) -> float:
        return self.coverage[-1]

    @property
    def auc_raw(self) -> float:
        """Right-continuous step-function integral, in %·ms."""
        total = 0.0
        for i in range(1, len(self.times_ms)):
            total += self.coverage[i - 1] * (self.times_ms[i] - self.times_ms[i - 1])
        total += self.coverage[-1] * (self.end_time_ms - self.times_ms[-1])
        return total

    @property
    def auc_avg(self) -> float:
        """Normalised AUC — average branch coverage over the run, in %."""
        return self.auc_raw / self.end_time_ms if self.end_time_ms > 0 else 0.0


def load_curve(tsv_path: Path, label: str | None, end_time_ms: int | None) -> Curve:
    times: List[int] = [0]
    coverage: List[float] = [0.0]
    path_types: List[str] = []

    with tsv_path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"path_index", "elapsed_ms", "branch_coverage", "path_type"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{tsv_path}: TSV is missing columns {sorted(missing)}; "
                f"got {reader.fieldnames}"
            )
        for row in reader:
            times.append(int(row["elapsed_ms"]))
            coverage.append(float(row["branch_coverage"]))
            path_types.append(row["path_type"])

    if len(times) == 1:
        raise ValueError(f"{tsv_path}: no data rows found")

    end = end_time_ms if end_time_ms is not None else times[-1]
    if end < times[-1]:
        raise ValueError(
            f"{tsv_path}: --end-time {end} ms precedes last sample at {times[-1]} ms"
        )

    return Curve(
        label=label or tsv_path.parent.name or tsv_path.stem,
        times_ms=times,
        coverage=coverage,
        path_types=path_types,
        end_time_ms=end,
    )


# Colour palette that matches the three canonical strategies when the labels
# come from the default folder layout. Any label not in the map falls back to
# matplotlib's default cycle.
DEFAULT_COLOURS = {
    "dynamic-coverage-guided": "#1f77b4",  # blue
    "dfs": "#9467bd",                       # purple (avoid red to not clash with ERROR markers)
    "bfs": "#2ca02c",                       # green
}

# Marker per path type — we plot markers at the sample points to make
# OK (improvements) vs IGNORE (pruned, flat) vs ERROR visible on the curve.
PATH_TYPE_MARKER = {
    "OK": ("o", "tab:blue"),
    "IGNORE": ("x", "tab:gray"),
    "ERROR": ("s", "tab:red"),
    "DONT_KNOW": ("^", "tab:orange"),
}


def plot_curves(curves: Sequence[Curve], args: argparse.Namespace) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless-safe
        import matplotlib.pyplot as plt
    except ImportError:
        sys.stderr.write(
            "matplotlib is required for plotting. Install with:\n"
            "  pip install -r requirements.txt\n"
            "or: pip install matplotlib\n"
        )
        sys.exit(2)

    # Convert to seconds for readability on anything longer than a couple of seconds.
    t_max_ms = max(c.end_time_ms for c in curves)
    use_seconds = t_max_ms >= 2000
    time_div = 1000.0 if use_seconds else 1.0
    time_unit = "s" if use_seconds else "ms"

    fig, ax = plt.subplots(figsize=(9.5, 5.5))

    for curve in curves:
        colour = DEFAULT_COLOURS.get(curve.label, None)
        xs = [t / time_div for t in curve.times_ms] + [curve.end_time_ms / time_div]
        ys = list(curve.coverage) + [curve.coverage[-1]]
        # Right-continuous step: value in [t_{i-1}, t_i) is coverage[i-1], so
        # drawstyle="steps-post" (hold value until next x) matches exactly.
        line, = ax.step(
            xs,
            ys,
            where="post",
            linewidth=1.8,
            label=f"{curve.label} — avg {curve.auc_avg:.2f}% · final {curve.final_coverage:.2f}%",
            color=colour,
        )
        plot_colour = line.get_color()

        if not args.no_shade:
            ax.fill_between(xs, 0, ys, step="post", alpha=0.08, color=plot_colour)

        # Scatter per-path samples, coloured by path type. OK markers use the
        # line colour so the improvements stay associated with the strategy,
        # but IGNORE/ERROR/DONT_KNOW use their own colour to pop out.
        for t_ms, cov, ptype in zip(
            curve.times_ms[1:], curve.coverage[1:], curve.path_types
        ):
            marker, marker_colour = PATH_TYPE_MARKER.get(ptype, ("o", plot_colour))
            face = plot_colour if ptype == "OK" else marker_colour
            # matplotlib warns when edgecolor is given to an unfilled marker
            # like "x", so only pass it for filled markers.
            kwargs = dict(zorder=3, color=face)
            if ptype == "OK":
                kwargs.update(s=26, edgecolors=plot_colour, linewidths=0.6)
            else:
                kwargs.update(s=16)
            ax.scatter(t_ms / time_div, cov, marker=marker, **kwargs)

    # Threshold guide if everything looks like a TimedOrBranchCoverageTermination run.
    if args.threshold is not None:
        ax.axhline(
            args.threshold,
            color="#888888",
            linestyle="--",
            linewidth=1.0,
            label=f"JDart branch-coverage threshold ({args.threshold:.0f}%)",
        )

    ax.set_xlim(left=0, right=t_max_ms / time_div)
    ax.set_ylim(0, 100)
    ax.set_xlabel(f"Elapsed JDart time ({time_unit})")
    ax.set_ylabel("Branch coverage (%, JDart-reported)")
    if args.title:
        ax.set_title(args.title)
    else:
        names = ", ".join(c.label for c in curves)
        ax.set_title(f"JDart coverage-over-time — {names}")
    ax.grid(True, linestyle=":", alpha=0.5)

    # Path-type legend (separate from the curve legend). The OK marker in the
    # plot inherits each curve's colour, so we show it in neutral black here
    # and spell that out in the label to avoid implying OK is any one colour.
    from matplotlib.lines import Line2D
    pt_handles = [
        Line2D([0], [0], marker="o", linestyle="", color="black",
               markersize=6, label="OK (new coverage, curve colour)"),
        Line2D([0], [0], marker="x", linestyle="", color="tab:gray",
               markersize=6, label="IGNORE (pruned)"),
        Line2D([0], [0], marker="s", linestyle="", color="tab:red",
               markersize=6, label="ERROR"),
    ]
    curve_legend = ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.add_artist(curve_legend)
    ax.legend(handles=pt_handles, loc="upper left", fontsize=8,
              title="Path type", title_fontsize=8, framealpha=0.95)

    fig.tight_layout()

    out_path = args.output
    if out_path is None:
        first = Path(args.inputs[0])
        suffix = ".png"
        out_path = first.with_name(first.stem + suffix)
    else:
        out_path = Path(out_path)

    fig.savefig(out_path, dpi=args.dpi)
    plt.close(fig)
    print(f"[plot] saved {out_path}")


def parse_labels(labels_arg: str | None, n: int) -> List[str | None]:
    if labels_arg is None:
        return [None] * n
    parts = [p.strip() for p in labels_arg.split(",")]
    if len(parts) != n:
        sys.exit(
            f"--labels has {len(parts)} entries but {n} input files were given"
        )
    return parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot JDart coverage-over-time from a coverage-curve.tsv and compute AUC."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="One or more coverage-curve.tsv files. Multiple files are overlaid.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output image path (.png, .svg, .pdf). Defaults to <input>.png.",
    )
    parser.add_argument(
        "--end-time",
        type=int,
        default=None,
        help="Run end time in milliseconds (T). Defaults to the last elapsed_ms "
        "in the first TSV. When overlaying multiple TSVs, each uses its own "
        "last elapsed_ms unless --end-time is provided, in which case all "
        "curves share that endpoint.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Override the plot title.",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Comma-separated legend labels, one per input file. Defaults to "
        "each file's parent folder name (e.g. dynamic-coverage-guided, dfs, bfs).",
    )
    parser.add_argument(
        "--no-shade",
        action="store_true",
        help="Skip the shaded AUC region under each curve.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90.0,
        help="Horizontal guide line at this branch-coverage threshold. "
        "Set to a negative value to hide. Default: 90.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Raster output DPI. Default: 150.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Only print the AUC summary, do not render an image.",
    )
    args = parser.parse_args()

    if args.threshold is not None and args.threshold < 0:
        args.threshold = None

    labels = parse_labels(args.labels, len(args.inputs))
    curves: List[Curve] = []
    for tsv_path, label in zip(args.inputs, labels):
        curves.append(load_curve(tsv_path, label, args.end_time))

    # Text summary — goes to stdout regardless of --no-plot.
    print(
        f"{'label':<30}  {'T (ms)':>8}  {'final %':>8}  {'AUC (%·ms)':>12}  {'AUC avg %':>10}"
    )
    print("-" * 76)
    for c in curves:
        print(
            f"{c.label:<30}  {c.end_time_ms:>8d}  {c.final_coverage:>8.2f}  "
            f"{c.auc_raw:>12.1f}  {c.auc_avg:>10.2f}"
        )

    if args.no_plot:
        return

    plot_curves(curves, args)


if __name__ == "__main__":
    main()
