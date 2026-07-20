---
title: "Peeka 登录页面设计规范"
description: "源自 pm.test.com 的登录页面还原 — 左右分栏、视觉层级、交互逻辑、组织信息字段"
date: 2026-07-21
status: done
type: spec
---

# Peeka 登录页面设计规范

## 一、页面布局

左右两栏，左侧品牌区（41.6%），右侧登录表单（58.3%）。

- **左侧**：渐变蓝紫背景 + Logo + AI 图标，纯品牌展示，无交互
- **右侧**：白底卡片，从上到下：标题|语言切换|过期提示|用户名/密码|保持登录|忘记密码|登录按钮

## 二、视觉层次

1. **主标题** — 黑色加粗 16px，展示"XX公司项目管理系统"（可配公司名）
2. **表单卡片** — 白底圆角阴影，居中悬浮
3. **登录按钮** — 品牌蓝 100% 宽度
4. **辅链接** — 灰小字"忘记密码"在密码框右侧

## 三、交互逻辑

- 用户名输入框自动聚焦
- 密码框支持回车提交
- "保持登录" checkbox 默认关闭
- 语言切换：简体/繁體/English 右上下拉
- session 过期：红色提示条"系统登录已过期，请重新登录"
- POST user-login.json → 成功跳转 referer → 失败提示

## 四、组织信息字段（squads 表）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | VARCHAR(128) | 组织名/公司名（唯一键） |
| description | TEXT | 组织简介 |
| address | TEXT | 注册地址 |
| industry | VARCHAR(64) | 信息技术/金融/教育/医疗… |
| founded_at | VARCHAR(16) | 成立时间：2020-03 |
| legal_person | VARCHAR(64) | 法人代表 |
| contact_phone | VARCHAR(32) | 联系电话 |
| website | VARCHAR(256) | 网站 URL |
| contact_email | VARCHAR(128) | 联系邮箱 |
| managed_by_uid | INT | 管理人 winpeek uid |
| owner_person_id | INT | 创建者 persons.id |
| invite_code | VARCHAR(8) | 6位邀请码 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
