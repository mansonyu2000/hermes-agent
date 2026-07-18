"""
MIM 功能清单查询工具
用法:
  python query_features.py                          # 全部
  python query_features.py --status todo            # 待做的
  python query_features.py --module 群聊             # 群聊模块
  python query_features.py --decision V1             # V1 优先级的
  python query_features.py --search 安全             # 搜索关键词
  python query_features.py --summary                 # 统计摘要
"""
import json, argparse

import os
with open(os.path.join(os.path.dirname(__file__), 'feature-inventory.json'), encoding='utf-8') as f:
    data = json.load(f)

parser = argparse.ArgumentParser(description='Query MIM Features')
parser.add_argument('--status', help='Filter: done/todo')
parser.add_argument('--module', help='Filter: 身份与登录/联系人/...')
parser.add_argument('--decision', help='Filter: V1/V1.5/V2/已完成')
parser.add_argument('--search', help='Search in feature name and sub details')
parser.add_argument('--summary', action='store_true', help='Print summary only')
args = parser.parse_args()

# Filter
results = data
if args.status:
    results = [f for f in results if f['status'] == args.status]
if args.module:
    results = [f for f in results if args.module in f['module']]
if args.decision:
    results = [f for f in results if args.decision in str(f['decision'])]
if args.search:
    results = [f for f in results if args.search.lower() in f['feature'].lower() 
               or args.search.lower() in (f.get('sub') or '').lower()]

if args.summary:
    done = sum(1 for f in data if f['status'] == 'done')
    todo = sum(1 for f in data if f['status'] == 'todo')
    print(f"Total: {len(data)} | Done: {done} | Todo: {todo}")
    for m in sorted(set(f['module'] for f in data)):
        c = sum(1 for f in data if f['module'] == m)
        d = sum(1 for f in data if f['module'] == m and f['status'] == 'done')
        print(f"  {m}: {c} ({d} done)")
else:
    for f in results:
        print(f"{f['id']} [{f['status'].upper():4}] {f['module']}/{f['feature']}")
        if f.get('deps'):
            print(f"       deps: {f['deps']}")
        print(f"       decision: {f.get('decision','')}")
        print()
    print(f"\n--- {len(results)} results ---")
