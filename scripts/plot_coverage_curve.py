#!/usr/bin/env python3
"""
Plot the JDart coverage-over-time curve from a ``coverage-curve.tsv`` file and
report the area under the curve (AUC).

The TSV is produced alongside every evaluation run (see
``master-thesis-obsidian-vault/Evaluation/.../coverage-curve.tsv``). Each row is
one ``jdart.evaluation`` telemetry line:

    path_index  elapsed_ms  branch_coverage  path_type

AUC is computed as a right-continuous step-function integral of the JDart
branch-coverage curve. Between consecutive samples ``t_{i-1}`` and ``t_i``
the coverage is held at ``cov_{i-1}`` — i.e. the coverage "jumps" at the
moment a path completes. This is a conservative lower bound on true
achieved coverage (mid-path progress is invisible to us).

By default the integration window is ``[t_1, T_ext]`` — from the first
path's completion time to the longest normalised end-time across all
input curves. Strategies that terminated earlier are **extended at their
final coverage** to reach ``T_ext``. This removes the window-length bias
of per-own-window averaging (where a short run is penalised for
spending a larger fraction of its window in the "climb" phase) and
rewards strategies that reach the coverage plateau fastest.

JPF / class-loading startup time is excluded: each curve is shifted so
its own ``t_1`` lands at ``x = 0``, putting all strategies on a shared
"exploration time since first path" axis.

Pass ``--window-mode common`` to truncate to the shortest window
instead; ``--window-mode own`` for each curve's natural window (the
biased legacy behaviour). ``--include-startup`` integrates from ``t=0``
and plots absolute elapsed time (used by the first batch of evaluation
notes).

**Caveat on extended mode**: the plateau extension is only meaningful
when the early-terminating run stopped because of a coverage threshold.
If a run timed out, its real trajectory would probably have kept
climbing, so the extension underestimates what it would have reached.

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
    include_startup: bool = False
    # Where the AUC integration actually ends. Defaults to end_time_ms but can
    # be extended past the last sample (extending at final coverage) or
    # truncated below it (ignoring trailing samples) by the window-mode logic.
    effective_end_ms: int | None = None

    def __post_init__(self) -> None:
        if self.effective_end_ms is None:
            self.effective_end_ms = self.end_time_ms

    @property
    def final_coverage(self) -> float:
        return self.coverage[-1]

    @property
    def first_path_ms(self) -> int:
        """Elapsed time of the first path sample (t_1). 0 if there are no samples."""
        return self.times_ms[1] if len(self.times_ms) > 1 else 0

    @property
    def auc_start_ms(self) -> int:
        """Lower bound of the AUC integration window."""
        return 0 if self.include_startup else self.first_path_ms

    @property
    def auc_end_ms(self) -> int:
        """Upper bound of the AUC integration window."""
        return self.effective_end_ms  # type: ignore[return-value]

    @property
    def auc_window_ms(self) -> int:
        """Length of the AUC integration window."""
        return max(self.auc_end_ms - self.auc_start_ms, 0)

    @property
    def own_window_ms(self) -> int:
        """Length of the curve's natural window (end_time_ms - t_1)."""
        return max(self.end_time_ms - self.auc_start_ms, 0)

    @property
    def auc_raw(self) -> float:
        """Right-continuous step-function integral over ``[auc_start_ms, auc_end_ms]``.

        Between samples ``t_{i-1}`` and ``t_i`` coverage is held at
        ``cov_{i-1}``. If ``auc_end_ms`` exceeds the last sample, coverage
        is extended at ``coverage[-1]`` until ``auc_end_ms``. If
        ``auc_end_ms`` precedes the last sample, samples beyond the window
        are clipped.
        """
        start = self.auc_start_ms
        end = self.auc_end_ms
        if end <= start:
            return 0.0
        total = 0.0
        for i in range(1, len(self.times_ms)):
            t_prev, t_cur = self.times_ms[i - 1], self.times_ms[i]
            left = max(t_prev, start)
            right = min(max(t_cur, start), end)
            if right > left:
                total += self.coverage[i - 1] * (right - left)
        # Plateau extension past the last sample, if requested.
        total += self.coverage[-1] * max(end - max(self.times_ms[-1], start), 0)
        return total

    @property
    def auc_avg(self) -> float:
        """Normalised AUC — average branch coverage over the window, in %."""
        window = self.auc_window_ms
        return self.auc_raw / window if window > 0 else 0.0


