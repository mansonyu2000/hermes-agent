"""
wechat_to_relationship.py — WeChat数据 → relationship-manager JSON ETL管道

功能:
  1. 从MySQL读取 wechat_friend + wechat_chat
  2. 计算5维评分(个人模板) 或 8维评分(商业模板)
  3. 聊天聚合为事件时间线
  4. 关系阶段自动推算
  5. 输出 relationship-manager 兼容 JSON

用法:
  python scripts/wechat_to_relationship.py                    # 默认输出个人模板
  python scripts/wechat_to_relationship.py --mode business    # 商业模板(8维)
  python scripts/wechat_to_relationship.py --mode both        # 两种模板都输出
  python scripts/wechat_to_relationship.py --limit 10         # 只处理前10个好友(测试)
  python scripts/wechat_to_relationship.py --out ./output     # 指定输出目录
"""
from __future__ import annotations

import json
import os
import sys
import io
import time
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── MySQL 连接 ────────────────────────────────────────────
MYSQL_CONFIG = {
    "host": os.environ.get("DB_HOST", "192.168.3.23"),
    "user": os.environ.get("DB_USER", "winpeek"),
    "password": os.environ.get("DB_PASS", "Server33"),
    "database": os.environ.get("DB_NAME", "winpeek-db2"),
    "charset": "utf8mb4",
}

# ── 颜色预设 ────────────────────────────────────────────────
PROFILE_COLORS = [
    "linear-gradient(145deg,#786589,#27283f 58%,#263b39)",
    "linear-gradient(145deg,#5c4b7a,#2a1e3a 58%,#1a3a3a)",
    "linear-gradient(145deg,#6b4e7a,#1f2a3f 58%,#2a4a3a)",
    "linear-gradient(145deg,#7a5c5c,#3a2222 58%,#2a3a3a)",
    "linear-gradient(145deg,#4a667a,#1e2a3f 58%,#3a3a2a)",
    "linear-gradient(145deg,#5a6a7a,#202a3a 58%,#2a3a4a)",
    "linear-gradient(145deg,#6a5a5a,#3a1e2a 58%,#2a3a3a)",
    "linear-gradient(145deg,#4a5a6a,#1e2e3f 58%,#3a3a1a)",
]

# ── 5维个人指标定义 ─────────────────────────────────────────
HEART_METRICS = [
    {"id": "familiarity", "label": "熟悉度"},
    {"id": "trust",       "label": "信任感"},
    {"id": "curiosity",   "label": "好奇心"},
    {"id": "initiative",  "label": "主动性"},
    {"id": "risk",        "label": "风险性"},
]

# ── 8维商业指标定义 ─────────────────────────────────────────
BUSINESS_METRICS = [
    {"id": "biz_closeness",    "label": "亲密度"},
    {"id": "biz_trust",        "label": "信任度"},
    {"id": "biz_respect",      "label": "尊重度"},
    {"id": "biz_affection",    "label": "好感度"},
    {"id": "biz_value",        "label": "商业价值"},
    {"id": "biz_growth",       "label": "成长价值"},
    {"id": "biz_credit",       "label": "经济信用"},
    {"id": "biz_reciprocity",  "label": "互惠度"},
]

# ── source_type -> 标签映射 ─────────────────────────────────
SOURCE_TAG_MAP = {
    "card_share":   "名片分享",
    "phone_search": "手机号",
    "wxid_search":  "微信号",
    "group_chat":   "群聊",
    "qr_scan":      "扫一扫",
}

# ── 关系阶段定义 ────────────────────────────────────────────
HEART_MILESTONES = [
    {"name": "初识",    "description": "刚加上微信，还在互相了解的阶段。"},
    {"name": "熟悉",    "description": "有过几次互动，彼此印象不错。"},
    {"name": "稳定",    "description": "关系趋于稳定，有规律的互动。"},
    {"name": "长期",    "description": "认识已久，关系基础扎实。"},
]

BUSINESS_MILESTONES = [
    {"name": "初次接触",  "description": "刚建立联系，尚未深入沟通。"},
    {"name": "意向确认",  "description": "有过初步沟通，对方表达兴趣。"},
    {"name": "商务洽谈",  "description": "进入实质性商务对话阶段。"},
    {"name": "合作签约",  "description": "已达成合作或签约。"},
    {"name": "长期维护",  "description": "长期合作伙伴，关系稳固。"},
]


