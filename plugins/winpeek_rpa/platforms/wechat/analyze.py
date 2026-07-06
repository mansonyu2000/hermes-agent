"""
wechat_analyze.py �?微信消息 AI 分析引擎

功能: 清洗去重 �?关键词提�?�?主题提取 �?标签建议 �?文件分析

用法:
  python wechat_analyze.py --friend "于杨�? --topics    # 主题提取
  python wechat_analyze.py --friend "于杨�? --keywords  # 关键词提�?
  python wechat_analyze.py --friend "于杨�? --all       # 全部分析
"""
import sys, os, json, re, argparse
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# (removed - now using package imports)
from .db import WeChatDB

# 尝试导入分词�?
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

# LLM 客户端（支持 Ollama �?DeepSeek�?
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ══════════════════════════════════════════════════════�?
# 消息清洗
# ══════════════════════════════════════════════════════�?

def clean_messages(db, friend_id):
    """读取并清洗消息：去日期分隔符、去系统消息、去�?""
    all_msgs = db.list_messages(friend_id=friend_id, limit=5000)

    cleaned = []
    seen = set()
    for m in all_msgs:
        if m.get("is_date_sep"):
            continue
        content = (m.get("content") or "").strip()
        if not content:
            continue
        # 去系统消�?
        if content in ("图片", "[文件]", "[视频]", "[语音]"):
            m["msg_type"] = {"图片":"image","[文件]":"file","[视频]":"video","[语音]":"voice"}.get(content, "system")
            if m["msg_type"] != "system":
                cleaned.append(m)
            continue
        # 去重
        key = content[:60]
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(m)

    return cleaned


# ══════════════════════════════════════════════════════�?
# 关键词提�?(jieba)
# ══════════════════════════════════════════════════════�?

def extract_keywords(messages, top_n=20):
    """jieba 分词 �?词频 �?Top N 关键�?""
    if not HAS_JIEBA:
        return {"error": "需要安�?jieba: pip install jieba"}

    all_text = " ".join(m.get("content", "") for m in messages if m.get("content"))
    words = jieba.cut(all_text)

    # 过滤停用�?
    stopwords = {"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"一",
                 "一�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"着","没有",
                 "�?,"�?,"自己","�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?,"�?}
    filtered = [w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in stopwords]

    counter = Counter(filtered)
    return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]


# ══════════════════════════════════════════════════════�?
# 主题提取 (LLM)
# ══════════════════════════════════════════════════════�?

def extract_topics_llm(messages, max_samples=20):
    """取最�?N 条消息发�?LLM 提取主题"""
    if not HAS_REQUESTS:
        return {"error": "需要安�?requests: pip install requests"}

    # 取样本消�?
    samples = messages[-max_samples:] if len(messages) > max_samples else messages
    text_samples = "\n".join(
        f"- {m.get('sender_name','?')}: {m.get('content','')[:100]}"
        for m in samples if m.get("content"))

    prompt = f"""分析以下微信对话，提�?-5个讨论主题。每个主题一行，格式: 主题�? 简要描述�?

对话内容:
{text_samples}

主题:"""

    try:
        # 优先�?DeepSeek (通过本地 Ollama)
        resp = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
            timeout=30)
        if resp.status_code == 200:
            topics_text = resp.json().get("response", "")
            topics = [t.strip() for t in topics_text.split("\n") if t.strip()]
            return {"topics": topics, "samples": len(samples)}
    except Exception:
        pass

    return {"error": "LLM 不可�?, "samples": len(samples)}


def extract_topics_simple(messages):
    """�?LLM 的简单主题提取：基于关键词聚�?""
    kw = extract_keywords(messages, top_n=10)
    if isinstance(kw, dict) and "error" in kw:
        return kw
    # 简单聚类：把关键词按语义分�?
    topics = [f"高频�? {', '.join(item['word'] for item in kw[:5])}"]
    return {"topics": topics, "keywords": kw}


# ══════════════════════════════════════════════════════�?
# 统计分析
# ══════════════════════════════════════════════════════�?

def message_stats(messages):
    """消息统计分析"""
    total = len(messages)
    if total == 0:
        return {"total": 0}

    from_me = sum(1 for m in messages if m.get("is_from_me"))
    from_other = total - from_me

    type_counts = Counter(m.get("msg_type", "text") for m in messages)

    # 消息时间分布（按天）
    days = Counter()
    for m in messages:
        mt = m.get("msg_time", "")
        if "�? in mt and "�? in mt:
            days[mt[:8]] += 1

    return {
        "total": total,
        "from_me": from_me,
        "from_other": from_other,
        "type_distribution": dict(type_counts),
        "daily_distribution": dict(days.most_common(10)),
        "avg_msg_length": sum(len(m.get("content","") or "") for m in messages) // max(total, 1),
    }


# ══════════════════════════════════════════════════════�?
# 主分析流�?
# ══════════════════════════════════════════════════════�?

def analyze(db, friend_name, do_topics=False, do_keywords=False, do_all=False):
    friend = db.get_friend(friend_name)
    if not friend:
        print(f"�?联系�?'{friend_name}' 不存�?)
        return

    fid = friend["id"]
    print(f"分析对象: {friend.get('nickname','')[:30]} (id={fid})")
    print(f"微信�? {friend.get('wxid','?')}  地区: {friend.get('region','?')}")

    # 清洗消息
    msgs = clean_messages(db, fid)
    print(f"\n消息: 原始→清洗后 {len(msgs)} �?)

    # 统计
    stats = message_stats(msgs)
    print(f"\n=== 统计 ===")
    print(f"  总消�? {stats['total']}")
    print(f"  我发�? {stats['from_me']}  对方发的: {stats['from_other']}")
    print(f"  类型分布: {stats['type_distribution']}")
    print(f"  日均消息长度: {stats['avg_msg_length']} �?)

    # 关键�?
    if do_keywords or do_all:
        print(f"\n=== 关键�?===")
        kw = extract_keywords(msgs, top_n=15)
        if isinstance(kw, list):
            for item in kw:
                bar = "�? * min(item["count"], 20)
                print(f"  {item['word']:<10} {item['count']:>3} {bar}")

    # 主题
    if do_topics or do_all:
        print(f"\n=== 主题分析 ===")
        result = extract_topics_llm(msgs)
        if "error" in result:
            print(f"  LLM不可用，使用简单模�?)
            result = extract_topics_simple(msgs)
        for t in result.get("topics", []):
            print(f"  📌 {t}")

    return msgs, stats


# ══════════════════════════════════════════════════════�?
# CLI
# ══════════════════════════════════════════════════════�?

def main():
    parser = argparse.ArgumentParser(description="微信消息 AI 分析")
    parser.add_argument("--friend", required=True, help="联系人名�?)
    parser.add_argument("--wxid", default="szyuyangmin", help="数据子目�?)
    parser.add_argument("--topics", action="store_true", help="主题提取")
    parser.add_argument("--keywords", action="store_true", help="关键词提�?)
    parser.add_argument("--all", action="store_true", help="全部分析")
    args = parser.parse_args()

    db = WeChatDB(wxid=args.wxid)
    analyze(db, args.friend,
            do_topics=args.topics,
            do_keywords=args.keywords,
            do_all=args.all)


if __name__ == "__main__":
    main()