def load_curve(
    tsv_path: Path,
    label: str | None,
    end_time_ms: int | None,
    include_startup: bool,
) -> Curve:
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
        include_startup=include_startup,
    )


# Colour palette that matches the three canonical strategies when the labels
# come from the default folder layout. Any label not in the map falls back to
# matplotlib's default cycle.
DEFAULT_COLOURS = {
    "dynamic-coverage-guided": "#1f77b4",  # blue
    "dfs": "#daa520",                       # goldenrod (avoid red to not clash with ERROR markers)
    "bfs": "#2ca02c",                       # green
}

# Pretty display names for the folder-level labels that show up in the
# evaluation artefact layout. Used for legend entries and the default title
# — the internal curve.label keeps the raw folder name so colour lookups
# still work.
DISPLAY_NAMES = {
    "dynamic-coverage-guided": "COVET",
    "dfs": "DFS",
    "bfs": "BFS",
}


def display_label(label: str) -> str:
    return DISPLAY_NAMES.get(label, label)

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

    # When startup is excluded (the default), shift each curve's time axis so
    # every strategy's first path lands at x = 0. This puts the three curves
    # on a common "exploration time" axis — boot / class-loading overhead
    # (which differs slightly per run but isn't strategy-specific) no longer
    # shifts the curves horizontally.
    normalize = not args.include_startup
    offsets_ms = {
        id(c): (c.first_path_ms if normalize else 0) for c in curves
    }
    # Use the integration window (incl. any plateau extension) to size the
    # x-axis, so the extended tail fits. For absolute mode this degenerates
    # to max(end_time_ms).
    x_max_ms = max(c.auc_end_ms - offsets_ms[id(c)] for c in curves)
    use_seconds = x_max_ms >= 2000
    time_div = 1000.0 if use_seconds else 1.0
    time_unit = "s" if use_seconds else "ms"

    fig, ax = plt.subplots(figsize=(9.5, 5.5))

    # Track whether any curve ended up being plateau-extended — used later
    # to add a legend entry explaining the dashed tail.
    any_extension = False

    for curve in curves:
        colour = DEFAULT_COLOURS.get(curve.label, None)
        offset = offsets_ms[id(curve)]
        # Skip the synthetic (0, 0) leading point when normalising — the
        # real first sample already sits at x = 0 after shifting.
        start_idx = 1 if normalize else 0
        # Natural curve segment ends at min(end_time_ms, auc_end_ms) — if the
        # window truncates (common mode), we clip; if it extends, the
        # natural segment ends at end_time_ms and an extension line follows.
        natural_end_ms = min(curve.end_time_ms, curve.auc_end_ms)
        natural_samples = [
            (t, c) for t, c in zip(curve.times_ms[start_idx:], curve.coverage[start_idx:])
            if t <= natural_end_ms
        ]
        xs = [(t - offset) / time_div for t, _ in natural_samples]
        ys = [c for _, c in natural_samples]
        # Cap the natural segment at natural_end_ms so step plotting ends
        # precisely at that x.
        if not xs or xs[-1] * time_div + offset < natural_end_ms:
            xs.append((natural_end_ms - offset) / time_div)
            ys.append(ys[-1] if ys else 0.0)
        # Right-continuous step: value in [t_{i-1}, t_i) is coverage[i-1], so
        # drawstyle="steps-post" (hold value until next x) matches exactly.
        line, = ax.step(
            xs,
            ys,
            where="post",
            linewidth=1.8,
            label=f"{display_label(curve.label)} — avg {curve.auc_avg:.2f}% · final {curve.final_coverage:.2f}%",
            color=colour,
        )
        plot_colour = line.get_color()

        # Plateau extension — only when auc_end_ms > end_time_ms.
        extension_ys = []
        if curve.auc_end_ms > curve.end_time_ms:
            any_extension = True
            ext_x0 = (curve.end_time_ms - offset) / time_div
            ext_x1 = (curve.auc_end_ms - offset) / time_div
            ax.plot(
                [ext_x0, ext_x1],
                [curve.final_coverage, curve.final_coverage],
                linestyle=(0, (4, 3)),
                linewidth=1.4,
                color=plot_colour,
                alpha=0.7,
                zorder=2,
            )
            extension_ys = [(ext_x0, ext_x1, curve.final_coverage)]

        if not args.no_shade:
            ax.fill_between(
                xs, 0, ys, step="post", alpha=0.08, color=plot_colour
            )
            for x0, x1, y in extension_ys:
                ax.fill_between(
                    [x0, x1], 0, [y, y], alpha=0.05, color=plot_colour
                )

        # Scatter per-path samples, coloured by path type. OK markers use the
        # line colour so the improvements stay associated with the strategy,
        # but IGNORE/ERROR/DONT_KNOW use their own colour to pop out. Skip
        # samples that fall outside the window (common-mode truncation).
        for t_ms, cov, ptype in zip(
            curve.times_ms[1:], curve.coverage[1:], curve.path_types
        ):
            if t_ms > natural_end_ms:
                continue
            marker, marker_colour = PATH_TYPE_MARKER.get(ptype, ("o", plot_colour))
            face = plot_colour if ptype == "OK" else marker_colour
            # matplotlib warns when edgecolor is given to an unfilled marker
            # like "x", so only pass it for filled markers.
            kwargs = dict(zorder=3, color=face)
            if ptype == "OK":
                kwargs.update(s=26, edgecolors=plot_colour, linewidths=0.6)
            else:
                kwargs.update(s=16)
            ax.scatter((t_ms - offset) / time_div, cov, marker=marker, **kwargs)

    # Threshold guide if everything looks like a TimedOrBranchCoverageTermination run.
    if args.threshold is not None:
        ax.axhline(
            args.threshold,
            color="#888888",
            linestyle="--",
            linewidth=1.0,
            label=f"JDart branch-coverage threshold ({args.threshold:.0f}%)",
        )

    ax.set_xlim(left=0, right=x_max_ms / time_div)
    ax.set_ylim(0, 100)
    if normalize:
        ax.set_xlabel(f"Exploration time since first path ({time_unit})")
    else:
        ax.set_xlabel(f"Elapsed JDart time ({time_unit})")
    ax.set_ylabel("Branch coverage (%)")
    if args.title:
        ax.set_title(args.title)
    else:
        names = " vs ".join(display_label(c.label) for c in curves)
        ax.set_title(f"Coverage over time — {names}")
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
    if any_extension:
        pt_handles.append(
            Line2D([0], [0], linestyle=(0, (4, 3)), color="black",
                   linewidth=1.4, alpha=0.7,
                   label="Plateau extension (terminated early, held at final cov.)")
        )
    curve_legend = ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.add_artist(curve_legend)
    # Stack the path-type legend in the lower-right, directly above the
    # curve-info legend. Both share the right edge (x=1.0 in axes fraction).
    ax.legend(
        handles=pt_handles,
        loc="lower right",
        bbox_to_anchor=(1.0, 0.22),
        ncol=1,
        fontsize=8,
        title="Path type",
        title_fontsize=8,
        framealpha=0.95,
    )

    fig.tight_layout()

    out_path = args.output
    if out_path is None:
        first = Path(args.inputs[0])
        suffix = ".png"
        out_path = first.with_name(first.stem + suffix)
    else:
        out_path = Path(out_path)

    # bbox_inches="tight" ensures the out-of-axes path-type legend is not
    # clipped by the figure bounds.
    fig.savefig(out_path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] saved {out_path}")


