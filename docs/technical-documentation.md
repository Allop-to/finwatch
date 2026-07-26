# FinWatch 项目技术文档

> 版本：1.0.0 | 更新日期：2026-07-25 | License: MIT

---

## 目录

1. [项目概述](#1-项目概述)
2. [需求分析](#2-需求分析)
3. [技术栈](#3-技术栈)
4. [系统架构](#4-系统架构)
5. [项目目录结构](#5-项目目录结构)
6. [数据库设计](#6-数据库设计)
7. [核心模块实现](#7-核心模块实现)
8. [API 接口文档](#8-api-接口文档)
9. [前端页面设计](#9-前端页面设计)
10. [性能与安全](#10-性能与安全)
11. [测试策略](#11-测试策略)
12. [部署指南](#12-部署指南)

---

## 1. 项目概述

**FinWatch** 是一个本地优先的个人财务行为数据挖掘与异常消费预测系统。系统通过多维度检测引擎自动发现异常消费模式，借助大模型提供通俗化解读，支持 Web / Android / iOS / Desktop 多平台部署。

### 核心能力

- 多源消费数据导入（支付宝/微信/银行 CSV/OFX/QIF + 手动录入）
- 四层检测引擎（统计异常 + 规则引擎 + 行为模式 + 欺诈检测）
- DeepSeek 大模型智能解读 + 离线降级
- 实时 WebSocket 告警推送
- 响应式 Web + Capacitor 移动端 + Electron 桌面端

---

## 2. 需求分析

### 2.1 功能需求

| 模块 | 需求描述 | 优先级 |
|------|---------|:-----:|
| 数据导入 | 支持支付宝/微信/银行 CSV/OFX/QIF 文件导入 + 手动录入 + 批量录入 | P0 |
| 幂等去重 | SHA256 哈希防重，重复导入自动跳过 | P0 |
| 分类管理 | 24 个系统预置分类（emoji + 二级树）+ 自定义分类 | P0 |
| 异常检测 | 统计异常（Isolation Forest + IQR）+ 规则引擎（硬规则否决）+ 行为模式 + 欺诈检测 | P0 |
| 实时告警 | WebSocket 推送 + 浏览器 Toast + 移动端系统通知 | P0 |
| 预算管理 | 月度/分类预算 + 进度条 + 超阈值预警 | P1 |
| AI 解读 | DeepSeek 实时解读异常 + 离线 Jinja2 模板降级 | P1 |
| 智能对话 | 自然语言查询消费数据 + 脱敏保护 | P1 |
| 分析报表 | 月度收支/每日趋势/分类占比/异常分布图表 | P1 |
| 检测规则 | 自定义规则 CRUD + 启用停用 + 硬规则标记 | P2 |
| 数据管理 | CSV 导出 + 清空检测/全部数据 | P2 |
| 多用户 | 单用户起步 + 数据库预留 user_id + 种子数据隔离 | P3 |
| 多平台 | Web + Docker + Android APK + iOS + Electron 桌面 | P3 |

### 2.2 非功能需求

| 类别 | 要求 |
|------|------|
| 性能 | 10 万条交易数据内检测 < 5 秒（Polars + DuckDB） |
| 安全 | LLM 调用前强制脱敏，银行卡/身份证/余额永不外传 |
| 隐私 | 所有数据本地存储（SQLite），不上传云端 |
| 可用性 | DeepSeek 不可用时自动降级为离线模板 |
| 可扩展 | 检测器/解析器插件化，实现 BaseDetector/BaseParser 即可扩展 |
| 兼容性 | Python 3.8+ / Node.js 18+ / Android 8+ / iOS 15+ |

---

## 3. 技术栈

### 3.1 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | >= 3.8 (推荐 3.11+) | 主语言 |
| FastAPI | >= 0.115 | REST API + WebSocket 框架 |
| Uvicorn | >= 0.30 | ASGI 服务器 |
| SQLAlchemy | >= 2.0 | ORM |
| SQLite | (内置) | 本地数据库 |
| PostgreSQL | 16 (Docker) | 容器化数据库 |
| Alembic | >= 1.13 | 数据库迁移 |
| DuckDB | >= 1.0 | OLAP 分析查询引擎 |
| Polars | >= 1.5 | 高性能 DataFrame + 特征工程 |
| PyOD | >= 2.0 | Isolation Forest 异常检测 |
| Scikit-learn | >= 1.3 | IQR / Z-Score 统计方法 |
| APScheduler | >= 3.10 | 定时任务调度 |
| Jinja2 | >= 3.1 | 离线模板引擎 |
| httpx | >= 0.27 | DeepSeek API 异步客户端 |
| Pydantic | >= 2.8 | 数据校验与配置管理 |

### 3.2 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| TypeScript | ~5.x | 类型安全 |
| React | 19 | UI 框架 |
| Vite | 8 | 构建工具 |
| Tailwind CSS | 3.4 | 原子化 CSS |
| Shadcn UI | (组件) | UI 组件（Button/Input/Badge/Sheet/Select） |
| Recharts | 3 | 图表（折线/饼图/柱状图） |
| React Router | 7 | 路由 |
| TanStack Query | 5 | 服务端状态缓存 |
| Zustand | 5 | 客户端状态管理 |
| Sonner | 2 | Toast 通知 |
| Axios | 1 | HTTP 请求 |

### 3.3 移动端与桌面端

| 技术 | 用途 |
|------|------|
| Capacitor 8 | Web → Android APK / iOS IPA |
| @capacitor/local-notifications | 移动端系统级推送通知 |
| Electron 43 | Web → Windows/macOS/Linux 桌面应用 |
| electron-builder | 桌面应用打包分发 |

### 3.4 DevOps

| 技术 | 用途 |
|------|------|
| Docker + Docker Compose | 容器化一键部署 |
| GitHub Actions | CI/CD 自动化测试与构建 |
| pytest | Python 单元测试 + API 测试 |

---

## 4. 系统架构

### 4.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │   Web    │  │ Android  │  │   iOS    │  │  Desktop       │  │
│  │  Vite +  │  │ Capacitor│  │ Capacitor│  │  Electron      │  │
│  │  React   │  │  + APK   │  │  + IPA   │  │  + exe/dmg     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       └──────────────┴─────────────┴───────────────┘            │
│                          │ HTTP/WebSocket                        │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                    后端层 (Backend)                               │
│                          ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ REST API │  │WebSocket │  │ APScheduler│  │  CORS   │   │  │
│  │  │  /api/v1 │  │   /ws    │  │ 定时检测   │  │ 中间件   │   │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘   │  │
│  └───────┼─────────────┼─────────────┼────────────────────────┘  │
│          │             │             │                            │
│  ┌───────┴─────────────┴─────────────┴────────────────────────┐  │
│  │                    Service Layer (业务层)                    │  │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌─────────┐  │  │
│  │  │Import  │ │Detection │ │Budget  │ │ LLM  │ │Scheduler│  │  │
│  │  │Service │ │Service   │ │Service │ │Service│ │Service  │  │  │
│  │  └───┬────┘ └────┬─────┘ └───┬────┘ └──┬───┘ └─────────┘  │  │
│  └──────┼───────────┼───────────┼─────────┼───────────────────┘  │
│         │           │           │         │                       │
│  ┌──────┴───────────┴───────────┴─────────┴───────────────────┐  │
│  │                   Engine Layer (引擎层)                      │  │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐    │  │
│  │  │   Parsers    │  │         Detectors                │    │  │
│  │  │  ├─ Alipay   │  │  ├─ StatisticalDetector (PyOD)  │    │  │
│  │  │  ├─ Wechat   │  │  ├─ RuleDetector (硬/软规则)     │    │  │
│  │  │  ├─ BankCSV  │  │  ├─ PatternDetector (行为模式)  │    │  │
│  │  │  ├─ OFX      │  │  └─ FraudDetector (欺诈检测)    │    │  │
│  │  │  └─ QIF      │  └──────────────────────────────────┘    │  │
│  │  ├──────────────┤  ┌──────────────────────────────────┐    │  │
│  │  │  features.py │  │        preprocess.py             │    │  │
│  │  │  (特征工程)   │  │  (LLM数据脱敏 + 商户泛化引擎)     │    │  │
│  │  └──────────────┘  └──────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Data Layer (数据层)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐            │  │
│  │  │ SQLite   │  │ DuckDB   │  │ PostgreSQL   │            │  │
│  │  │ (本地)   │  │ (OLAP)   │  │ (容器化)      │            │  │
│  │  └──────────┘  └──────────┘  └──────────────┘            │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 数据流

```
用户录入/CSV上传 → Parser解析 → idempotency_hash去重 → SQLite存储
                                                              ↓
                                              APScheduler定时触发
                                                              ↓
                                    Polars特征工程(含冷启动防护)
                                                              ↓
                              4个检测器并行打分 → 混合融合算法
                                                              ↓
                         高危异常 → WebSocket推送 → 前端Toast/通知
                                                              ↓
                         DeepSeek解读(脱敏) / Jinja2模板(离线)
```

---

## 5. 项目目录结构

```
finwatch/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口 + 生命周期（建表+种子+调度器）
│   │   ├── config.py                 # Pydantic Settings（环境变量/DB/LLM配置）
│   │   ├── database.py               # SQLAlchemy 引擎 + Session 工厂
│   │   ├── api/v1/
│   │   │   ├── router.py             # 路由聚合
│   │   │   ├── transactions.py       # 交易 CRUD（REST API）
│   │   │   ├── categories.py         # 分类管理 API
│   │   │   ├── imports.py            # 文件导入 API（multipart upload）
│   │   │   ├── detection.py          # 异常检测触发 + 结果查询
│   │   │   ├── budget.py             # 预算管理 API
│   │   │   ├── llm.py                # LLM 解读 + 对话 + 用量统计
│   │   │   ├── rules.py              # 检测规则 CRUD + 数据管理
│   │   │   └── websocket.py          # WebSocket 连接管理 + 事件广播
│   │   ├── services/
│   │   │   ├── transaction_service.py  # 交易业务逻辑（含幂等哈希）
│   │   │   ├── import_service.py       # 导入管道（解析→去重→入库）
│   │   │   ├── detection_service.py    # 检测编排（4检测器+融合+解读）
│   │   │   ├── budget_service.py       # 预算计算（进度百分比）
│   │   │   ├── llm_service.py          # DeepSeek客户端+解释器+对话+限流
│   │   │   └── scheduler_service.py    # APScheduler定时任务
│   │   ├── engine/
│   │   │   ├── features.py             # Polars特征工程（冷启动防护）
│   │   │   ├── analyzer.py             # DuckDB OLAP查询（预留）
│   │   │   ├── preprocess.py           # 数据脱敏+商户泛化三级引擎
│   │   │   ├── parsers/
│   │   │   │   ├── base.py             # 解析器抽象基类
│   │   │   │   ├── alipay.py           # 支付宝CSV解析器
│   │   │   │   ├── wechat.py           # 微信CSV解析器
│   │   │   │   └── bank.py             # 银行CSV/OFX/QIF解析器
│   │   │   └── detectors/
│   │   │       ├── base.py             # 检测器抽象基类
│   │   │       ├── statistical.py      # 统计检测器（IF+IQR）
│   │   │       ├── rule.py             # 规则检测器（硬/软规则）
│   │   │       ├── pattern.py          # 行为模式检测器
│   │   │       └── fraud.py            # 欺诈检测器
│   │   ├── models/
│   │   │   ├── base.py                 # Declarative Base + TimestampMixin
│   │   │   ├── user.py                 # 用户模型
│   │   │   ├── transaction.py          # 交易模型（含idempotency_hash）
│   │   │   ├── category.py             # 分类模型（自引用+is_system）
│   │   │   ├── budget.py               # 预算模型
│   │   │   ├── detection_result.py     # 检测结果模型（JSON reasons）
│   │   │   ├── detection_rule.py       # 自定义检测规则模型
│   │   │   ├── import_record.py        # 导入记录模型
│   │   │   └── llm_conversation.py     # LLM对话历史模型
│   │   ├── schemas/                    # Pydantic请求/响应Schema
│   │   └── seeds/
│   │       ├── categories.json         # 24个系统预置分类数据
│   │       └── seeder.py               # 种子数据写入器
│   ├── templates/fallback/
│   │   └── anomaly_explanation.md      # Jinja2离线降级模板
│   ├── tests/
│   │   ├── conftest.py                 # pytest fixtures
│   │   ├── test_transactions.py        # 交易/分类/预算API测试
│   │   └── test_detection.py           # 检测/导入/规则/脱敏测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # 根组件（路由+QueryClient+Toaster）
│   │   ├── main.tsx                    # 入口
│   │   ├── index.css                   # Tailwind + Shadcn CSS变量
│   │   ├── components/
│   │   │   ├── ui/                     # Shadcn UI组件
│   │   │   ├── charts/                 # Recharts封装
│   │   │   └── layout/
│   │   │       ├── AppLayout.tsx       # 响应式布局+移动端Drawer
│   │   │       └── Sidebar.tsx         # 桌面侧边栏导航
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx           # 仪表盘（4卡片+2图表）
│   │   │   ├── Transactions.tsx        # 交易列表+搜索筛选分页
│   │   │   ├── Import.tsx              # 文件导入+手动录入+批量录入
│   │   │   ├── Detection.tsx           # 异常检测结果+触发
│   │   │   ├── Reports.tsx             # 分析报表（4维度图表）
│   │   │   ├── Budget.tsx              # 预算管理+进度条
│   │   │   ├── Chat.tsx                # AI对话（DeepSeek实时）
│   │   │   └── Settings.tsx            # 设置（分类+规则+数据）
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts         # WS连接+重连+降级轮询
│   │   │   └── useNotification.ts      # 平台自适应通知
│   │   ├── api/client.ts               # Axios实例+所有API封装
│   │   ├── store/
│   │   │   ├── alertStore.ts           # 告警状态
│   │   │   └── uiStore.ts              # UI状态
│   │   ├── types/index.ts              # TypeScript类型定义
│   │   └── lib/utils.ts                # cn()工具函数
│   ├── electron/
│   │   ├── main.js                     # Electron主进程
│   │   └── preload.js                  # 预加载脚本
│   ├── capacitor.config.ts             # Capacitor配置
│   ├── vite.config.ts                  # Vite配置（代理+别名）
│   ├── tailwind.config.js              # Tailwind配置
│   ├── tsconfig.json / tsconfig.app.json
│   ├── components.json                 # Shadcn UI配置
│   └── Dockerfile
├── .github/workflows/ci.yml            # GitHub Actions CI/CD
├── docker-compose.yml                   # Docker Compose编排
├── .gitignore
├── .env.example
├── LICENSE (MIT)
├── README.md
└── docs/
    ├── spec.md                          # 设计规格文档
    ├── phase-1-plan.md                  # Phase 1实现计划
    └── technical-documentation.md       # 本文档
```

---

## 6. 数据库设计

### 6.1 ER 图

```
users ──1:N── transactions ──N:1── categories (自引用parent_id)
  │               │
  │               ├── N:1 ── import_records
  │               │
  ├──1:N── budgets ──N:1──┘
  │
  ├──1:N── detection_results ──N:1── transactions
  │
  ├──1:N── detection_rules
  │
  └──1:N── llm_conversations
```

### 6.2 核心表结构

#### transactions（交易记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| user_id | INTEGER FK | 用户ID（多用户预留） |
| amount | REAL | 金额（正=收入，负通过type区分） |
| type | VARCHAR(10) | income / expense / transfer |
| category_id | INTEGER FK | 分类ID |
| transaction_date | DATETIME | 交易时间（索引） |
| description | VARCHAR(500) | 备注 |
| merchant | VARCHAR(200) | 商户名称（原始值） |
| payment_method | VARCHAR(50) | 支付方式 |
| source | VARCHAR(20) | manual / import |
| import_id | INTEGER FK | 导入批次ID |
| **idempotency_hash** | VARCHAR(64) UNIQUE | SHA256幂等键（防重核心） |
| tags | JSON | 灵活标签 |
| created_at | DATETIME | 创建时间 |

**idempotency_hash 生成规则：**
```
SHA256(user_id | amount | transaction_date | merchant | description)
```
所有字段先归一化（去空格、统一日期格式），再拼接哈希。导入时 `INSERT OR SKIP` 基于 UNIQUE 约束自动去重。

#### categories（分类）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | VARCHAR(50) | 分类名 |
| icon | VARCHAR(10) | emoji 图标 |
| parent_id | INTEGER FK (自引用) | 二级分类父级 |
| user_id | INTEGER FK (nullable) | NULL=系统预置（全局可见） |
| is_system | BOOLEAN | TRUE=系统预置，禁止编辑删除 |
| sort_order | INTEGER | 排序 |

#### detection_results（检测结果）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| transaction_id | INTEGER FK (nullable) | 关联交易 |
| detector_type | VARCHAR(30) | 检测器类型组合 |
| severity | VARCHAR(10) | high / medium / low |
| anomaly_score | REAL | 0.000 ~ 1.000 |
| **reason** | JSON | **结构化**数组，每项含 detector/method/score/detail |
| suggestion | TEXT | LLM 解读或离线模板文案 |
| is_read | BOOLEAN | 已读标记 |

#### detection_rules（自定义规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| condition | JSON | `{"field":"amount","operator":">","value":10000}` |
| is_hard_rule | BOOLEAN | 硬规则（命中即高危，否决权） |
| is_enabled | BOOLEAN | 启停开关 |

---

## 7. 核心模块实现

### 7.1 异常检测引擎

#### 7.1.1 检测流水线

```
Transaction数据 → Polars特征工程(冷启动防护) → 4检测器并行打分 → 混合融合 → 入库 → WebSocket推送
```

#### 7.1.2 四个检测器

| 检测器 | 方法 | 检测能力 | 权重 |
|--------|------|---------|:---:|
| **StatisticalDetector** | Isolation Forest + IQR + Z-Score | 金额离群、分类占比突变、消费额异常 | 0.40 |
| **RuleDetector** | 硬规则（否决权）+ 软规则 | 单笔大额(>¥10,000)、深夜消费(23:00-05:00)、用户自定义规则 | 0.40 |
| **PatternDetector** | 滑动窗口 + 同比环比 | 消费频率突变、陌生商户识别、订阅续费异常 | 0.20 |
| **FraudDetector** | 时间窗口统计 + 频率分析 | 小额试探攻击、快刷检测、相同金额重复扣款 | 0.15 |

#### 7.1.3 混合融合算法

```
final_score = max(
    max(hard_rule_scores),        # 硬规则直接穿透（否决权）
    Σ(w_i × score_i) / Σw_i       # 软规则加权平均
)
```

#### 7.1.4 严重度分级

| final_score | severity | 动作 |
|:---:|---------|------|
| ≥ 0.8 | 🔴 high | WebSocket 即时推送 + 移动端系统通知 |
| ≥ 0.5 | 🟡 medium | 记录但不推送 |
| < 0.5 | 🟢 low | 仅记录 |

#### 7.1.5 冷启动防护

新用户数据不足时（某分类 < 5 条记录），Z-Score 降级为全局基线，`fill_nan(0.0)`：

```python
pl.when(pl.col("cat_count") >= 5)
  .then((amount - mean) / std)
  .otherwise(0.0)
  .fill_nan(0.0)
```

### 7.2 数据脱敏引擎

#### 7.2.1 三级商户泛化

```
优先级1: 前缀词典精确匹配
  "美团外卖-xx麻辣烫" → "外卖平台-餐饮商户"
  "滴滴出行-行程单"   → "出行平台-打车"

优先级2: 关键词行业分类
  "xx饭店" → "某餐饮商户"
  "xx超市" → "某零售商户"

优先级3: 正则兜底
  其余 → "未知商户(已脱敏)"
```

#### 7.2.2 脱敏策略

| 原始数据 | 处理方式 | 发送给 LLM 的形式 |
|----------|---------|------------------|
| 交易金额 | 保留 | `¥42.50` |
| 商户全名 | 三级泛化 | `"外卖平台-餐饮商户"` |
| 银行卡号 | 完全移除 | 不进入 LLM 上下文 |
| 真实姓名 | 移除 | 不进入 LLM 上下文 |
| 精确地址 | 模糊化 | `"北京市"` |
| 手机号 | 正则替换 | `[手机号已隐藏]` |
| 身份证号 | 正则替换 | `[身份证已隐藏]` |
| 账户余额 | 完全移除 | 不进入 LLM 上下文 |

#### 7.2.3 Tools 双重防线

Pydantic AI Agent 注册的工具函数内部强制执行：
1. SQL 层面：只执行 `GROUP BY / COUNT / SUM` 聚合查询
2. 输出层面：`DataSanitizer.sanitize_aggregated_for_tool()` 过滤

### 7.3 LLM 集成

#### 7.3.1 架构

```
用户触发(chat) / 自动触发(异常解读)
  → llm_service.py (ChatManager / AnomalyExplainer)
  → Prompt Builder (System + Context 组装)
  → DataSanitizer (preprocess.py) 强制脱敏
  → httpx.AsyncClient(trust_env=False) → DeepSeek API
  → Pydantic Model 校验响应
  → 失败 → Jinja2 离线模板降级
```

#### 7.3.2 调用控制

| 维度 | 策略 |
|------|------|
| 异常解读 | 自动触发（用户可关闭），≤ 10次/小时 |
| 智能对话 | 手动触发，≤ 30次/小时 |
| Token 控制 | 上下文 ≤ 20条交易 + 近3个月统计 |
| 离线降级 | DeepSeek 不可用时自动切换 Jinja2 模板 |

#### 7.3.3 降级文案示例

```
🔴 检测到高危异常消费

规则命中：
- 单笔消费 ¥15,000.00 超过了大额交易阈值。
  请确认该笔消费是否为本人操作。

建议：
- 定期检查账单，关注异常支出
- 为常用分类设置预算上限
- 大额消费前三思，避免冲动购物
```

---

## 8. API 接口文档

Base URL: `http://localhost:8000/api/v1`

### 8.1 交易（Transactions）

| 方法 | 路径 | 请求体/参数 | 说明 |
|------|------|-----------|------|
| `POST` | `/transactions` | `TransactionCreate` | 创建交易（自动去重） |
| `GET` | `/transactions` | `?page=1&page_size=20&search=xx&type=expense&category_id=1&start_date=&end_date=` | 分页列表+筛选 |
| `GET` | `/transactions/:id` | — | 交易详情 |
| `PUT` | `/transactions/:id` | `TransactionCreate` | 更新交易 |
| `DELETE` | `/transactions/:id` | — | 删除交易 |

### 8.2 分类（Categories）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/categories` | 分类树（系统预置+自定义） |
| `POST` | `/categories` | 创建自定义分类 |
| `DELETE` | `/categories/:id` | 删除自定义分类（系统分类禁止） |

### 8.3 导入（Imports）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/imports/upload` | multipart 上传 CSV/OFX/QIF 文件 |
| `GET` | `/imports` | 导入历史列表 |

支持 source_type: `alipay`, `wechat`, `bank_csv`, `bank_ofx`, `bank_qif`

### 8.4 检测（Detection）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/detection/run` | 手动触发全量检测 |
| `GET` | `/detection` | 检测结果列表（`?severity=high`） |
| `GET` | `/detection/:id` | 单条结果详情 |
| `PATCH` | `/detection/:id/read` | 标记已读 |

### 8.5 预算（Budgets）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/budgets` | 创建预算 |
| `GET` | `/budgets` | 预算列表（含进度百分比） |
| `DELETE` | `/budgets/:id` | 删除预算 |

### 8.6 LLM

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/llm/explain` | 解读异常（`{"detection_id":3}`） |
| `POST` | `/llm/chat` | 智能对话（`{"message":"本月花了多少？"}`） |
| `GET` | `/llm/usage` | 用量统计 |

### 8.7 规则与数据管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/rules` | 检测规则列表 |
| `POST` | `/rules` | 创建规则 |
| `PUT` | `/rules/:id` | 更新规则（含启停） |
| `DELETE` | `/rules/:id` | 删除规则 |
| `POST` | `/rules/seed-defaults` | 初始化3条默认规则 |
| `GET` | `/rules/data/stats` | 数据库统计 |
| `GET` | `/rules/data/export` | 导出CSV |
| `POST` | `/rules/data/clear-detections` | 清空检测结果 |
| `POST` | `/rules/data/clear-all` | 清空全部数据 |

### 8.8 WebSocket

| 路径 | 事件类型 |
|------|---------|
| `ws://localhost:8000/api/v1/ws` | `detection.alert`, `budget.warning`, `import.done`, `system.health` |

---

## 9. 前端页面设计

### 9.1 路由表

| 路由 | 页面 | 功能 |
|------|------|------|
| `/dashboard` | Dashboard | 4 指标卡片 + 30天趋势折线 + 分类饼图 |
| `/transactions` | Transactions | 列表 + 搜索 + 筛选 + 分页 |
| `/import` | Import | 📁 文件导入（5种格式）+ ✏️ 手动录入 + 批量录入 |
| `/detection` | Detection | 异常列表 + 严重度筛选 + 一键检测 |
| `/reports` | Reports | 月度收支柱状图 + 每日趋势 + TOP8饼图 + 异常分布 |
| `/budget` | Budget | 创建/删除 + 进度条 + 超预算预警 |
| `/chat` | Chat | DeepSeek 实时对话 + 离线提示 |
| `/settings` | Settings | 分类管理 + 检测规则CRUD + 数据管理 |

### 9.2 响应式断点

| 断点 | 布局变化 |
|------|---------|
| `< 640px` (sm) | 卡片 1 列，表格横向滚动 |
| `640-1024px` | 卡片 2 列 |
| `>= 1024px` (lg) | 卡片 4 列，侧边栏常驻 |
| 移动端 | 侧边栏 → Sheet/Drawer 抽屉 |

### 9.3 状态管理架构

```
TanStack Query (服务端缓存)
  ├── transactions (分页列表)
  ├── categories (分类树)
  ├── detection (异常结果)
  ├── budgets (预算+进度)
  ├── rules (检测规则)
  └── data-stats (数据库统计)

Zustand (客户端状态)
  ├── alertStore (WebSocket告警)
  └── uiStore (侧边栏开关)

URL State (React Router)
  └── 筛选参数同步到 query string
```

---

## 10. 性能与安全

### 10.1 性能优化

| 策略 | 实现 |
|------|------|
| **Polars DataFrame** | 特征工程使用 Polars（Rust 内核），10万行 < 1秒 |
| **DuckDB OLAP** | 聚合查询使用 DuckDB，比 SQLite 原生快 10-100x |
| **SQLite WAL 模式** | 读写并发不阻塞 |
| **前端分页** | 每页 20 条，TanStack Query 缓存 |
| **React 代码分割** | Vite 自动 code-splitting（后续可加 `React.lazy`） |
| **LLM Token 控制** | 上下文限制 20 条交易 + 3 个月统计，单次返回 ≤ 1024 tokens |

### 10.2 安全措施

| 层级 | 措施 |
|------|------|
| **数据存储** | SQLite 本地文件，不联网同步 |
| **LLM 脱敏** | `DataSanitizer` 强制过滤银行卡/身份证/余额/姓名 |
| **API 密钥** | `.env` 文件，已 gitignore，不进入版本控制 |
| **CORS** | FastAPI 中间件限制 origin |
| **SQL 注入** | SQLAlchemy ORM 参数化查询 |
| **幂等去重** | SHA256 哈希 + UNIQUE 约束，防重复导入 |
| **商户泛化** | 发送给 LLM 前三级泛化，不泄露真实商户 |

### 10.3 数据隐私

- 所有消费数据仅存储在本地 SQLite 文件中
- 调用 DeepSeek API 前执行 `DataSanitizer.sanitize_for_llm()` 强制脱敏
- 注册给 LLM Agent 的工具函数内部双重防线（SQL 聚合 + 输出过滤）
- 用户可随时通过设置页「清空全部数据」删除所有本地数据

---

## 11. 测试策略

### 11.1 测试覆盖

| 测试文件 | 测试范围 | 用例数 |
|---------|---------|:-----:|
| `test_transactions.py` | 交易CRUD + 去重 + 筛选 + 分类 + 预算API | 14 |
| `test_detection.py` | 检测引擎 + 导入 + 规则 + 脱敏 | 17 |

### 11.2 运行测试

```bash
cd backend
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

### 11.3 测试架构

```
conftest.py
  ├── Module-level SQLite :memory: engine
  ├── Per-test session with seed data
  └── FastAPI TestClient with dependency override
```

---

## 12. 部署指南

### 12.1 本地开发

```bash
# 终端 1 — 后端
cd finwatch/backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
cp ../.env.example .env        # 编辑 .env 填入 DEEPSEEK_API_KEY
uvicorn app.main:app --reload --port 8000

# 终端 2 — 前端
cd finwatch/frontend
npm install
npm run dev                    # http://localhost:5173
```

### 12.2 部署到 GitHub

```bash
cd finwatch
git init
git add -A
git commit -m "Initial commit"

# 创建 GitHub 仓库后
git remote add origin https://github.com/YOUR_USERNAME/finwatch.git
git branch -M main
git push -u origin main
```

推送后 GitHub Actions 自动运行：
- `backend-tests`: pytest 全部测试
- `frontend-build`: TypeScript 检查 + Vite 构建
- `docker-build`: Docker Compose 构建验证

### 12.3 部署到 Android 手机

**前置条件：** Android Studio + JDK 17 + Android SDK

```bash
cd finwatch/frontend

# 1. 构建前端
npm run build

# 2. 同步 Capacitor
npx cap sync

# 3. 打开 Android Studio 构建 APK
npx cap open android
```

在 Android Studio 中：
1. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
2. APK 位于 `frontend/android/app/build/outputs/apk/debug/app-debug.apk`
3. 通过 USB 或 AirDroid 传输到手机安装

> **注意：** APK 中的后端地址为 `http://10.0.2.2:8000`（Android 模拟器映射到宿主机 localhost）。真机使用时需修改 `capacitor.config.ts` 中的 `server.url` 为电脑的局域网 IP。

### 12.4 部署到 iOS 手机

**前置条件：** macOS + Xcode + Apple Developer 账号

```bash
cd finwatch/frontend

# 1. 构建前端
npm run build

# 2. 添加 iOS 平台
npx cap add ios

# 3. 同步
npx cap sync

# 4. 打开 Xcode
npx cap open ios
```

在 Xcode 中：
1. 选择目标设备（iPhone 或模拟器）
2. **Product → Archive** 生成 IPA
3. 通过 TestFlight 或直接安装到设备

### 12.5 部署为桌面应用（Electron）

```bash
cd finwatch/frontend

# 开发模式
npm run electron:dev

# 打包为可分发的桌面应用
npm run electron:dist
# 输出: frontend/dist-electron/
#   - FinWatch Setup.exe (Windows)
#   - FinWatch.dmg (macOS)
#   - FinWatch.AppImage (Linux)
```

### 12.6 Docker 一键部署

```bash
cd finwatch

# 创建 .env 文件
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 启动
docker compose up -d

# 访问
# 前端: http://localhost:5173
# 后端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 12.7 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./finwatch.db` | 数据库连接（Docker 用 PostgreSQL） |
| `DEEPSEEK_API_KEY` | (空) | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `LLM_ENABLED` | `false` | 是否启用 LLM 功能 |
| `DEBUG` | `true` | SQLAlchemy 调试日志 |
| `DETECTION_SCHEDULE_HOUR` | `2` | 全量检测时间（凌晨2点） |
| `DETECTION_INCREMENTAL_MINUTES` | `30` | 增量检测间隔 |

---

## 附录

### A. Git 提交历史

```
88afe65 fix: DeepSeek v4 model + proxy bypass
f7b938a feat: Phase 2 - LLM integration, PatternDetector, data sanitizer, Chat & Reports
88f5579 feat: rules CRUD, data management, manual entry
ca6fd4c fix: accurate skipped_count in import dedup
7705791 fix: Python 3.8 compatibility - Optional/List/Dict typing
130e117 feat: Capacitor Android integration + frontend build
3423d9b feat: FinWatch Phase 1 backbone
f1bc166 feat: project scaffolding - backend config and dependencies
```

### B. 系统依赖

| 软件 | 最低版本 | 用途 |
|------|---------|------|
| Python | 3.8+ | 后端 |
| Node.js | 18+ | 前端 |
| Android Studio | Hedgehog+ | APK 打包 |
| Xcode | 15+ | iOS 打包 |
| Docker | 24+ | 容器化 |
| Git | 2.40+ | 版本控制 |

### C. 后续路线图

- [ ] PatternDetector 增强：时序分解 + 周期性建模 + 连锁异常关联
- [ ] 实际多用户登录系统（JWT/OAuth）
- [ ] 通知渠道扩展（邮件/钉钉/企业微信）
- [ ] i18n 国际化（英文版本）
- [ ] 数据可视化大屏模式