def connect_mysql():
    import pymysql
    return pymysql.connect(**MYSQL_CONFIG)


def get_friends_with_chats(conn, limit=None):
    """获取有聊天记录的微信好友列表。

    wechat_chat 中 from_uid/to_uid 存的是昵称（非wxid），需匹配 wechat_friend.nickname。
    排除群聊（gid不为空的）和系统消息。
    """
    sql = """
    SELECT DISTINCT f.id, f.wxid, f.nickname, f.alias, f.region,
           f.signature, f.source, f.source_type, f.tags,
           f.avatar_url, f.first_met, f.is_starred, f.shared_groups
    FROM wechat_friend f
    WHERE f.is_friend = 1
      AND f.nickname IS NOT NULL
      AND (
        f.nickname IN (
            SELECT DISTINCT from_uid FROM wechat_chat
            WHERE gid IS NULL AND is_date_sep = 0 AND from_uid IS NOT NULL
        )
        OR f.nickname IN (
            SELECT DISTINCT to_uid FROM wechat_chat
            WHERE gid IS NULL AND is_date_sep = 0 AND to_uid IS NOT NULL
        )
        OR f.alias IN (
            SELECT DISTINCT from_uid FROM wechat_chat
            WHERE gid IS NULL AND is_date_sep = 0 AND from_uid IS NOT NULL
        )
        OR f.alias IN (
            SELECT DISTINCT to_uid FROM wechat_chat
            WHERE gid IS NULL AND is_date_sep = 0 AND to_uid IS NOT NULL
        )
      )
    ORDER BY f.id
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, row)) for row in rows]


def get_friend_chats(conn, friend):
    """获取某个好友的全部聊天记录。

    匹配逻辑: from_uid/to_uid 存的是昵称，需同时尝试 nickname 和 alias。
    """
    nickname = friend.get("nickname", "")
    alias = friend.get("alias", "")

    cur = conn.cursor()
    params = []
    conditions = []
    for name in (nickname, alias):
        if name:
            conditions.append("(from_uid = %s OR to_uid = %s)")
            params.extend([name, name])

    if not conditions:
        return []

    sql = f"""
    SELECT id, content, is_from_me, msg_type, msg_ts, file_name, from_uid, to_uid
    FROM wechat_chat
    WHERE ({" OR ".join(conditions)}) AND gid IS NULL AND is_date_sep = 0
    ORDER BY msg_ts ASC
    """
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def calc_heart_metrics(chats, friend):
    """计算5维个人评分"""
    total = len(chats)
    if total == 0:
        return {"familiarity": 10, "trust": 30, "curiosity": 10, "initiative": 20, "risk": 5}

    from_me = sum(1 for m in chats if m.get("is_from_me"))
    from_other = total - from_me

    # 长消息比例 (>50字)
    long_msgs = sum(1 for m in chats if m.get("content") and len(str(m.get("content", ""))) > 50)
    long_ratio = long_msgs / max(total, 1)

    # 有消息的天数
    msg_dates = set()
    for m in chats:
        ts = m.get("msg_ts")
        if ts:
            msg_dates.add(str(ts)[:10] if isinstance(ts, str) else ts.strftime("%Y-%m-%d"))
    active_days = max(len(msg_dates), 1)

    # 认识天数
    first_met = friend.get("first_met")
    days_known = 365
    if first_met:
        try:
            days_known = max((datetime.now() - datetime.strptime(first_met[:10], "%Y-%m-%d")).days, 30)
        except Exception:
            pass

    # 熟悉度: 有消息天数 + 消息数量加权
    familiarity = min(100, int(
        min(active_days / max(days_known, 30), 1) * 50 +
        min(total / 50, 1) * 30 +
        (20 if active_days > 3 else 0)
    ))

    # 信任感: 对方主动发言比例 + 回复长消息
    trust = min(100, int((from_other / max(total, 1)) * 60 + long_ratio * 40))

    # 好奇心: 长消息比例 + 对方提问
    curiosity = min(100, int(long_ratio * 70 + 20))

    # 主动性: 自己占比
    initiative = min(100, int((from_me / max(total, 1)) * 80 + 10))

    # 风险性: 来源方式加权
    risk = 15
    st = friend.get("source_type") or ""
    if st == "card_share":
        risk = 25
    elif st == "phone_search":
        risk = 20
    elif st == "group_chat":
        risk = 30
    elif st == "wxid_search":
        risk = 35
    elif st == "qr_scan":
        risk = 40

    return {
        "familiarity": familiarity,
        "trust": trust,
        "curiosity": curiosity,
        "initiative": initiative,
        "risk": risk,
    }


def calc_business_metrics(chats, friend):
    """计算8维商业评分"""
    base = calc_heart_metrics(chats, friend)
    total = len(chats)
    from_me = sum(1 for m in chats if m.get("is_from_me"))

    # 商业关键词检测
    biz_keywords = ["报价", "合同", "订单", "付款", "合作", "项目", "方案", "预算",
                    "报价单", "发票", "招标", "投标", "签约", "协议", "回款", "佣金",
                    "采购", "供应商", "客户", "需求", "渠道", "代理", "价格", "优惠",
                    "定金", "尾款", "对公", "税", "验收", "交付", "上线", "测试",
                    "产品", "服务", "方案书", "PPT", "演示", "面谈", "见面", "拜访"]
    biz_count = sum(1 for m in chats if m.get("content") and
                    any(kw in str(m.get("content", "")) for kw in biz_keywords))
    biz_ratio = biz_count / max(total, 1)

    # 回复速度估算 (相邻消息时间差)
    reply_speed = 30  # 默认中等
    msg_times = []
    for m in chats:
        ts = m.get("msg_ts")
        if ts:
            msg_times.append(ts if isinstance(ts, datetime) else datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S"))
    if len(msg_times) >= 2:
        gaps = [(msg_times[i+1] - msg_times[i]).total_seconds() for i in range(len(msg_times)-1)]
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap < 300:   reply_speed = 80  # 5分钟内
        elif avg_gap < 1800: reply_speed = 60  # 30分钟内
        elif avg_gap < 7200: reply_speed = 40  # 2小时内

    return {
        "biz_closeness":    base["familiarity"],
        "biz_trust":        min(100, base["trust"] + int(biz_ratio * 30)),
        "biz_respect":      min(100, int((1 - from_me / max(total, 1)) * 50 + reply_speed * 0.3 + biz_ratio * 20)),
        "biz_affection":    min(100, int(base["curiosity"] * 0.7 + biz_ratio * 30)),
        "biz_value":        min(100, int(biz_ratio * 60 + biz_count / max(total, 1) * 30 + 10)),
        "biz_growth":       min(100, int(base["curiosity"] * 0.5 + reply_speed * 0.3 + 15)),
        "biz_credit":       50,   # 需要经济往来数据，暂无则默认50
        "biz_reciprocity":  min(100, int((from_me / max(total, 1)) * 40 + (1 - from_me / max(total, 1)) * 30 + 15)),
    }


def aggregate_events(chats, milestones, max_events=20):
    """将聊天记录聚合为事件（每100条或按时间自然分段）"""
    if not chats:
        return []

    events = []
    batch_size = max(1, len(chats) // min(max_events, 8))  # 最少8个事件
    batch_size = min(batch_size, 100)

    for i in range(0, len(chats), batch_size):
        batch = chats[i:i+batch_size]
        if not batch:
            continue

        # 时间范围
        first_ts = batch[0].get("msg_ts")
        last_ts = batch[-1].get("msg_ts")
        date_str = ""
        if first_ts:
            ts = first_ts if isinstance(first_ts, str) else str(first_ts)
            date_str = ts[:10]

        # 内容摘要: 取3条代表性消息
        samples = [m for m in batch if m.get("content") and len(str(m.get("content", ""))) > 5][:3]
        sample_text = "；".join(str(m.get("content", ""))[:40] for m in samples)

        # 关键词提取
        all_text = " ".join(str(m.get("content", "")) for m in batch if m.get("content"))
        word_counts = defaultdict(int)
        for word in all_text.replace("，", " ").replace("。", " ").replace("？", " ").split():
            word = word.strip()
            if len(word) >= 2 and len(word) <= 6:
                word_counts[word] += 1
        top_words = [w for w, _ in sorted(word_counts.items(), key=lambda x: -x[1])[:5]]

        # 生成标题
        if top_words:
            title = f"关于{'/'.join(top_words[:3])}的对话"
        else:
            title = f"{date_str} 的聊天互动"

        summary = sample_text[:80] or f"共{batch_size}条消息"
        detail = "\n".join(
            f"[{'我' if m.get('is_from_me') else 'TA'}] {str(m.get('content', ''))[:120]}"
            for m in batch[:15]
        )

        # 阶段归属: 按时间比例
        stage_idx = min(i // max(batch_size, 1), len(milestones) - 1)

        events.append({
            "date": date_str or "时间待补",
            "title": title,
            "summary": summary,
            "detail": detail,
            "stage": stage_idx,
        })

    return events[:max_events]


def calc_stage(friend):
    """根据first_met推算关系阶段"""
    first_met = friend.get("first_met")
    if not first_met:
        return "初识", 0
    try:
        fm = first_met[:10]
        days = (datetime.now() - datetime.strptime(fm, "%Y-%m-%d")).days
    except Exception:
        return "初识", 0

    if days <= 7:
        return "初识", 0
    elif days <= 30:
        return "熟悉", 1
    elif days <= 90:
        return "稳定", 2
    else:
        return "长期", 3


def calc_business_stage(friend):
    """商业模板的阶段推算"""
    first_met = friend.get("first_met")
    if not first_met:
        return "初次接触", 0
    try:
        fm = first_met[:10]
        days = (datetime.now() - datetime.strptime(fm, "%Y-%m-%d")).days
    except Exception:
        return "初次接触", 0

    if days <= 7:
        return "初次接触", 0
    elif days <= 30:
        return "意向确认", 1
    elif days <= 180:
        return "商务洽谈", 2
    elif days <= 365:
        return "合作签约", 3
    else:
        return "长期维护", 4


def build_tags(friend):
    """构建标签列表"""
    tags = []
    # 现有标签
    if friend.get("tags"):
        tags.extend([t.strip() for t in str(friend["tags"]).split(",") if t.strip()][:3])

    # source_type映射
    st = friend.get("source_type") or ""
    tag = SOURCE_TAG_MAP.get(st)
    if tag and tag not in tags:
        tags.insert(0, tag)

    # region
    region = friend.get("region") or ""
    if region and region not in tags:
        city = region.split()[-1] if " " in region else region
        if city and city not in ["中国大陆", "阿尔巴尼亚"]:
            tags.append(city)

    return tags[:6]


def build_profile(friend, chats, mode="heart"):
    """为单个好友构建完整的 profile 数据"""
    name = friend.get("nickname") or friend.get("wxid") or "未知"
    wxid = friend.get("wxid") or ""

    if mode == "business":
        metrics = calc_business_metrics(chats, friend)
        metric_schema = BUSINESS_METRICS
        milestones = BUSINESS_MILESTONES
        stage_name, stage_idx = calc_business_stage(friend)
        relation_type = "work"
    else:
        metrics = calc_heart_metrics(chats, friend)
        metric_schema = HEART_METRICS
        milestones = HEART_MILESTONES
        stage_name, stage_idx = calc_stage(friend)
        relation_type = "heart"

    # 事件聚合
    events = aggregate_events(chats, milestones)

    profile_id = f"wx-{wxid.replace(':', '-')}" if wxid else f"profile-{hash(name)}"

    return {
        "id": profile_id,
        "name": name,
        "initial": name[0] if name else "?",
        "title": friend.get("alias") or friend.get("signature") or "",
        "stage": stage_name,
        "color": PROFILE_COLORS[hash(wxid) % len(PROFILE_COLORS)],
        "tags": build_tags(friend),
        "summary": "微信联系人，{}。{}{} 条聊天记录。".format(
            friend.get('source', '') or '来源未知',
            f"地区: {friend.get('region', '')}。" if friend.get('region') else '',
            len(chats)
        ),
        "persona": {
            "communication": "待AI分析",
            "interests": build_tags(friend)[:4],
            "boundaries": "待AI分析",
            "confidence": f"基于{len(chats)}条聊天记录的基本画像",
        },
        "metrics": {m["id"]: metrics[m["id"]] for m in metric_schema},
        "metricSchema": metric_schema,
        "milestones": [m["name"] for m in milestones],
        "milestoneDetails": milestones,
        "current": stage_idx,
        "focusedMilestone": stage_idx,
        "stageMetrics": [
            {m["id"]: min(100, max(0, int(metrics[m["id"]] * (0.3 + 0.7 * (i + 1) / max(len(milestones), 1)))))
             for m in metric_schema}
            for i in range(len(milestones))
        ],
        "events": events,
        "photos": [friend.get("avatar_url")] if friend.get("avatar_url") else [],
        "direction": f"当前处于{stage_name}阶段，沟通频率{'高' if metrics.get('familiarity', 0) > 60 else '一般'}。",
        "analysis": f"自{friend.get('first_met', '未知时间')}添加好友以来，共互动{len(chats)}次。聊天主要在{'你' if metrics.get('initiative', 0) > 50 else '对方'}主导。",
        "aiAdvice": "建议定期保持联系，关注对方动态。" if metrics.get("familiarity", 0) > 40 else "可以适当增加互动频率。",
        "contextSummary": f"微信好友，{friend.get('region', '') or ''}，{friend.get('source', '') or ''}添加。",
        "relationType": relation_type,
        "materials": [],
        "sourceRecords": [],
        "archiveChat": [],
        "coverPhotoIndex": 0,
    }


def run_etl(mode="heart", limit=None, output_dir="./output"):
    """主ETL流程"""
    print(f"\n{'='*60}")
    print(f"  WeChat → relationship-manager ETL")
    print(f"  Mode: {mode} | Limit: {limit or 'ALL'} | Output: {output_dir}")
    print(f"{'='*60}\n")

    # 1. 连接MySQL
    print("[1/5] 连接MySQL...")
    conn = connect_mysql()
    print(f"  ✅ 已连接 {MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}")

    # 2. 获取好友列表
    print("[2/5] 获取有聊天记录的好友...")
    friends = get_friends_with_chats(conn, limit=limit)
    print(f"  ✅ 找到 {len(friends)} 个好友")

    # 3. 处理每个好友
    print("[3/5] 计算评分 & 聚合事件...")
    profiles = []
    for i, friend in enumerate(friends):
        wxid = friend["wxid"]
        name = friend.get("nickname") or wxid
        chats = get_friend_chats(conn, friend)

        if mode == "both":
            profiles.append(build_profile(friend, chats, "heart"))
            profiles.append(build_profile(friend, chats, "business"))
        else:
            profiles.append(build_profile(friend, chats, mode))

        if (i + 1) % 20 == 0 or i == len(friends) - 1:
            print(f"  [{i+1}/{len(friends)}] {name} ({len(chats)}条消息)")

    conn.close()

    # 4. 构建输出
    print("[4/5] 构建输出JSON...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if mode == "both":
        # 分开输出两个文件
        heart_profiles = [p for p in profiles if p.get("relationType") == "heart"]
        biz_profiles = [p for p in profiles if p.get("relationType") == "work"]

        heart_data = build_rm_data(heart_profiles, "heart")
        biz_data = build_rm_data(biz_profiles, "business")

        heart_path = output_path / "relationship-manager-heart.json"
        biz_path = output_path / "relationship-manager-business.json"

        heart_path.write_text(json.dumps(heart_data, ensure_ascii=False, indent=2), encoding="utf-8")
        biz_path.write_text(json.dumps(biz_data, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"  ✅ 个人模板: {heart_path} ({len(heart_profiles)}个人物)")
        print(f"  ✅ 商业模板: {biz_path} ({len(biz_profiles)}个人物)")
    else:
        data = build_rm_data(profiles, mode)
        out_file = output_path / f"relationship-manager-{mode}.json"
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✅ 输出文件: {out_file} ({len(profiles)}个人物)")

    # 5. 统计摘要
    print("[5/5] 统计摘要:")
    for p in profiles[:5]:
        m = p["metrics"]
        vals = ", ".join(f"{k}={v}" for k, v in list(m.items())[:5])
        print(f"  📋 {p['name'][:20]:<22} | {p['stage']:<6} | 事件:{len(p['events']):<3} | {vals[:60]}")

    if len(profiles) > 5:
        print(f"  ... 共 {len(profiles)} 个人物")

    print(f"\n{'='*60}")
    print(f"  ✅ ETL完成! 数据可导入 relationship-manager")
    print(f"{'='*60}\n")
    return profiles


def build_rm_data(profiles, mode):
    """构建 relationship-manager 兼容的完整数据包"""
    preset = "heart" if mode in ("heart", "both") else "work"
    preset_config = {
        "heart": {
            "title": "人际关系管理器",
            "subtitle": "本地关系资料库 · WeChat数据导入",
            "mark": "人",
            "modeLabel": "通用关系管理",
            "theme": "heart",
        },
        "business": {
            "title": "商业关系管理器",
            "subtitle": "商务人脉资料库 · WeChat数据导入",
            "mark": "商",
            "modeLabel": "商业关系管理",
            "theme": "work",
        },
    }

    cfg = preset_config.get(mode, preset_config["heart"])

    return {
        "format": "relationship-manager-local-v1",
        "compatibleFormat": "relationship-manager-sync-v1",
        "exportedAt": datetime.now().isoformat(),
        "activeAccountId": "wechat-import",
        "activeAccountName": f"WeChat导入-{cfg['title']}",
        "accountBook": {
            "accounts": [{
                "id": "wechat-import",
                "name": f"WeChat导入-{cfg['title']}",
                "pinHash": "",
                "data": build_store_data(profiles, mode, cfg),
            }],
            "activeId": "wechat-import",
        },
        "data": build_store_data(profiles, mode, cfg),
        "note": f"从 WeChat MySQL 自动导入生成。模式: {mode}。",
    }


def build_store_data(profiles, mode, cfg):
    """构建 store 数据（不含 api key）"""
    return {
        "profiles": profiles,
        "selected": profiles[0]["id"] if profiles else "",
        "tab": "概览",
        "api": {
            "baseUrl": "https://api.deepseek.com/v1",
            "model": "deepseek-v4-flash",
            "apiKey": "",
            "persona": "像一位冷静、尊重边界的关系记录顾问。",
        },
        "me": {
            "about": "微信用户",
            "workAndCreation": "",
            "lifeAndHealth": "",
            "relationshipHistory": "",
            "patterns": "",
            "goals": "",
            "boundaries": "",
            "avatar": "",
            "aiPortrait": "",
            "aiPortraitUpdatedAt": 0,
        },
        "app": {
            "activePreset": mode if mode != "business" else "work",
            "themePalette": "heart" if mode != "business" else "businessBlue",
            "customTitle": "",
            "customSubtitle": "",
            "customMark": "",
            "customAccent": "",
            "customGold": "",
        },
        "trash": [],
    }


# ─────────────────────────────────────────────────────────
# 查询工具: 谁该联系
# ─────────────────────────────────────────────────────────

def query_who_to_contact(profiles, top_n=20):
    """分析谁该联系: 按失联风险+亲密度综合排序"""
    results = []
    for p in profiles:
        m = p["metrics"]
        events = p.get("events", [])

        # 最后互动日期
        last_date = None
        if events:
            last_date = events[-1].get("date", "")
        elif p.get("first_met"):
            last_date = p.get("first_met")

        days_since = 999
        if last_date and last_date != "时间待补":
            try:
                days_since = (datetime.now() - datetime.strptime(last_date[:10], "%Y-%m-%d")).days
            except Exception:
                pass

        # 亲密度 (不同模板用不同key)
        closeness = m.get("familiarity") or m.get("biz_closeness") or 50
        trust = m.get("trust") or m.get("biz_trust") or 50
        biz_val = m.get("biz_value") or 0

        # 综合优先级: 失联天数 * 亲密度权重
        priority = closeness * 0.4 + trust * 0.2 + biz_val * 0.2 - max(0, days_since - 30) * 0.2

        # 分类
        if days_since > 90 and closeness > 60:
            category = "🔴 重要失联"
        elif days_since > 30 and closeness > 50:
            category = "🟡 需要联系"
        elif biz_val > 60 and days_since > 14:
            category = "💰 商业跟进"
        elif days_since <= 7:
            category = "🟢 近期活跃"
        else:
            category = "⚪ 正常"

        results.append({
            "name": p["name"],
            "stage": p["stage"],
            "category": category,
            "closeness": closeness,
            "trust": trust,
            "biz_value": biz_val,
            "events": len(events),
            "days_since_last": days_since,
            "priority": round(priority, 1),
        })

    results.sort(key=lambda x: (-x["priority"]))
    return results[:top_n]


def print_contact_ranking(results):
    """打印沟通对象排行榜"""
    print(f"\n{'='*70}")
    print(f"  📋 谁该联系 - 沟通优先级排行榜 (Top {len(results)})")
    print(f"{'='*70}")
    print(f"  {'排名':<5} {'分类':<12} {'姓名':<22} {'亲密度':<7} {'天数':<6} {'事件':<5}")
    print(f"  {'-'*65}")

    for i, r in enumerate(results):
        print(f"  {i+1:<5} {r['category']:<12} {r['name'][:20]:<22} {r['closeness']:<7} "
              f"{r['days_since_last']:<6} {r['events']:<5}")

    print(f"{'='*70}\n")


def print_cooling_warning(profiles):
    """打印降温预警: 最近活跃度下降的好友"""
    print(f"\n{'='*70}")
    print(f"  ⚠️ 降温预警 - 30天内互动减少的好友")
    print(f"{'='*70}")

    warnings = []
    for p in profiles:
        events = p.get("events", [])
        if len(events) < 3:
            continue

        # 最近30天 vs 30-60天 事件数对比
        recent = sum(1 for e in events if _event_in_range(e, 30))
        older = sum(1 for e in events if _event_in_range(e, 60) and not _event_in_range(e, 30))

        if older > recent + 1 and older > 0:
            drop = int((older - recent) / max(older, 1) * 100)
            m = p["metrics"]
            closeness = m.get("familiarity") or m.get("biz_closeness") or 50
            warnings.append({
                "name": p["name"],
                "closeness": closeness,
                "recent": recent,
                "older": older,
                "drop_pct": drop,
            })

    warnings.sort(key=lambda x: (-x["drop_pct"], -x["closeness"]))
    for i, w in enumerate(warnings[:10]):
        print(f"  {i+1}. {w['name'][:25]:<27} 亲密度:{w['closeness']:<4} "
              f"近30天:{w['recent']}条  前30天:{w['older']}条  ↓{w['drop_pct']}%")

    if not warnings:
        print("  ✅ 未检测到明显降温。")

    print(f"{'='*70}\n")


def _event_in_range(event, days):
    """判断事件是否在最近N天内"""
    date_str = event.get("date", "")
    if not date_str or date_str == "时间待补":
        return False
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return (datetime.now() - dt).days <= days
    except Exception:
        return False


# ─────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WeChat → relationship-manager ETL")
    parser.add_argument("--mode", choices=["heart", "business", "both"], default="both",
                        help="模板类型: heart(个人5维) / business(商业8维) / both(两种)")
    parser.add_argument("--limit", type=int, default=None,
                        help="限制处理好友数(测试用)")
    parser.add_argument("--out", default="./output",
                        help="输出目录")
    parser.add_argument("--query", action="store_true",
                        help="仅查询谁该联系(不重新ETL)")
    parser.add_argument("--json", default=None,
                        help="从已有JSON文件读取并分析")
    args = parser.parse_args()

    if args.query and args.json:
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
        profiles = data.get("data", {}).get("profiles", [])
        if not profiles:
            print("未找到 profiles 数据")
            return
        results = query_who_to_contact(profiles, top_n=20)
        print_contact_ranking(results)
        print_cooling_warning(profiles)
        return

    profiles = run_etl(mode=args.mode, limit=args.limit, output_dir=args.out)

    # 自动输出查询结果
    if profiles:
        results = query_who_to_contact(profiles, top_n=20)
        print_contact_ranking(results)
        print_cooling_warning(profiles)


if __name__ == "__main__":
    main()
