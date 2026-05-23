# AGN Beats — 活动星系核准周期振荡检测 Skill

检测活动星系核光学光变中的准周期振荡（QPO），支持 ZTF 和 TESS 数据源。基于 Hilbert 瞬时相位 + Lomb-Scargle + Rayleigh 检验的交叉验证管线。

## 触发关键词

- 「AGN」「QPO」「准周期振荡」「活动星系核」「光变」「blazar」「blazar 周期」
- 「TESS 光变」「下载 TESS」「TESS 测光」
- 「1ES 1927」「PG 1302」「OJ 287」「3C 273」等已知候选源
- 任何涉及「天文/天体物理 + 周期搜索/光变分析」的请求

## 环境依赖

- Python 3: astropy, numpy, scipy
- 联网（MAST TessCut API, IRSA TAP）

## 核心工作流

### 1. 搜索 AGN QPO（一键）

```
python scripts/agn_beats.py search --target TARGET_NAME [--source ztf|tess]
```

TARGET_NAME 可以是：`1ES1927+654`, `3C273`, `OJ287`, `BL Lac`, `M81`, `PG1302` 等。

### 2. 下载 TESS 数据

```
python scripts/agn_beats.py download --ra RA --dec DEC [--name TARGET_NAME]
```

从 MAST TessCut API 下载所有覆盖某个天区的 TESS sector 光变数据。

### 3. 分析单个 sector

```
python scripts/agn_beats.py analyze --fpath PATH_TO_FITS [--target-period SECONDS]
```

从 TPF 提取光变曲线 → 天光扣除 → QPO 管线（LS + MC + Rayleigh + von Mises）。

### 4. 批次分析

```
python scripts/agn_beats.py batch --dir DATA_DIR
```

批量分析一个目标的所有 TESS sector，输出汇总。

### 5. 窗口函数诊断

```
python scripts/agn_beats.py window --t-file TIMES_FILE
```

分析 ZTF/TESS 等非均匀采样的窗口函数。

## 数据目录

默认数据缓存在 `projects/agn-beats/data/` 下。

## 已知候选源

| 源名 | RA | DEC | 类型 |
|------|----|-----|------|
| 1ES 1927+654 | 291.93 | +65.63 | AGN，已知 ~1900s QPO |
| PG 1302-102 | 196.28 | -10.44 | 类星体，~5.2yr QPO 候选 |
| OJ 287 | 133.70 | +20.23 | 耀变体，~12yr 周期 |
| 3C 273 | 187.28 | +2.05 | 类星体 |
| BL Lac | 330.68 | +42.28 | 耀变体 |
| Mrk 421 | 166.11 | +38.21 | TeV 耀变体 |
| PKS 2155-304 | 329.72 | -30.23 | TeV 耀变体 |
| 1ES 1959+650 | 300.00 | +65.15 | TeV 耀变体 |
| M81* | 148.89 | +69.07 | 塞弗特星系 |
| PSO J334 | 334.12 | +22.50 | 已知 ~1yr QPO |

## 输出格式

分析结果返回 JSON，包含：
- `sector` / `n_pts` / `baseline_days`
- `target_{period}_Z` / `target_{period}_p` — Rayleigh 检验
- `ls_period_days` / `ls_power` — LS 周期图
- `mc_p` / `sig_95` / `sig_99` — MC 显著性
- `verdict` — NO SIGNAL / MARGINAL / QPO CANDIDATE
- `candidates` — 多个候选周期的交叉验证表
