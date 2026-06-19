#!/usr/bin/env python3
"""Analyze the link graph: hubs, orphans, bridges, clusters.

Loads wiki/data/links-graph.json, performs graph analysis,
and writes wiki/data/graph-stats.md.
"""
import json
import os
from collections import defaultdict, deque

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, 'wiki', 'data')
GRAPH_PATH = os.path.join(DATA_DIR, 'links-graph.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'graph-stats.md')

TOP_N = 20

def load_graph():
    with open(GRAPH_PATH, encoding='utf-8') as f:
        return json.load(f)

def find_hubs(nodes):
    ranked = sorted(nodes.items(), key=lambda x: x[1]['degree_in'] + x[1]['degree_out'], reverse=True)
    return ranked[:TOP_N]

def find_orphans(nodes):
    return sorted(
        [name for name, node in nodes.items()
         if node['degree_out'] == 0 and node['degree_in'] == 0]
    )

def find_connected_components(nodes):
    adjacency = {name: set(node['links_out']) for name, node in nodes.items()}
    reverse_adj = defaultdict(set)
    for src, node in nodes.items():
        for target in node['links_out']:
            if target in nodes:
                reverse_adj[target].add(src)

    visited = set()
    components = []

    for name in nodes:
        if name in visited:
            continue
        comp = set()
        queue = deque([name])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            comp.add(current)
            if current in adjacency:
                for nb in adjacency[current]:
                    if nb in nodes and nb not in visited:
                        queue.append(nb)
            if current in reverse_adj:
                for nb in reverse_adj[current]:
                    if nb not in visited:
                        queue.append(nb)
        if comp:
            components.append(comp)

    return components

def label_propagation(nodes, adjacency, max_iter=20):
    labels = {name: i for i, name in enumerate(sorted(nodes.keys()))}
    node_list = sorted(nodes.keys())

    for _ in range(max_iter):
        changed = False
        for node in node_list:
            neighbors = adjacency.get(node, set())
            reverse_neighbors = set()
            for src, out in adjacency.items():
                if node in out:
                    reverse_neighbors.add(src)
            all_neighbors = neighbors | reverse_neighbors

            if not all_neighbors:
                continue

            label_counts = defaultdict(int)
            for nb in all_neighbors:
                if nb in labels:
                    label_counts[labels[nb]] += 1

            if not label_counts:
                continue

            best_label = max(label_counts, key=label_counts.get)
            if labels[node] != best_label:
                labels[node] = best_label
                changed = True

        if not changed:
            break

    return labels

def build_clusters(nodes):
    adjacency = {name: set(node['links_out']) for name, node in nodes.items()}
    lp = label_propagation(nodes, adjacency)

    clusters = defaultdict(list)
    for name, label in lp.items():
        clusters[label].append(name)

    return clusters, lp

def find_bridges(nodes):
    adjacency = {name: set(node['links_out']) for name, node in nodes.items()}
    reverse_adj = defaultdict(set)
    for src, node in nodes.items():
        for target in node['links_out']:
            if target in nodes:
                reverse_adj[target].add(src)

    bridges = []

    for node in sorted(nodes.keys()):
        in_degree = len(reverse_adj.get(node, set()))
        out_degree = len(adjacency.get(node, set()))
        if in_degree > 0 and out_degree > 0:
            neighbors = adjacency.get(node, set()) | reverse_adj.get(node, set())
            tags = nodes[node].get('tags', [])
            neighbor_tags = set()
            for nb in neighbors:
                if nb in nodes:
                    neighbor_tags.update(nodes[nb].get('tags', []))
            tag_overlap = set(tags) & neighbor_tags
            if len(tag_overlap) < len(tags) * 0.3 and len(neighbors) >= 3:
                bridges.append({
                    'name': node,
                    'degree': in_degree + out_degree,
                    'tags': tags,
                    'neighbor_tags': sorted(neighbor_tags),
                    'overlap': sorted(tag_overlap)
                })

    bridges.sort(key=lambda x: x['degree'], reverse=True)
    return bridges[:TOP_N]

def compare_clusters_tags(nodes, clusters):
    tag_sets = {}
    for name, node in nodes.items():
        tag_sets[name] = set(node.get('tags', []))

    report = []
    for label, members in sorted(clusters.items()):
        if len(members) < 3:
            continue
        all_tags = defaultdict(int)
        for m in members:
            for t in tag_sets.get(m, set()):
                all_tags[t] += 1
        top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:5]
        report.append({
            'cluster': label,
            'size': len(members),
            'top_tags': [(t, c) for t, c in top_tags],
            'members': sorted(members)[:10]
        })

    report.sort(key=lambda x: x['size'], reverse=True)
    return report

