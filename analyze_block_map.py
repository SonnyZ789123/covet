#!/usr/bin/env python3
"""
Analyze the ICFG block map JSON to understand edge hit distributions,
coverage state consistency, and branchIndex semantics.

This script investigates potential issues that could affect JDart's
CoverageHeuristicStrategy when using this block map.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BLOCK_MAP_PATH = Path(
    "/Users/yoran.mertens/dev/master-thesis/covet"
    "/development/data/blockmaps/icfg_block_map.json"
)

COVERAGE_DATA_PATH = Path(
    "/Users/yoran.mertens/dev/master-thesis/covet"
    "/development/data/coverage/coverage_data.json"
)


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def analyze(data, coverage_data):
    method_maps = data.get("methodBlockMaps", [])
    print(f"Total method block maps: {len(method_maps)}")
    print()

    # -- Aggregate counters --
    total_blocks = 0
    total_edges = 0

    edge_hits_minus1 = 0
    edge_hits_zero = 0
    edge_hits_positive = 0

    blocks_with_edges = 0
    blocks_without_edges = 0

    blocks_all_edges_minus1 = []
    blocks_mixed_minus1 = []

    coverage_state_counts = Counter()
    coverage_state_of_all_minus1 = Counter()
    coverage_state_of_any_minus1 = Counter()

    branch_type_counts = Counter()
    branch_index_by_type = defaultdict(Counter)

    inconsistent_blocks = []
    covered_with_minus1_edges = []
    not_covered_with_positive_edges = []
    partial_blocks_edge_analysis = []
    if_branch_index_patterns = []
    method_summaries = []

    for mm in method_maps:
        method_name = mm.get("fullName", "<unknown>")
        blocks = mm.get("blocks", [])
        method_block_count = len(blocks)
        method_edge_count = 0
        method_edges_minus1 = 0

        for block in blocks:
            total_blocks += 1
            block_id = block["id"]
            coverage_state = block["coverageData"]["coverageState"]
            edges = block.get("edges", [])
            coverage_state_counts[coverage_state] += 1

            if not edges:
                blocks_without_edges += 1
                continue

            blocks_with_edges += 1
            total_edges += len(edges)
            method_edge_count += len(edges)

            edge_hit_values = []
            for edge in edges:
                hits = edge["hits"]
                branch_type = edge["branchType"]
                branch_index = edge["branchIndex"]

                branch_type_counts[branch_type] += 1
                branch_index_by_type[branch_type][branch_index] += 1
                edge_hit_values.append(hits)

                if hits == -1:
                    edge_hits_minus1 += 1
                    method_edges_minus1 += 1
                elif hits == 0:
                    edge_hits_zero += 1
                elif hits > 0:
                    edge_hits_positive += 1

            all_minus1 = all(h == -1 for h in edge_hit_values)
            any_minus1 = any(h == -1 for h in edge_hit_values)
            any_positive = any(h > 0 for h in edge_hit_values)
            all_positive = all(h > 0 for h in edge_hit_values)

            if all_minus1:
                blocks_all_edges_minus1.append(
                    (method_name, block_id, coverage_state, edges)
                )
                coverage_state_of_all_minus1[coverage_state] += 1

            if any_minus1 and not all_minus1:
                blocks_mixed_minus1.append(
                    (method_name, block_id, coverage_state, edges)
                )

            if any_minus1:
                coverage_state_of_any_minus1[coverage_state] += 1

            if coverage_state == "COVERED" and any_minus1:
                covered_with_minus1_edges.append(
                    (method_name, block_id, edges)
                )

            if coverage_state == "NOT_COVERED" and any_positive:
                not_covered_with_positive_edges.append(
                    (method_name, block_id, edges)
                )

            if coverage_state == "PARTIALLY_COVERED":
                has_taken = any(h > 0 for h in edge_hit_values)
                has_not_taken = any(h == 0 for h in edge_hit_values)
                has_unknown = any(h == -1 for h in edge_hit_values)
                partial_blocks_edge_analysis.append(
                    {
                        "method": method_name,
                        "block_id": block_id,
                        "edge_hits": edge_hit_values,
                        "has_taken": has_taken,
                        "has_not_taken": has_not_taken,
                        "has_unknown": has_unknown,
                        "edges": edges,
                    }
                )

            if coverage_state == "COVERED" and len(edges) == 2:
                if not all_positive:
                    inconsistent_blocks.append(
                        {
                            "type": "COVERED_but_not_all_positive",
                            "method": method_name,
                            "block_id": block_id,
                            "edge_hits": edge_hit_values,
                            "edges": edges,
                        }
                    )

            if coverage_state == "NOT_COVERED" and any_positive:
                inconsistent_blocks.append(
                    {
                        "type": "NOT_COVERED_but_has_positive",
                        "method": method_name,
                        "block_id": block_id,
                        "edge_hits": edge_hit_values,
                        "edges": edges,
                    }
                )

            if_true_indices = []
            if_false_indices = []
            for edge in edges:
                if edge["branchType"] == "IF_TRUE":
                    if_true_indices.append(edge["branchIndex"])
                elif edge["branchType"] == "IF_FALSE":
                    if_false_indices.append(edge["branchIndex"])

            if if_true_indices or if_false_indices:
                if_branch_index_patterns.append(
                    {
                        "method": method_name,
                        "block_id": block_id,
                        "if_true_indices": if_true_indices,
                        "if_false_indices": if_false_indices,
                    }
                )

        method_summaries.append(
            {
                "method": method_name,
                "blocks": method_block_count,
                "edges": method_edge_count,
                "edges_minus1": method_edges_minus1,
            }
        )

    # ================================================================
    # REPORT
    # ================================================================
    sep = "=" * 72

    print(sep)
    print("1. OVERALL STATISTICS")
    print(sep)
    print(f"  Total blocks:         {total_blocks}")
    print(f"  Blocks with edges:    {blocks_with_edges}")
    print(f"  Blocks without edges: {blocks_without_edges}")
    print(f"  Total edges:          {total_edges}")
    print()

    print(sep)
    print("2. EDGE HIT VALUE DISTRIBUTION")
    print(sep)
    print(f"  hits = -1:  {edge_hits_minus1:>5}  ({edge_hits_minus1/total_edges*100:.1f}%)")
    print(f"  hits =  0:  {edge_hits_zero:>5}  ({edge_hits_zero/total_edges*100:.1f}%)")
    print(f"  hits >  0:  {edge_hits_positive:>5}  ({edge_hits_positive/total_edges*100:.1f}%)")
    print()

    print(sep)
    print("3. COVERAGE STATE DISTRIBUTION (all blocks)")
    print(sep)
    for state, count in coverage_state_counts.most_common():
        print(f"  {state:>20s}: {count:>5}  ({count/total_blocks*100:.1f}%)")
    print()

    print(sep)
    print("4. BLOCKS WHERE ALL EDGES HAVE hits=-1")
    print(sep)
    print(f"  Count: {len(blocks_all_edges_minus1)}")
    print()
    print("  Coverage state breakdown of these blocks:")
    for state, count in coverage_state_of_all_minus1.most_common():
        print(f"    {state:>20s}: {count}")
    print()
    print("  Detailed listing:")
    for method, bid, state, edges in blocks_all_edges_minus1:
        short_method = method.split(".")[-1].split("(")[0] if "." in method else method
        edge_types = [f"{e['branchType']}(idx={e['branchIndex']})" for e in edges]
        print(f"    Block {bid:>3} in ...{short_method}  state={state:>20s}  edges={edge_types}")
    print()

    print(sep)
    print("5. BLOCKS WITH MIXED hits=-1 AND OTHER VALUES")
    print(sep)
    print(f"  Count: {len(blocks_mixed_minus1)}")
    if blocks_mixed_minus1:
        for method, bid, state, edges in blocks_mixed_minus1:
            short_method = method.split(".")[-1].split("(")[0] if "." in method else method
            edge_desc = [f"{e['branchType']}(idx={e['branchIndex']},hits={e['hits']})" for e in edges]
            print(f"    Block {bid:>3} in ...{short_method}  state={state:>20s}  edges={edge_desc}")
    print()

    print(sep)
    print("6. CONSISTENCY: COVERED BLOCKS WITH hits=-1 EDGES")
    print(sep)
    print(f"  Count: {len(covered_with_minus1_edges)}")
    print()
    for method, bid, edges in covered_with_minus1_edges:
        short_method = method.split(".")[-1].split("(")[0] if "." in method else method
        edge_desc = [f"{e['branchType']}(idx={e['branchIndex']},hits={e['hits']})" for e in edges]
        print(f"    Block {bid:>3} in ...{short_method}  edges={edge_desc}")
    print()

    print(sep)
    print("7. CONSISTENCY: NOT_COVERED BLOCKS WITH hits>0 EDGES (BUGS)")
    print(sep)
    print(f"  Count: {len(not_covered_with_positive_edges)}")
    if not_covered_with_positive_edges:
        for method, bid, edges in not_covered_with_positive_edges:
            short_method = method.split(".")[-1].split("(")[0] if "." in method else method
            edge_desc = [f"{e['branchType']}(idx={e['branchIndex']},hits={e['hits']})" for e in edges]
            print(f"    Block {bid:>3} in ...{short_method}  edges={edge_desc}")
    else:
        print("  None found (good).")
    print()

    print(sep)
    print("8. PARTIALLY_COVERED BLOCKS: EDGE ANALYSIS")
    print(sep)
    print(f"  Total PARTIALLY_COVERED blocks with edges: {len(partial_blocks_edge_analysis)}")
    print()
    partial_consistent = 0
    partial_all_minus1 = 0
    partial_no_taken = 0
    partial_other = 0
    for p in partial_blocks_edge_analysis:
        hit_vals = p["edge_hits"]
        if all(h == -1 for h in hit_vals):
            partial_all_minus1 += 1
        elif p["has_taken"] and (p["has_not_taken"] or p["has_unknown"]):
            partial_consistent += 1
        elif not p["has_taken"]:
            partial_no_taken += 1
        else:
            partial_other += 1

    print(f"  Consistent (has taken + not-taken edges):   {partial_consistent}")
    print(f"  All edges hits=-1 (no edge-level data):     {partial_all_minus1}")
    print(f"  No taken edge but state=PARTIAL:            {partial_no_taken}")
    print(f"  Other:                                      {partial_other}")
    print()

    print(sep)
    print("9. BRANCH TYPE DISTRIBUTION")
    print(sep)
    for bt, count in branch_type_counts.most_common():
        print(f"    {bt:>15s}: {count:>5}")
    print()

    print(sep)
    print("10. branchIndex VALUES PER BRANCH TYPE")
    print(sep)
    for bt in sorted(branch_index_by_type.keys()):
        indices = branch_index_by_type[bt]
        print(f"    {bt}:")
        for idx, count in sorted(indices.items()):
            print(f"      branchIndex={idx}: {count} occurrences")
    print()

    print(sep)
    print("11. branchIndex CONSISTENCY FOR IF_TRUE/IF_FALSE PAIRS")
    print(sep)
    if_true_always_0 = 0
    if_true_not_0 = 0
    if_false_always_1 = 0
    if_false_not_1 = 0
    for p in if_branch_index_patterns:
        for idx in p["if_true_indices"]:
            if idx == 0:
                if_true_always_0 += 1
            else:
                if_true_not_0 += 1
        for idx in p["if_false_indices"]:
            if idx == 1:
                if_false_always_1 += 1
            else:
                if_false_not_1 += 1

    print(f"    IF_TRUE  with branchIndex=0: {if_true_always_0}  (expected)")
    print(f"    IF_TRUE  with branchIndex!=0: {if_true_not_0}  (unexpected)")
    print(f"    IF_FALSE with branchIndex=1: {if_false_always_1}  (expected)")
    print(f"    IF_FALSE with branchIndex!=1: {if_false_not_1}  (unexpected)")
    print()
    if if_true_not_0 or if_false_not_1:
        print("    WARNING: branchIndex is NOT always 0=IF_TRUE, 1=IF_FALSE!")
    else:
        print("    CONSISTENT: branchIndex=0 always maps to IF_TRUE, branchIndex=1 always maps to IF_FALSE.")
    print()

    # -- What does hits=-1 mean? --
    print(sep)
    print("12. ANALYSIS: WHAT DOES hits=-1 MEAN?")
    print(sep)

    goto_minus1 = 0
    if_minus1 = 0
    normal_minus1 = 0
    switch_minus1 = 0
    for mm in method_maps:
        for block in mm.get("blocks", []):
            for edge in block.get("edges", []):
                if edge["hits"] == -1:
                    bt = edge["branchType"]
                    if bt == "GOTO":
                        goto_minus1 += 1
                    elif bt in ("IF_TRUE", "IF_FALSE"):
                        if_minus1 += 1
                    elif bt == "NORMAL":
                        normal_minus1 += 1
                    else:
                        switch_minus1 += 1

    print(f"    hits=-1 on GOTO edges:             {goto_minus1}")
    print(f"    hits=-1 on IF_TRUE/IF_FALSE edges: {if_minus1}")
    print(f"    hits=-1 on NORMAL edges:           {normal_minus1}")
    print(f"    hits=-1 on SWITCH_* edges:         {switch_minus1}")
    print()

    total_if_edges = branch_type_counts.get("IF_TRUE", 0) + branch_type_counts.get("IF_FALSE", 0)
    if_zero = sum(
        1
        for mm in method_maps
        for block in mm.get("blocks", [])
        for edge in block.get("edges", [])
        if edge["branchType"] in ("IF_TRUE", "IF_FALSE") and edge["hits"] == 0
    )
    if_pos = total_if_edges - if_minus1 - if_zero

    print(f"    Total IF_TRUE + IF_FALSE edges: {total_if_edges}")
    print(f"    Of those with hits=-1:          {if_minus1}  ({if_minus1/max(total_if_edges,1)*100:.1f}%)")
    print(f"    Of those with hits=0:           {if_zero}")
    print(f"    Of those with hits>0:           {if_pos}")
    print()

    # -- Line-level analysis for COVERED blocks with hits=-1 IF edges --
    print(sep)
    print("13. COVERED BLOCKS WITH hits=-1 IF EDGES: LINE-LEVEL ANALYSIS")
    print(sep)
    print()
    print("    These blocks have coverageState=COVERED, all lines hit,")
    print("    but the IF edges show hits=-1 (no branch data resolved).")
    print()
    for mm in method_maps:
        for block in mm.get("blocks", []):
            state = block["coverageData"]["coverageState"]
            edges = block.get("edges", [])
            if_edges = [e for e in edges if e["branchType"] in ("IF_TRUE", "IF_FALSE")]
            if state == "COVERED" and any(e["hits"] == -1 for e in if_edges):
                lines = block["coverageData"]["lines"]
                all_lines_hit = all(l["hits"] > 0 for l in lines)
                has_jumps = any(len(l.get("jumps", [])) > 0 for l in lines)
                tail_line = lines[-1]["line"] if lines else "?"
                tail_branches = lines[-1]["branches"]["total"] if lines else "?"
                bid = block["id"]
                method = mm["fullName"]
                short_method = method.split(".")[-1].split("(")[0] if "." in method else method
                print(f"    Block {bid:>3} ...{short_method}: tail_line={tail_line}, "
                      f"all_lines_hit={all_lines_hit}, has_jumps_in_blockmap={has_jumps}, "
                      f"tail_branches_total={tail_branches}")
    print()

    # -- ROOT CAUSE ANALYSIS: lineToCoverageMap collisions --
    if coverage_data:
        print(sep)
        print("14. ROOT CAUSE: lineToCoverageMap LINE NUMBER COLLISIONS")
        print(sep)
        print()
        print("    pathcov's CoverageReport.buildLineToCoverageMap() uses a flat")
        print("    Map<Integer, LineDTO> keyed only by line number, without class/method")
        print("    scoping. When two methods share the same source line number (common")
        print("    in multi-class projects), the LAST one iterated wins.")
        print()

        line_owners = defaultdict(list)
        for cls in coverage_data.get("classes", []):
            for method in cls.get("methods", []):
                for line in method.get("lines", []):
                    has_jumps = len(line.get("jumps", [])) > 0
                    has_switches = len(line.get("switches", [])) > 0
                    line_owners[line["line"]].append({
                        "method": f'{cls["name"]}.{method["methodSignature"].split("(")[0]}',
                        "has_jumps": has_jumps,
                        "has_switches": has_switches,
                        "branches_total": line["branches"]["total"],
                        "hits": line["hits"],
                    })

        total_lines = len(line_owners)
        collision_lines = sum(1 for owners in line_owners.values() if len(owners) > 1)
        jump_loss_lines = 0
        for owners in line_owners.values():
            if len(owners) > 1:
                has_any_jumps = any(o["has_jumps"] or o["has_switches"] for o in owners)
                has_any_without = any(not o["has_jumps"] and not o["has_switches"] for o in owners)
                if has_any_jumps and has_any_without:
                    jump_loss_lines += 1

        print(f"    Total unique line numbers in coverage data: {total_lines}")
        print(f"    Lines shared by >1 method:                  {collision_lines}  ({collision_lines/total_lines*100:.1f}%)")
        print(f"    Lines where jump/switch data can be lost:   {jump_loss_lines}  ({jump_loss_lines/total_lines*100:.1f}%)")
        print()
        print("    When the winning entry lacks jump data but the losing entry has it,")
        print("    resolveIfEdgeHits() returns -1 for edges that SHOULD have hit counts.")
        print("    This makes JDart unable to determine branch coverage at those nodes.")
        print()

        # Count how many of the 112 IF hits=-1 are explained by this
        explained = 0
        unexplained_blocks = []
        for mm in method_maps:
            for block in mm.get("blocks", []):
                edges = block.get("edges", [])
                for edge in edges:
                    if edge["hits"] == -1 and edge["branchType"] in ("IF_TRUE", "IF_FALSE"):
                        # Find the tail line of this block
                        lines = block["coverageData"]["lines"]
                        if lines:
                            tail_line = lines[-1]["line"]
                            owners = line_owners.get(tail_line, [])
                            if len(owners) > 1:
                                explained += 1
                            else:
                                # Check if line just has no jump data at all
                                if not any(o["has_jumps"] for o in owners):
                                    pass  # Line genuinely has no jumps
                                else:
                                    unexplained_blocks.append(
                                        (block["id"], mm["fullName"], tail_line)
                                    )

        print(f"    IF edges with hits=-1 explained by collision:  {explained} / {if_minus1}")
        print(f"    IF edges with hits=-1 NOT from collision:      {if_minus1 - explained}")
        print()
        if if_minus1 - explained > 0:
            print("    The remaining hits=-1 IF edges come from lines where:")
            print("    - The block was NOT_COVERED (line.hits=0, so no jump data recorded)")
            print("    - The jumpIndex computation failed (block not found in CFG iteration)")
            print("    - The line genuinely has no IntelliJ jump instrumentation")
        print()

    # -- Impact assessment --
    print(sep)
    print("15. IMPACT ON JDART CoverageHeuristicStrategy")
    print(sep)
    print()
    print("    JDart reads this block map to decide which paths to explore (uncovered)")
    print("    and which to skip (already covered). The ignore_covered_paths=true setting")
    print("    marks fully-covered paths as IGNORE.")
    print()
    print(f"    Blocks with ALL edges hits=-1:     {len(blocks_all_edges_minus1)}")
    print(f"      Of those, COVERED:               {coverage_state_of_all_minus1.get('COVERED', 0)}")
    print(f"      Of those, NOT_COVERED:           {coverage_state_of_all_minus1.get('NOT_COVERED', 0)}")
    print(f"      Of those, PARTIALLY_COVERED:     {coverage_state_of_all_minus1.get('PARTIALLY_COVERED', 0)}")
    print()
    print(f"    COVERED blocks with IF hits=-1:    These look COVERED at block level")
    print(f"      but JDart cannot read which branches were taken. If JDart uses")
    print(f"      edge-level hits for heuristic decisions, -1 creates ambiguity.")
    print()
    print(f"    NOT_COVERED blocks with IF hits=-1: {coverage_state_of_all_minus1.get('NOT_COVERED', 0)}")
    print(f"      These blocks were never reached. The -1 is redundant: the block's")
    print(f"      NOT_COVERED state already tells JDart to explore them.")
    print()
    print("    RECOMMENDATION:")
    print("    Fix lineToCoverageMap in pathcov to be scoped per-method (not global).")
    print("    Use a composite key like (className, methodSignature, lineNumber) to avoid")
    print("    cross-method line number collisions. This should eliminate most hits=-1")
    print("    on IF/SWITCH edges for COVERED blocks.")
    print()

    # -- Per-method summary --
    print(sep)
    print("16. PER-METHOD SUMMARY (sorted by % hits=-1)")
    print(sep)
    method_summaries.sort(key=lambda ms: ms["edges_minus1"] / max(ms["edges"], 1), reverse=True)
    for ms in method_summaries:
        if ms["edges"] == 0:
            continue
        short_method = ms["method"].split(".")[-1] if "." in ms["method"] else ms["method"]
        if len(short_method) > 80:
            short_method = short_method[:77] + "..."
        pct = ms["edges_minus1"] / ms["edges"] * 100
        print(f"    {pct:5.1f}%  ({ms['edges_minus1']:>3}/{ms['edges']:>3})  {short_method}")
    print()


if __name__ == "__main__":
    data = load_json(BLOCK_MAP_PATH)
    coverage_data = None
    if COVERAGE_DATA_PATH.exists():
        coverage_data = load_json(COVERAGE_DATA_PATH)
    analyze(data, coverage_data)
