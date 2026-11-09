"""Graphviz DOT generator and pure SVG renderer for dependency graphs."""

import os
import shutil
import subprocess
from typing import Dict, List, Set, Tuple

ZERO_VAL = 0
ONE_VAL = 1
TWO_VAL = 2
SVG_PADDING = 40
NODE_WIDTH = 150
NODE_HEIGHT = 40
RANK_GAP = 200
ROW_GAP = 65
CORNER_RADIUS = 8
STROKE_WIDTH = 2
FONT_SIZE = 13


def generate_graphviz_dot(
    root: str,
    graph: Dict[str, List[str]],
) -> str:
    """Generate Graphviz DOT formatted text for directed dependency graph."""
    lines = [
        f'digraph "{root}" {{',
        '  rankdir=LR;',
        '  node [shape=box, style="rounded,filled", fillcolor="#EBF3FB", '
        'color="#1A73E8", fontname="Helvetica"];',
        '  edge [color="#1A73E8", arrowhead=vee];',
    ]
    all_nodes = set(graph.keys())
    for deps in graph.values():
        all_nodes.update(deps)

    for node in sorted(all_nodes):
        lines.append(f'  "{node}";')

    for src, targets in graph.items():
        for dst in targets:
            lines.append(f'  "{src}" -> "{dst}";')

    lines.append("}")
    return "\n".join(lines)


def _compute_ranks(
    root: str,
    graph: Dict[str, List[str]],
) -> Dict[str, int]:
    """Assign horizontal rank level to each node using BFS distances."""
    ranks: Dict[str, int] = {root: ZERO_VAL}
    queue = [root]
    while len(queue) > ZERO_VAL:
        curr = queue.pop(ZERO_VAL)
        curr_rank = ranks[curr]
        for neighbor in graph.get(curr, []):
            if neighbor not in ranks:
                ranks[neighbor] = curr_rank + ONE_VAL
                queue.append(neighbor)
    return ranks


def _layout_nodes(
    ranks: Dict[str, int],
) -> Tuple[Dict[str, Tuple[int, int]], int, int]:
    """Compute (x, y) coordinates for all nodes organized by rank."""
    columns: Dict[int, List[str]] = {}
    for node, rank in ranks.items():
        columns.setdefault(rank, []).append(node)

    positions: Dict[str, Tuple[int, int]] = {}
    max_x = SVG_PADDING
    max_y = SVG_PADDING

    for rank in sorted(columns.keys()):
        nodes_in_col = sorted(columns[rank])
        col_x = SVG_PADDING + rank * RANK_GAP
        for row_idx, node in enumerate(nodes_in_col):
            node_y = SVG_PADDING + row_idx * ROW_GAP
            positions[node] = (col_x, node_y)
            if col_x + NODE_WIDTH + SVG_PADDING > max_x:
                max_x = col_x + NODE_WIDTH + SVG_PADDING
            if node_y + NODE_HEIGHT + SVG_PADDING > max_y:
                max_y = node_y + NODE_HEIGHT + SVG_PADDING

    return positions, max_x, max_y


def _render_svg_edge(
    sx: int,
    sy: int,
    dx: int,
    dy: int,
) -> str:
    """Render single curved directed edge with arrowhead in SVG."""
    start_x = sx + NODE_WIDTH
    start_y = sy + NODE_HEIGHT // TWO_VAL
    end_x = dx
    end_y = dy + NODE_HEIGHT // TWO_VAL
    ctrl_offset = (end_x - start_x) // TWO_VAL
    c1_x = start_x + ctrl_offset
    c2_x = end_x - ctrl_offset
    return (
        f'  <path d="M {start_x} {start_y} C {c1_x} {start_y}, '
        f'{c2_x} {end_y}, {end_x} {end_y}" stroke="#1A73E8" '
        f'stroke-width="{STROKE_WIDTH}" fill="none" '
        f'marker-end="url(#arrow)"/>'
    )


def _render_svg_node(node: str, nx: int, ny: int) -> str:
    """Render single rounded node box and label in SVG."""
    tx = nx + NODE_WIDTH // TWO_VAL
    ty = ny + NODE_HEIGHT // TWO_VAL
    rect = (
        f'  <rect x="{nx}" y="{ny}" width="{NODE_WIDTH}" '
        f'height="{NODE_HEIGHT}" rx="{CORNER_RADIUS}" fill="#EBF3FB" '
        f'stroke="#1A73E8" stroke-width="{STROKE_WIDTH}"/>'
    )
    text = (
        f'  <text x="{tx}" y="{ty}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="Helvetica, Arial, sans-serif" '
        f'font-size="{FONT_SIZE}" fill="#202124">{node}</text>'
    )
    return f"{rect}\n{text}"


def _build_svg_xml(
    graph: Dict[str, List[str]],
    pos: Dict[str, Tuple[int, int]],
    width: int,
    height: int,
) -> str:
    """Build complete SVG XML markup from node positions and edges."""
    xml_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        '  <defs>',
        '    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1A73E8"/>',
        '    </marker>',
        '  </defs>',
    ]
    for src, targets in graph.items():
        if src in pos:
            sx, sy = pos[src]
            for dst in targets:
                if dst in pos:
                    dx, dy = pos[dst]
                    xml_parts.append(_render_svg_edge(sx, sy, dx, dy))

    for node, (nx, ny) in pos.items():
        xml_parts.append(_render_svg_node(node, nx, ny))

    xml_parts.append("</svg>")
    return "\n".join(xml_parts)


def render_svg_native(
    root: str,
    graph: Dict[str, List[str]],
) -> str:
    """Render directed dependency graph directly to SVG XML string."""
    ranks = _compute_ranks(root, graph)
    all_nodes = set(graph.keys())
    for targets in graph.values():
        all_nodes.update(targets)
    for node in all_nodes:
        if node not in ranks:
            ranks[node] = ONE_VAL

    positions, width, height = _layout_nodes(ranks)
    return _build_svg_xml(graph, positions, width, height)


def export_graph_visualization(
    root: str,
    graph: Dict[str, List[str]],
    output_svg_path: str,
) -> Tuple[str, str]:
    """Generate Graphviz DOT and export graph image to SVG file."""
    dot_content = generate_graphviz_dot(root, graph)
    dot_file_path = output_svg_path[:-4] + ".dot"
    with open(dot_file_path, "w", encoding="utf-8") as file:
        file.write(dot_content)

    dot_bin = shutil.which("dot")
    if dot_bin:
        try:
            subprocess.run(
                [dot_bin, "-Tsvg", dot_file_path, "-o", output_svg_path],
                check=True,
                capture_output=True,
            )
            return dot_file_path, output_svg_path
        except Exception:
            pass

    svg_content = render_svg_native(root, graph)
    with open(output_svg_path, "w", encoding="utf-8") as file:
        file.write(svg_content)
    return dot_file_path, output_svg_path
