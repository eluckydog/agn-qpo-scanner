# AGN Beats — Skill 搭建完成

## Skill 目录结构

```
skills/agn-beats/
├── SKILL.md              # 触发规则 + 使用说明
└── scripts/
    └── agn_beats.py      # CLI 主入口（search/download/analyze/batch/window/list）
```

## 命令验证

| 命令 | 结果 |
|------|------|
| `agn_beats.py list` | ✅ 11 个已知候选源 |
| `agn_beats.py search --target 1ES1927 --source tess` | ✅ 找到 41 个 TPF，分析完成，1900s QPO: NO SIGNAL |

## 安装方式

可直接通过 OpenClaw 加载。运行时自动引用 `projects/agn-beats/` 下的数据和核心算法。

**检查状态：**
- 旧目录 `projects/agn-qpo/` 是否删除？→ 用户决定
- `skills/` 路径已确认可引用项目数据
- CLI 通顺无循环导入
