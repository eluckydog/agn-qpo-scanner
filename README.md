# AGN QPO Scanner

> Hilbert 瞬时相位从天体中滤出了什么？38 个 TESS sector，229,514 个光变点，答案：没有 1900 秒周期。瞬态 QPO 被排除了，但方法本身通过了所有检验。

活动星系核（AGN）光变中是否存在准周期振荡（QPO）是天体物理学的开放问题——可能指向双黑洞轨道、吸积盘颤动、或喷流进动。我们用来自太阳周期建模的 **Hilbert 瞬时相位方法** 在 ZTF 和 TESS 数据中做了一次全盲扫描。

**核心结果**：7 个已知候选源在 ZTF 中全部未确认；1ES 1927+654 的 1900s QPO 在 6 年 TESS 数据中完全消失。这是瞬态信号的排除边界，不是否定。

## 结构

```
agn-qpo-scanner/
├── README.md                 ← 本项目
├── skill/                    ← OpenClaw Skill（可安装）
│   ├── SKILL.md              ← 触发规则与用法
│   └── scripts/
│       └── agn_beats.py      ← CLI（search/download/analyze/batch/window/list）
├── code/                     ← 核心分析管线
│   ├── agn_qpo_analyzer.py   ← QPO 分析引擎：LS周期图 + MC显著性 + Rayleigh检验 + von Mises拟合
│   ├── query_ztf.py          ← ZTF TAP 查询 → CSV 光变
│   ├── window_diagnostic.py  ← 窗口函数诊断工具
│   └── batch_analysis.py     ← 批量 TESS sector 分析
├── data/
│   ├── lc/                   ← ZTF CSV 光变（7个候选源）
│   └── tess_lc/              ← TESS TPF 缓存（仅含一个 demo Sector 16）
├── docs/                     ← 分析报告与 task artifacts
└── results/                  ← 汇总 JSON + 诊断结果
```

## 跨域映射

| 太阳物理（U(1) 模型） | AGN QPO（本项目） |
|----------------------|-------------------|
| 太阳黑子数 → U(1) 圆相位 | AGN 光变 → Hilbert 瞬时相位 |
| 耀斑发生率 ~ von Mises | 周期折叠强度 ~ Rayleigh Z |
| 太阳旋转调制 | 吸积盘热斑轨道调制 |
| 相位滞后 Φ_lag=142.9° | 候选周期相位折叠 |
| Monte Carlo 显著性检验 | 同左 |

## 为什么是一个仓库

七个 ZTF 候选源 + 一个 TESS 目标的全面扫描是一次完整调查，不是零散脚本。方法（Hilbert + LS + Rayleigh）在不同源间可复用，统一放在同一管线中。分开则每个子模块缺少独立生态。

## 快速开始

```bash
# 1. 列出已知候选源
python skill/scripts/agn_beats.py list

# 2. 搜索一个源
python skill/scripts/agn_beats.py search --target 1ES1927 --source tess

# 3. 下载新源的 TESS 数据
python skill/scripts/agn_beats.py download --ra 291.93 --dec 65.63 --name "1ES1927+654"

# 4. 全量批次分析
python skill/scripts/agn_beats.py batch
```

### 安装为 OpenClaw Skill

将 `skill/` 链接或复制到 `~/.qclaw/skills/agn-beats/` 即可。触发关键词：AGN、QPO、周期振荡、blazar、TESS 光变。

## 数据

- **ZTF 光变（data/lc/）**：7 个候选源，来自 IRSA TAP，CSV 格式
- **TESS TPF（data/tess_lc/）**：1ES 1927+654，41 sectors（仅 sector 16 demo 含在仓库中）
  - 完整数据：`python skill/scripts/agn_beats.py download --ra 291.93 --dec 65.63`

## 结果摘要

| 轮次 | 源 | 数据 | 结论 |
|------|-----|------|------|
| ZTF 扫描 | 7 个候选 | 301-1151 点 | ❌ 全部未确认（小样本/红噪声） |
| TESS 批次 | 1ES 1927+654 | 38 sectors, 229K 点 | ❌ 1900s QPO 消失 |
| 方法对照 | — | — | ✅ 1800s 采样频率伪影正确标出 |

**窗口函数发现**：ZTF 中 7/7 源共有 57-58d 月相周期（非天文物信号）。
**阳性对照**：TESS 1800s（30min FFI 采样率）Rayleigh Z = 332 — 方法明确区分物理信号与采样伪影。

## 许可证

MIT