def write_md(hubs, orphans, components, clusters, cluster_report, bridges):
    non_trivial = [c for c in components if len(c) > 1]
    giant = max(non_trivial, key=len) if non_trivial else set()
    small = [c for c in non_trivial if 2 <= len(c) <= 5]

    lines = [
        '---',
        'description: Статистика графа связей: хабы, сироты, мосты, кластеры, компоненты связности.',
        '---',
        '',
        '# Graph Statistics',
        '',
        '## Компоненты связности',
        f'- Всего компонент: {len(components)}',
        f'- Гигантская компонента: {len(giant)} заметок',
        f'- Мелких компонент (2–5 заметок): {len(small)}',
        f'- Изолированных (размер 1): {len([c for c in components if len(c) == 1])}',
        '',
        f'## Хабы (top-{len(hubs)})',
        '',
        '| # | Заметка | Degree | Out | In | Теги |',
        '|---|---------|--------|-----|----|------|',
    ]
    for idx, (name, node) in enumerate(hubs, 1):
        tags = ', '.join(f'`{t}`' for t in node.get('tags', [])[:3]) or '—'
        lines.append(
            f'| {idx} | [[{name}]] | {node["degree_in"] + node["degree_out"]} | '
            f'{node["degree_out"]} | {node["degree_in"]} | {tags} |'
        )

    lines.append('')
    lines.append('## Сироты (без связей)')
    lines.append(f'Всего: {len(orphans)} заметок')
    lines.append('')
    for name in orphans[:TOP_N]:
        lines.append(f'- [[{name}]]')
    if len(orphans) > TOP_N:
        lines.append(f'- ... и ещё {len(orphans) - TOP_N}')

    lines.append('')
    lines.append('## Мосты (межкластерные заметки)')
    lines.append('')
    for idx, b in enumerate(bridges, 1):
        lines.append(f'### {idx}. [[{b["name"]}]] (degree {b["degree"]})')
        lines.append(f'- Теги: {", ".join(f"`{t}`" for t in b["tags"]) or "—"}')
        lines.append(f'- Теги соседей: {", ".join(f"`{t}`" for t in b["neighbor_tags"][:5])}')
        lines.append(f'- Пересечение: {", ".join(f"`{t}`" for t in b["overlap"]) or "—"}')
        lines.append('')

    lines.append('## Кластеры (label propagation)')
    lines.append(f'Всего кластеров: {len(cluster_report)}')
    lines.append('')
    for cr in cluster_report:
        tag_str = ', '.join(f'`{t}` ({c})' for t, c in cr['top_tags'])
        lines.append(f'### Кластер {cr["cluster"]} (размер: {cr["size"]})')
        lines.append(f'- Топ-теги: {tag_str or "—"}')
        lines.append(f'- Заметки: {", ".join(f"[[{m}]]" for m in cr["members"][:10])}')
        if len(cr['members']) > 10:
            lines.append(f'  ... и ещё {len(cr["members"]) - 10}')
        lines.append('')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'Written analysis to {OUTPUT_PATH}')

def main():
    graph = load_graph()
    nodes = graph['nodes']

    hubs = find_hubs(nodes)
    orphans = find_orphans(nodes)
    components = find_connected_components(nodes)
    clusters, labels = build_clusters(nodes)
    cluster_report = compare_clusters_tags(nodes, clusters)
    bridges = find_bridges(nodes)

    print(f'Hubs: {len(hubs)}, Orphans: {len(orphans)}, Components: {len(components)}')
    print(f'Clusters: {len(set(labels.values()))}, Bridges: {len(bridges)}')

    for name, label in labels.items():
        if name in nodes:
            nodes[name]['cluster'] = label

    cluster_dict = {}
    for label, members in clusters.items():
        cluster_dict[str(label)] = members

    graph['clusters'] = cluster_dict

    with open(GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f'Updated {GRAPH_PATH} with cluster assignments')

    write_md(hubs, orphans, components, clusters, cluster_report, bridges)

if __name__ == '__main__':
    main()