def apply_window_mode(curves: Sequence[Curve], mode: str) -> None:
    """Rewrite each curve's ``effective_end_ms`` so the AUC integration
    window matches the requested cross-curve convention.

    - ``extended``: every curve ends at ``auc_start_ms + max_own_window``.
      Curves that terminated earlier get their final coverage held until
      that endpoint.
    - ``common``: every curve ends at ``auc_start_ms + min_own_window``.
      Curves that ran longer get truncated.
    - ``own``: no change; each curve keeps its native end time.
    """
    if not curves:
        return
    windows = [c.own_window_ms for c in curves]
    if mode == "extended":
        target = max(windows)
    elif mode == "common":
        target = min(windows)
    elif mode == "own":
        return
    else:
        raise ValueError(f"unknown window mode: {mode}")
    for c in curves:
        c.effective_end_ms = c.auc_start_ms + target


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
    parser.add_argument(
        "--include-startup",
        action="store_true",
        help="Integrate AUC from t=0 and plot with an absolute elapsed-time "
        "x-axis. Default excludes JPF / class-loading startup (AUC from t_1) "
        "and normalises each curve's x-axis so every strategy's first path "
        "lands at x=0, putting them on a shared 'exploration time since "
        "first path' axis.",
    )
    parser.add_argument(
        "--window-mode",
        choices=["extended", "common", "own"],
        default="extended",
        help="How the AUC integration window is chosen across multiple curves. "
        "'extended' (default): integrate every curve over the longest "
        "normalised window, extending curves that terminated earlier at "
        "their final coverage — fair when runs stopped via a coverage "
        "threshold. 'common': truncate every curve to the shortest window. "
        "'own': each curve uses its own window (window-length biased; not "
        "recommended for cross-strategy comparison).",
    )
    args = parser.parse_args()

    if args.threshold is not None and args.threshold < 0:
        args.threshold = None

    labels = parse_labels(args.labels, len(args.inputs))
    curves: List[Curve] = []
    for tsv_path, label in zip(args.inputs, labels):
        curves.append(
            load_curve(tsv_path, label, args.end_time, args.include_startup)
        )

    apply_window_mode(curves, args.window_mode)

    # Text summary — goes to stdout regardless of --no-plot.
    # The table shows each curve's NATURAL characteristics (raw T_end from
    # telemetry, window = T_end - t_1). The shared AUC integration window
    # (which may differ from the per-curve natural window under extended /
    # common modes) is called out in the trailing note.
    header = (
        f"{'label':<30}  {'t_1 (ms)':>8}  {'T_end (ms)':>10}  "
        f"{'window (ms)':>11}  {'final %':>8}  {'AUC (%·ms)':>12}  {'AUC avg %':>10}"
    )
    print(header)
    print("-" * len(header))
    for c in curves:
        print(
            f"{c.label:<30}  {c.first_path_ms:>8d}  {c.end_time_ms:>10d}  "
            f"{c.own_window_ms:>11d}  {c.final_coverage:>8.2f}  "
            f"{c.auc_raw:>12.1f}  {c.auc_avg:>10.2f}"
        )

    startup_note = (
        "from t=0" if args.include_startup else "from t_1 (startup excluded)"
    )
    if args.window_mode == "extended":
        auc_window = max(c.own_window_ms for c in curves)
        print(
            f"\nAUC integrated {startup_note} over {auc_window} ms (longest "
            "natural window; curves that terminated earlier are extended at "
            "their final coverage)"
        )
    elif args.window_mode == "common":
        auc_window = min(c.own_window_ms for c in curves)
        print(
            f"\nAUC integrated {startup_note} over {auc_window} ms (shortest "
            "natural window; curves that ran longer are truncated)"
        )
    else:
        print(
            f"\nAUC integrated {startup_note} over each curve's own window"
        )

    if args.no_plot:
        return

    plot_curves(curves, args)


if __name__ == "__main__":
    main()
