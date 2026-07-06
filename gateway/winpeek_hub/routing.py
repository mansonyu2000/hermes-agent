"""
routing.py — WinPeek Hub 跨平台消息路由

当用户 A 在微信上发消息给 Hermes，
Hub 查找 A 所属的 tenant，
然后根据 tenant 成员表找到用户 B 在钉钉上的绑定，
如果 B 在线，消息可以跨平台投递。

流程:
  微信(张三) → Hermes Gateway → Hub 路由 → 钉钉(李四)
"""

import logging
from typing import Optional
from .tenant import get_tenant_for_user, list_tenant_members

logger = logging.getLogger(__name__)


def resolve_cross_platform_target(
    from_platform: str,
    from_uid: str,
    target_display_name: str
) -> Optional[dict]:
    """
    解析跨平台投递目标。
    
    Args:
        from_platform: 消息来源平台 (如 'wechat')
        from_uid: 发送者在平台上的 UID (如 'wxid_xxx')
        target_display_name: 接收者显示名 (如 '李四')
    
    Returns:
        {"platform": "dingtalk", "platform_uid": "dt_xxx", "display_name": "李四"}
        或 None (未找到)
    """
    # 1. 找到发送者的 tenant
    sender_tenant = get_tenant_for_user(from_platform, from_uid)
    if not sender_tenant:
        logger.debug(f"Sender {from_uid}@{from_platform} has no tenant binding")
        return None
    
    # 2. 列出同 tenant 的所有成员
    members = list_tenant_members(sender_tenant["tenant_id"])
    
    # 3. 匹配 target_display_name
    for member in members:
        if member.get("display_name") == target_display_name:
            return {
                "platform": member["platform"],
                "platform_uid": member["platform_uid"],
                "display_name": member["display_name"],
                "tenant_id": sender_tenant["tenant_id"],
            }
    
    return None


def get_member_platforms(tenant_id: str, user_id: int) -> list:
    """
    获取某个用户在哪些平台上有绑定。
    用于判断"这个用户现在可以通过哪个平台收到消息"。
    """
    members = list_tenant_members(tenant_id)
    return [
        {"platform": m["platform"], "platform_uid": m["platform_uid"]}
        for m in members if m["user_id"] == user_id
    ]
