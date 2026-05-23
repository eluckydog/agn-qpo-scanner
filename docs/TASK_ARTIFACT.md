# AGN QPO Scan - 2026-05-23 任务总结

**启动时间**: 15:44 | **完成时间**: 16:15 | **耗时**: ~30 分钟

## 做了什么

1. 建项目目录、初始化 git
2. 写理论框架（dimensions/01_agn_qpo.md）
3. 写 ZTF 查询模块（query_ztf.py v2，修复 VOTable 命名空间解析）
4. 写 QPO 分析管线（agn_qpo_analyzer.py：LS + MC 显著性 + Hilbert 相位 + Rayleigh 检验 + von Mises 拟合）
5. 定义 8 个已知 AGN QPO 候选源
6. 拉取 7 个源的 ZTF 光变曲线（~1.1MB，Mrk 421 不在 ZTF 覆盖）
7. 全线 QPO 扫描

## 核心发现（负发现也是发现）

- **没有确认任何显著 QPO**——ZTF 7.5年窗口的窗口函数在~1363d 产生强伪影
- **方法验证成功**：LS+MC 显著性能正确拒绝（p=0.9+）而裸相位折叠会假阳性（Z=129）
- **1ES 1959+650** 和 **PSO J334** 有边缘迹象，但数据不足以确认

## 文件结构

```
projects/agn-qpo/
├── dimensions/01_agn_qpo.md           # 理论
├── code/
│   ├── candidates.py                  # AGN QPO候选列表
│   ├── query_ztf.py                   # ZTF光变曲线下载 (v2)
│   ├── agn_qpo_analyzer.py            # QPO分析管线
│   ├── run_pipeline.py                # 主调度器
│   ├── fetch_all.py                   # 批量拉取
│   └── run_all_analysis.py            # 分析脚本
├── data/lc/*.csv                      # 7个源的ZTF光变（~1.1MB）
├── docs/SCAN_RESULTS.md               # 扫描结果
└── results/                           # 结果缓存
```
