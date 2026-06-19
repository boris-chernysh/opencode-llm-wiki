import json
import os

#!/usr/bin/env python3
"""Generate link suggestions from the graph using Common Neighbors and Jaccard.

Loads wiki/data/links-graph.json, computes missing link scores,
and writes wiki/data/link-suggestions.md.

Filters out daily-notes noise: excludes pairs where both notes
are from excluded directories or have only excluded tags.
"""



SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, 'wiki', 'data')
GRAPH_PATH = os.path.join(DATA_DIR, 'links-graph.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'link-suggestions.md')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'wiki', 'config.json')

MIN_COMMON = 1
MAX_SUGGESTIONS = 50

EXCLUDED_DIRS = ['daily notes']
EXCLUDED_TAGS = {'daily-note'}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            global EXCLUDED_DIRS, EXCLUDED_TAGS, MAX_SUGGESTIONS
            EXCLUDED_DIRS = cfg.get('exclude', {}).get('dirs_from_suggestions', EXCLUDED_DIRS)
            EXCLUDED_TAGS = set(cfg.get('exclude', {}).get('tags', list(EXCLUDED_TAGS)))
            MAX_SUGGESTIONS = cfg.get('thresholds', {}).get('max_link_suggestions', MAX_SUGGESTIONS)
        except (json.JSONDecodeError, KeyError):
            pass

def is_excluded(fname, nodes):
    node = nodes.get(fname, {})
    source_dir = node.get('source_dir', '')
    if source_dir in EXCLUDED_DIRS:
        return True
    tags = set(node.get('tags', []))
    if tags and tags.issubset(EXCLUDED_TAGS):
        return True
    return False

def load_graph():
    with open(GRAPH_PATH, encoding='utf-8') as f:
        return json.load(f)

def jaccard(neighbors_a, neighbors_b):
    union = neighbors_a | neighbors_b
    if not union:
        return 0.0
    return len(neighbors_a & neighbors_b) / len(union)

def suggest(graph):
    nodes = graph['nodes']
    adjacency = {name: set(node['links_out']) for name, node in nodes.items()}

    suggestions = []
    node_names = sorted(adjacency.keys())

    for i, a in enumerate(node_names):
        if is_excluded(a, nodes):
            continue
        neighbors_a = adjacency[a]
        for j in range(i + 1, len(node_names)):
            b = node_names[j]
            if is_excluded(b, nodes):
                continue

            if b in neighbors_a:
                continue

            neighbors_b = adjacency[b]
            common = neighbors_a & neighbors_b
            if len(common) < MIN_COMMON:
                continue

            jac = jaccard(neighbors_a, neighbors_b)
            tags_a = set(nodes[a].get('tags', []))
            tags_b = set(nodes[b].get('tags', []))
            shared_tags = tags_a & tags_b

            if jac == 0.0 and not shared_tags:
                continue

            suggestions.append({
                'a': a,
                'b': b,
                'common': len(common),
                'jaccard': round(jac, 4),
                'shared_neighbors': sorted(common)[:5],
                'shared_tags': sorted(shared_tags),
                'tags_a': sorted(tags_a),
                'tags_b': sorted(tags_b)
            })

    suggestions.sort(key=lambda x: (x['common'], x['jaccard']), reverse=True)
    return suggestions[:MAX_SUGGESTIONS]

def write_md(suggestions, stats):
    lines = [
        '---',
        'description: Топ предложений по связям на основе графового анализа (Common Neighbours + Jaccard).',
        '---',
        '',
        '# Link Suggestions (Graph)',
        '',
        f'Всего заметок: {stats["total_nodes"]}, рёбер: {stats["total_edges"]}',
        f'Найдено предложений: {len(suggestions)}',
        '',
        '| # | Заметка A | Заметка B | Common | Jaccard | Общие теги |',
        '|---|-----------|-----------|--------|---------|------------|',
    ]

    for idx, s in enumerate(suggestions, 1):
        shared = ', '.join(f'`{t}`' for t in s['shared_tags']) or '—'
        lines.append(
            f'| {idx} | [[{s["a"]}]] | [[{s["b"]}]] | '
            f'{s["common"]} | {s["jaccard"]} | {shared} |'
        )

    lines.append('')
    lines.append('## Детали')
    lines.append('')
    for idx, s in enumerate(suggestions, 1):
        lines.append(f'### {idx}. [[{s["a"]}]] ↔ [[{s["b"]}]]')
        lines.append(f'- Common neighbours ({s["common"]}): {", ".join(f"[[{n}]]" for n in s["shared_neighbors"])}')
        lines.append(f'- Jaccard: {s["jaccard"]}')
        lines.append(f'- Tags A: {", ".join(f"`{t}`" for t in s["tags_a"]) or "—"}')
        lines.append(f'- Tags B: {", ".join(f"`{t}`" for t in s["tags_b"]) or "—"}')
        lines.append('')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'Written {len(suggestions)} suggestions to {OUTPUT_PATH}')

def main():
    load_config()
    graph = load_graph()
    suggestions = suggest(graph)
    write_md(suggestions, graph['stats'])

if __name__ == '__main__':
    main()
