"""Reproducible domain documentation, not a text parser or a build hook.

The design renderer is reused from the approved review2 handoff. Runtime
capabilities are added from the output schema and checked consumer manifest.
"""
import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

def jtext(value: Any) -> str:
    # Mapping keys can be canonical; semantic lists MUST preserve their order.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def component_edges(nodes: list[dict]) -> list[dict]:
    """Pure reading projection from stored order; no globally stored child index."""
    return [{'parent_id': node['id'], 'child_id': child_id,
             'relation': 'has_part', 'layer': 'term_composition', 'component_index': index}
            for node in nodes for index, child_id in enumerate(node['child_ids'])]


def cell(value: Any) -> str:
    result = value if isinstance(value, str) else jtext(value)
    return result.replace('|', '\\|').replace('\n', '<br>')


def table(headers: list[str], rows) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    lines.extend('| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows)
    return '\n'.join(lines) + '\n'


def block(value: Any) -> str:
    return '```json\n' + json.dumps(value, ensure_ascii=False, indent=2) + '\n```\n'


def _render_design_documents(registry: dict, schema: dict, suite: dict) -> dict[str, str]:
    """Review2's pure renderer; source definitions and ordered projections reused."""
    header = ('由kernel.registry.json、kernel.schema.json及paper-probes.json确定性生成。'
              '这是设计说明；运行时能力状态以Codex实施后的consumer manifest和效应测试为准。\n')
    ref = ['# Schema Reference — ' + registry['schema_version'], header,
           '## 1. 候选状态与关系投影',
           '构词的直接子项读取child_ids，语义参数读取expression.arguments；两个结构都保留。'
           '支持、约束、授权三轴分别显示；OSCA只表示处理活动。', block(registry['projection_contracts']),
           '### 共享状态字段', block(schema['$defs']['StatusAxes']),
           '## 2. 类型字段']
    for name, definition in schema['$defs'].items():
        ref += ['### ' + name]
        if definition.get('description'): ref.append(definition['description'])
        if definition.get('properties'):
            rows = []
            for field, value in definition['properties'].items():
                kind = value.get('$ref', value.get('type', 'enum' if 'enum' in value else 'composite'))
                constraints = {k: v for k, v in value.items() if k in
                               ('enum', 'const', 'minimum', 'maximum', 'minItems', 'maxItems', 'uniqueItems', 'description')}
                rows.append([field, 'required' if field in definition.get('required', []) else 'optional', kind, constraints])
            ref.append(table(['字段', '必需', '类型／引用', '限定'], rows))
        else:
            ref.append(block(definition))
        if 'allOf' in definition:
            ref += ['条件约束：', block(definition['allOf'])]
        if 'additionalProperties' in definition:
            ref.append('additionalProperties = ' + jtext(definition['additionalProperties']))
    ref += ['## 3. 概念层级', table(['ID', '名称', 'family', 'parents', '定义状态', '来源', '说明'],
        [[c['id'], c['label_zh'], c['family'], c['parent_ids'], c['definition_status'], c['evidence_ids'], c.get('note', '')]
         for c in registry['concepts']])]
    ref += ['## 4. 词形线索', table(['ID', 'form', 'sense_concept_ids', '完整记录'],
        [[c['id'], c['form'], c['sense_concept_ids'], c] for c in registry['lexical_cues']])]
    ref += ['## 5. 语义构造器', table(['ID', '说明', '参数sort', 'result_sort', '关系提示'],
        [[c['id'],c['label_zh'],c['arguments'],c['result_sort'],c['relation_kind']] for c in registry['constructors']]),
        'relation_kind是受分层约束的投影提示，不将expression.arguments冒充构词顺序；'
        '所有构词父子边仍由child_ids产生。']
    ref += ['## 6. 组合规则']
    for rule in registry['composition_rules']:
        ref += ['### ' + rule['id'] + ' — ' + rule['label_zh'], block(rule)]
    ref += ['## 7. 固定技术表达候选', block(registry['fixed_expressions']),
            '## 8. Scoped facts（K1运行视图不消费）', block(registry['scoped_facts']),
            '## 9. 人工动作', table(['ID','阶段','作用','当前状态','校验','恢复'],
             [[r['id'],r['stage'],r['effect'],r['current_status'],r['validation'],r['resume_from']]
              for r in registry['human_actions']]),
            '## 10. 关系词汇', table(['关系', '层', '中文显示', '英文显示', '含义', '限制'],
             [[r['id'],r['layer'],r['label_zh'],r['label_en'],r['meaning'],r['not_equivalent_to']]
              for r in registry['relations']]),
            '## 11. 来源记录（本轮保留原核查身份，不新增历史证明）', block(registry['sources'])]
    paper = ['# Paper Probes — ' + suite['schema_version'],
             '六组已公开开发预期，authored_expected_nodes由人工编写，engine_observed_result全部为null。'
             '本次工具只验证已给结构及参考算术；本文件不代表新引擎运行结果。',
             '## 阅读约定', '节点表child_ids保持直接成分原文顺序；候选树、语义表达、状态三轴分别保存。'
             '操作预期、人工后续和执行预期不能混为K1验收。']
    for probe in suite['probes']:
        paper += ['## ' + probe['id'] + ' — ' + probe['title'],
                  'source_class: ' + probe['source_class'], '### 原文与reading', block(probe['documents']),
                  '### 禁用整词捷径', block(probe['forbidden_whole_term_shortcuts']),
                  '### 有序候选树（人工预期）', table(['ID','跨度','method / rule / cue','直接child_ids','表达','支持／约束／授权'],
                    [[n['id'], n['span'], [n['method'], n['rule_id'], n['cue_id']], n['child_ids'], n['expression'],
                      [n['support_status'], n['constraint_status'], n['authorization_status']]]
                     for n in probe['authored_expected_nodes']]),
                  '边序号是父项局部派生值：', block(component_edges(probe['authored_expected_nodes'])),
                  '### 预期与边界', block(probe['expectations']),
                  '### 后续人工步骤（K1不提交为真实决定）', block(probe['human_steps']),
                  '### 负例', block(probe['negative_controls']),
                  '### 参考算术', block(probe['numeric_reference']),
                  str(probe['execution_scope_note']),
                  'engine_observed_result: ' + jtext(probe['engine_observed_result'])]
    contract = ['# Semantic Consumption Contract — ' + registry['schema_version'], header,
                '## 权限与处理活动', block(registry['phases']), registry['phase_note'],
                '## 各类证据的允许效果与必需前提', table(['ID','证据来源','允许','禁止','requires_all','grant_scope','状态'],
                 [[a['id'],a['knowledge_source'],a['allow_effects'],a['deny_effects'],a['requires_all'],
                   a['grant_scope'],a['implementation_status']] for a in registry['authority_rules']]),
                '## Applicability predicates', table(['ID','含义','缺失','冲突','实施状态'],
                 [[a['id'],a['meaning'],a['missing_result'],a['conflict_result'],a['implementation_status']]
                  for a in registry['predicate_contracts']]),
                '## 人工动作与恢复', table(['动作','阶段','效果','现有状态','校验','恢复'],
                 [[a['id'],a['stage'],a['effect'],a['current_status'],a['validation'],a['resume_from']]
                  for a in registry['human_actions']]),
                '## 投影强制契约', block(registry['projection_contracts']),
                '## 外部效果验收', block(registry['required_external_checks']),
                '本次validate_data只检查资料契约，consumer_effect、实际scope gate、stale replay及执行闭包需由后续产品测试验证。'
                'UI标签没有授权权限，provenance边不能代替输入绑定，顺序字段不能按ID或集合方式重排。']
    return {name: '\n\n'.join(parts).rstrip() + '\n' for name, parts in (
        ('SCHEMA_REFERENCE.md', ref), ('PAPER_PROBES.md', paper), ('CONSUMPTION_CONTRACT.md', contract))}


def _load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _symbol_exists(reference):
    try:
        filename, symbol = reference.split('::')
        path = (ROOT/filename).resolve()
        if not path.is_relative_to(ROOT) or path.suffix != '.py':
            return False
        body = ast.parse(path.read_text(encoding='utf-8')).body
        for part in symbol.split('.'):
            node = next((n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == part), None)
            if node is None:
                return False
            body = node.body
        return True
    except (OSError, ValueError, SyntaxError):
        return False


def validate_manifest(manifest):
    """Require concrete producers/consumers and named effect tests for delivery.

    Symbol existence is not test execution. The named tests still run in the
    development suite; this check prevents documentation claiming absent code.
    """
    if manifest.get('schema') != 'DomainKernelConsumers/1':
        raise ValueError('consumer_manifest_schema')
    ids = set()
    required = {'id', 'producer', 'validator', 'consumer', 'allowed_effect', 'effect_test', 'status'}
    for row in manifest['capabilities']:
        if set(row) != required or row['id'] in ids:
            raise ValueError('consumer_manifest_fields_or_duplicate')
        ids.add(row['id'])
        if row['status'] not in ('suggestion_only', 'implemented', 'metadata_only', 'planned'):
            raise ValueError('consumer_manifest_status')
        for field in ('producer', 'validator', 'consumer', 'effect_test'):
            if row['status'] in ('suggestion_only', 'implemented') and not row[field]:
                raise ValueError('missing_consumer_or_effect_test:' + row['id'])
            for reference in row[field]:
                if not _symbol_exists(reference):
                    raise ValueError('consumer_symbol_missing:' + reference)
                if field == 'effect_test' and not reference.rsplit('.', 1)[-1].startswith('test_'):
                    raise ValueError('effect_test_not_test:' + reference)


def render_documents(*, registry=None, schema=None, probes=None, output_schema=None, manifest=None):
    """Pure generation from definitions, shared schema and consumer evidence."""
    registry = _load(HERE/'kernel.registry.json') if registry is None else registry
    schema = _load(HERE/'kernel.schema.json') if schema is None else schema
    probes = _load(ROOT/'tests/fixtures/domain_kernel/paper-probes.json') if probes is None else probes
    output_schema = _load(HERE/'output.schema.json') if output_schema is None else output_schema
    manifest = _load(HERE/'consumer-manifest.json') if manifest is None else manifest
    validate_manifest(manifest)
    rendered = _render_design_documents(registry, schema, probes)
    intro = ('> K1 已实现可选 suggestion-only 候选；下面的 review2 定义仍保留原设计身份。'
             '人工裁决、统一授权、计数坐标、reading 选择与恢复尚未接入。'
             '既有 parser 硬编码未在本阶段清理。\n\n')
    consumers = table(['能力', '状态', 'producer', 'validator', 'consumer', '允许效果', '效应测试'],
        [[r['id'], r['status'], r['producer'], r['validator'], r['consumer'], r['allowed_effect'], r['effect_test']]
         for r in manifest['capabilities']])
    reference = (intro + rendered['SCHEMA_REFERENCE.md'] + '\n## K1 运行产物封装\n\n' + block(output_schema)
                 + '\n## 实际消费者与能力状态\n\n' + consumers
                 + '\n符号存在校验不等于效应测试执行；实际测试结果见 INTEGRATION.md。'
                 '后端候选选项默认关闭；固定 Inspector 在 R2 后开启只读候选展示。'
                 '未接网站 build/CI，未实现 kernel/code 失效 watcher。\n')
    return {'SCHEMA_REFERENCE.md': reference, 'PAPER_PROBES.md': rendered['PAPER_PROBES.md']}


def check_documents(directory=None):
    directory = ROOT/'docs/domain-kernel' if directory is None else Path(directory)
    for name, content in render_documents().items():
        path = directory/name
        if not path.is_file() or path.read_text(encoding='utf-8') != content:
            raise ValueError('generated_doc_stale:' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check generated docs without writing.')
    args = parser.parse_args()
    try:
        if args.check:
            check_documents()
        else:
            directory = ROOT/'docs/domain-kernel'
            directory.mkdir(parents=True, exist_ok=True)
            for name, content in render_documents().items():
                (directory/name).write_text(content, encoding='utf-8', newline='\n')
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print('Domain docs: ' + ('current (read-only check)' if args.check else 'generated'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
