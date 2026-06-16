#!/usr/bin/env python3
"""TF-IDF semantic link suggestions.

Reads note content, builds TF-IDF vectors (pure Python),
computes cosine similarity within graph clusters,
and finds notes that are semantically similar but not linked.
Writes agent/data/semantic-suggestions.md.

Filters out daily-notes noise: excludes pairs where both notes
are from excluded directories or have only excluded tags.
"""
import json
import math
import os
import re

from collections import Counter






SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, 'agent', 'data')
GRAPH_PATH = os.path.join(DATA_DIR, 'links-graph.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'semantic-suggestions.md')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'agent', 'config.json')

MAX_SUGGESTIONS = 50
MIN_SIMILARITY = 0.20
MAX_NOTES = 1500
MIN_CONTENT_TOKENS = 50

EXCLUDED_DIRS = ['daily notes']
EXCLUDED_TAGS = {'daily-note'}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            global EXCLUDED_DIRS, EXCLUDED_TAGS, MAX_SUGGESTIONS, MIN_SIMILARITY, MIN_CONTENT_TOKENS
            EXCLUDED_DIRS = cfg.get('exclude', {}).get('dirs_from_suggestions', EXCLUDED_DIRS)
            EXCLUDED_TAGS = set(cfg.get('exclude', {}).get('tags', list(EXCLUDED_TAGS)))
            MAX_SUGGESTIONS = cfg.get('thresholds', {}).get('max_link_suggestions', MAX_SUGGESTIONS)
            MIN_SIMILARITY = cfg.get('thresholds', {}).get('min_tfidf_similarity', MIN_SIMILARITY)
            MIN_CONTENT_TOKENS = cfg.get('thresholds', {}).get('min_content_tokens', MIN_CONTENT_TOKENS)
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

RUSSIAN_STOP_WORDS = {
    'и', 'в', 'не', 'на', 'я', 'что', 'с', 'как', 'а', 'то', 'все', 'она', 'так',
    'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее',
    'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь',
    'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть',
    'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там',
    'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
    'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб',
    'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда',
    'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь',
    'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были',
    'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два',
    'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти',
    'нас', 'про', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя',
    'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя',
    'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между',
    'которые', 'который', 'которая', 'которое', 'которые', 'которых',
    'которым', 'которыми', 'это', 'ещё', 'очень', 'также', 'свои', 'нету',
    'например', 'свой', 'также', 'того', 'каждый', 'любой', 'впрочем',
    'достаточно', 'вообще', 'однако', 'поэтому',
}

def tokenize(text):
    text = text.lower()
    words = re.findall(r'[а-яёa-z0-9]{2,}', text)
    return [w for w in words if w not in RUSSIAN_STOP_WORDS]

def build_tfidf(docs, doc_ids):
    n_docs = len(docs)
    df = Counter()
    for words in docs:
        df.update(set(words))

    vectors = {}
    for i, (doc_id, words) in enumerate(zip(doc_ids, docs)):
        if not words:
            continue
        tf = Counter(words)
        vec = {}
        total = len(words)
        for word, freq in tf.items():
            idf = math.log(n_docs / (df[word] + 1))
            vec[word] = (freq / total) * idf

        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            vec = {w: v / norm for w, v in vec.items()}

        vectors[doc_id] = vec

    return vectors

def cosine_sim(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(vec_a.get(w, 0) * vec_b.get(w, 0) for w in set(vec_a) | set(vec_b))
    return dot

def suggest(graph):
    nodes = graph['nodes']
    adjacency = {name: set(node['links_out']) for name, node in nodes.items()}

    fname_to_path = {fname: node.get('path', '') for fname, node in nodes.items()}

    doc_ids = []
    docs = []
    for fname in sorted(nodes.keys())[:MAX_NOTES]:
        if is_excluded(fname, nodes):
            continue
        path = fname_to_path.get(fname, '')
        full_path = os.path.join(PROJECT_ROOT, path)
        if not os.path.isfile(full_path):
            continue
        try:
            with open(full_path, encoding='utf-8') as f:
                content = f.read()
            parts = content.split('---', 2)
            body = parts[2] if len(parts) >= 3 else content
            body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
            body = re.sub(r'\[\[.*?\]\]', '', body)
            words = tokenize(body)
            if len(words) >= MIN_CONTENT_TOKENS:
                doc_ids.append(fname)
                docs.append(words)
        except Exception:
            continue

    print(f'Tokenized {len(doc_ids)} docs for TF-IDF')

    vectors = build_tfidf(docs, doc_ids)
    print(f'Built vectors for {len(vectors)} docs')

    suggestions = []
    doc_list = sorted(vectors.keys())

    for i, a in enumerate(doc_list):
        for j in range(i + 1, len(doc_list)):
            b = doc_list[j]

            linked_a = b in adjacency.get(a, set())
            linked_b = a in adjacency.get(b, set())
            if linked_a or linked_b:
                continue

            sim = cosine_sim(vectors[a], vectors[b])
            if sim < MIN_SIMILARITY:
                continue

            suggestions.append({
                'a': a,
                'b': b,
                'similarity': round(sim, 4),
                'tags_a': nodes.get(a, {}).get('tags', []),
                'tags_b': nodes.get(b, {}).get('tags', [])
            })

    suggestions.sort(key=lambda x: x['similarity'], reverse=True)
    return suggestions[:MAX_SUGGESTIONS]

def write_md(suggestions):
    lines = [
        '---',
        'description: Топ семантических предложений по связям на основе TF-IDF косинусного сходства.',
        '---',
        '',
        '# Semantic Link Suggestions (TF-IDF)',
        '',
        f'Найдено предложений: {len(suggestions)} (min similarity: {MIN_SIMILARITY})',
        '',
        '| # | Заметка A | Заметка B | Similarity | Общие теги |',
        '|---|-----------|-----------|------------|------------|',
    ]

    for idx, s in enumerate(suggestions, 1):
        shared = set(s['tags_a']) & set(s['tags_b'])
        shared_str = ', '.join(f'`{t}`' for t in sorted(shared)) or '—'
        lines.append(
            f'| {idx} | [[{s["a"]}]] | [[{s["b"]}]] | '
            f'{s["similarity"]} | {shared_str} |'
        )

    lines.append('')
    lines.append('## Детали')
    lines.append('')
    for idx, s in enumerate(suggestions, 1):
        lines.append(f'### {idx}. [[{s["a"]}]] ↔ [[{s["b"]}]]')
        lines.append(f'- Similarity: {s["similarity"]}')
        lines.append(f'- Tags A: {", ".join(f"`{t}`" for t in s["tags_a"]) or "—"}')
        lines.append(f'- Tags B: {", ".join(f"`{t}`" for t in s["tags_b"]) or "—"}')
        lines.append('')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'Written {len(suggestions)} suggestions to {OUTPUT_PATH}')

def main():
    load_config()
    graph = load_graph_local()
    suggestions = suggest(graph)
    write_md(suggestions)

def load_graph_local():
    with open(GRAPH_PATH, encoding='utf-8') as f:
        return json.load(f)

if __name__ == '__main__':
    main()
