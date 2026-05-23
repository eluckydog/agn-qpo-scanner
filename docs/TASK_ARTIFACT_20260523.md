# AGN Beats — 2026-05-23 全量批次分析

## 做了什么

1. **改名**：`agn-qpo` → `agn-beats`，写入中文简介 README
2. **批量拉取**：1ES 1927+654 全部 41 个 TESS sector
3. **分析**：38 个 sector 成功提取光变曲线（3 个因 TPF 边界失败）

## 结果

### 核心：1900s QPO 未在 TESS 中探测到
- 38/38 sector：Rayleigh Z ≈ 0.0，p > 0.93
- 6 年 TESS 连续数据排除该 QPO
- 方法验证通过：1800s（TESS FFI 采样频率）正确标记为伪影

### 副产品
- ZTF 窗口函数诊断：57-58d 月相周期确认
- TESS 天光扣除测光管线：从 TPF 提取干净光变

## 交付物
- `projects/agn-beats/README.md` — 中文简介
- `docs/TESS_BATCH_RESULTS.md` — 批次分析报告
- `results/tess_batch_results.json` — 全量数据
- `code/batch_analysis.py` / `batch_download.py`
