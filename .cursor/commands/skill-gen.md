---
description: 自主开发新 Skill 的完整工作流。当用户要求创建、开发或生成新的 skill 时触发。
---

# Skill Generator Workflow

## 阶段 1：需求分析（Research）
1. 询问用户：这个 skill 要解决什么问题？
2. 收集 3-5 个具体使用场景（如：'旋转PDF'、'填写表单'）
3. 评估需求完整性（0-10 分）
4. IF score < 7 THEN 要求用户补充信息（目标、预期结果、约束条件）

**完成标准**：需求评分 ≥ 7 分，输出 requirements.json。

// turbo
## 阶段 2：资源规划（Planning）
1. 基于需求场景，分析需要的 scripts/、references/、assets/ 结构
2. 确定依赖的外部库（如 pypdf、openpyxl、pandoc）
3. 生成资源清单（resource_plan.json）
4. FOR EACH script IN plan: 确定脚本语言（Python/Node.js）和核心功能

**完成标准**：资源清单完整且可执行。

// turbo
## 阶段 3：骨架生成（Scaffolding）
**前置检查**：确认 `scripts/init_skill.py` 存在
1. 运行 `python scripts/init_skill.py <skill-name> --path ./skills`
2. 验证目录结构（SKILL.md、scripts/、references/、assets/）
3. IF directory_missing THEN 重新运行 init_skill.py

**完成标准**：目录结构验证通过。

// turbo
## 阶段 4：核心开发（Implementation）
1. 根据 resource_plan.json 编写 scripts/ 中的 Python/JS 脚本
2. FOR EACH script: 测试至少 1 个样本（运行并验证输出）
3. 编写 SKILL.md frontmatter（name + description）
4. 编写 SKILL.md body（使用场景 + workflow + 依赖说明）
5. IF references/ 需要文档：创建并引用（如 forms.md、reference.md）

**质量指标**：脚本通过测试，SKILL.md description 完备。

// turbo
## 阶段 5：验证打包（Validation）
**前置检查**：确认 `scripts/package_skill.py` 存在
1. 运行 `python scripts/package_skill.py ./skills/<skill-name>`
2. READ validation_output -> PARSE errors
3. IF errors_found THEN FIX issues -> RETRY package_skill.py
   常见错误：
   - YAML 格式错误：检查 frontmatter 的 `---` 标记
   - 描述缺失：补充 description 字段
   - 文件结构不完整：确认 SKILL.md 存在
4. ENSURE output_file=<skill-name>.skill exists

**完成标准**：package_skill.py 返回 success。

## 阶段 6：生产测试（Production Test）
1. 要求用户提供 1 个真实使用场景
2. 在新对话中加载生成的 .skill 文件
3. 执行用户场景并收集反馈
4. IF feedback_negative THEN 返回阶段 4 修复问题（保留阶段 1-3 和 5 的成果）
5. IF feedback_positive THEN 标记为生产就绪