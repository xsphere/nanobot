# 行业轮动 + 多因子择时：基于 nanobot 的 CSE 简化试点系统设计说明书（System Design Specification）

## 1. 文档信息

- **文档类型**：系统设计说明书（SDS）
- **系统名称**：EvoQuant-CSE-Pilot
- **技术底座**：nanobot（OpenClaw 简化架构）
- **版本**：v1.0（试点版）
- **目标读者**：量化研究、Agent 工程、平台工程、风控/合规

---

## 2. 设计目标与范围

## 2.1 设计目标
构建一个可复现、可解释、可审计的“行业轮动 + 多因子择时”自进化研究系统，实现：
1. 夜间自动进化（生成、评估、变异、交叉、筛选）。
2. 白天人工审阅与策略入库。
3. 全流程风险闸门与审计追踪。

## 2.2 业务边界（In Scope）
- 行业层级资产（行业指数/行业 ETF）。
- 日频/周频研究与调仓。
- 离线回测与影子组合模拟。

## 2.3 非目标（Out of Scope）
- 高频/低延迟撮合优化。
- 个股级 alpha 全覆盖。
- 全自动真实下单（首期不直连交易柜台）。

---

## 3. 总体架构设计

## 3.1 分层架构
系统采用“**Agent 控制层 + Tool 执行层 + Memory 记忆层 + Governance 治理层**”四层架构：

1. **Agent 控制层**
   - Planner Agent：多样化策略草图生成。
   - Coder Agent：策略代码模板化生成与槽位化标注。
   - Evaluator Agent：回测执行、指标计算、归因分析。
   - Mutator Agent：按优先级执行受控变异。
   - Risk Agent：风控、合规、泄露/未来函数检查。

2. **Tool 执行层**
   - `quant_data`：数据读取与质量校验。
   - `quant_backtest`：统一回测引擎入口。
   - `quant_eval`：指标矩阵与鲁棒性评估。
   - `quant_riskcheck`：硬约束/合规扫描。

3. **Memory 记忆层**
   - Local Memory：任务内失败路径与禁用参数区间。
   - Global Memory：Alpha Zoo、Hall of Shame、Meta Rules。

4. **Governance 治理层**
   - 审批流：候选策略人工审核。
   - 审计流：记录 lineage、变异理由、发布动作。
   - 回滚机制：异常时回退到稳定父代策略。

## 3.2 逻辑架构图（文字版）
`任务配置 -> Planner -> Coder -> Backtest/Eval -> Mutation/Crossover -> Risk Gate -> Top-K Candidate -> Human Review -> Memory Distillation`

---

## 4. 核心设计：CSE 进化引擎

## 4.1 策略个体标准模型
每个策略个体 `StrategyGenome` 由以下槽位组成：
- `data_slot`：特征对齐、缺失处理、中性化。
- `alpha_slot`：行业轮动分数与择时分数计算。
- `portfolio_slot`：行业权重优化与约束。
- `risk_slot`：仓位上限、回撤控制、风格暴露控制。
- `execution_slot`：调仓频率、交易成本与滑点模型。

## 4.2 初始化设计（Diversified Planning）
每次任务初始化至少产生 4 条异构路线：
- 宏观驱动（利率/通胀/信用）
- 基本面驱动（盈利预期/估值偏离）
- 量价驱动（动量/波动/拥挤度）
- 事件驱动（政策/供需冲击）

每条路线必须产出：
1. 假设描述（NL）
2. 因子表达式（DSL）
3. 可运行代码模板（Python）

## 4.3 适应度函数（Multi-objective Fitness）
定义：

`fitness = w1*DSR + w2*RankIC + w3*RegimeRobustness - w4*Turnover - w5*MDD`

### 约束条件（硬闸门）
- 任一市场验证集失效 -> 淘汰。
- MDD 超阈值 -> 淘汰。
- 泄露/未来函数检测失败 -> 淘汰。

## 4.4 优先级受控变异（Priority-guided Mutation）
归因驱动映射：
- DSR 偏低 -> 变异 `alpha_slot`
- MDD 偏高 -> 变异 `risk_slot`
- Turnover 偏高 -> 变异 `execution_slot`
- 风格偏移 -> 变异 `portfolio_slot`

### 变异策略
- 参数微调：阈值、窗口长度、衰减系数。
- 逻辑替换：因子函数替换、信号融合方式切换。
- 局部重构：仅重写目标槽位，其他槽位冻结。

## 4.5 组合交叉（Compositional Crossover）
- 从父代 A、B 选择互补槽位生成子代 C。
- 交叉后执行接口一致性检查（输入/输出 schema）。
- 不通过静态检查的子代直接丢弃。

## 4.6 层级记忆与蒸馏
- Local Memory：记录本任务失败原因（如“震荡市换手过高导致成本侵蚀”）。
- Global Memory：提炼元规则（如“高波动 regime 下，波动抑制项权重应上调”）。
- 蒸馏周期：每次任务结束时进行一次规则提炼与去重。

---

## 5. 数据架构设计

## 5.1 数据域
1. 市场行情域：行业指数/ETF OHLCV。
2. 宏观因子域：利率、通胀、信用利差。
3. 资金行为域：成交额、资金流向、ETF 申赎。
4. 基本面聚合域：行业估值、盈利修正。

## 5.2 数据分层
- **Raw Layer**：原始落地，保留源格式。
- **Clean Layer**：统一时区、去异常、缺失填补。
- **Feature Layer**：标准化因子矩阵与标签。
- **Research Mart**：回测可直接消费的数据视图。

## 5.3 数据质量与时点控制
- 时点对齐：禁止使用未来可见数据。
- 质量阈值：缺失率、跳变率、延迟 SLA。
- 校验策略：任务启动前执行数据完整性检查。

---

## 6. 模块设计说明

## 6.1 Planner 模块
**输入**：研究主题、市场范围、约束配置。  
**输出**：多路线策略草图（含假设 + 因子 DSL）。  
**关键逻辑**：通过 prompt template 强制多样化采样。

## 6.2 Coder 模块
**输入**：策略草图 + 代码模板。  
**输出**：槽位化策略代码与配置。  
**关键逻辑**：
- 模板优先，避免自由生成导致不可执行。
- 生成后跑静态 lint/schema 校验。

## 6.3 Backtest/Evaluator 模块
**输入**：策略代码、数据切片、成本参数。  
**输出**：指标矩阵 + 归因报告 + 诊断标签。  
**关键逻辑**：
- 统一回测协议（Train/Valid/Test + Walk-forward）。
- 输出结构化诊断结论供 Mutator 消费。

## 6.4 Mutator/Crossover 模块
**输入**：诊断标签 + 策略族群。  
**输出**：下一代策略族群。  
**关键逻辑**：
- 按优先级定向变异目标槽位。
- 交叉后执行兼容性/可执行性检查。

## 6.5 Risk Gate 模块
**输入**：候选策略与评估结果。  
**输出**：通过/拒绝 + 原因。  
**关键逻辑**：
- 未来函数扫描。
- 风险约束检查（MDD、换手、集中度）。
- 合规规则校验。

## 6.6 Memory 模块
**输入**：任务过程轨迹、最终候选、失败样本。  
**输出**：更新后的 Alpha Zoo / Hall of Shame / Meta Rules。  
**关键逻辑**：
- 相似策略检索热启动。
- 失败模式去重与标签化。

---

## 7. 接口与契约设计

## 7.1 内部对象契约（建议）

### `TaskConfig`
- `markets: list[str]`
- `train_range, valid_range, test_range`
- `cost_model`
- `risk_limits`
- `evolution_params`

### `StrategyGenome`
- `id, parent_ids, generation`
- `slots: {data, alpha, portfolio, risk, execution}`
- `metadata: hypothesis, lineage, tags`

### `EvalReport`
- `metrics: {DSR, MDD, RankIC, Turnover, ...}`
- `regime_breakdown`
- `attribution_summary`
- `diagnosis_tags`

## 7.2 Tool 接口（建议函数签名）
- `quant_data.load(config) -> DataBundle`
- `quant_backtest.run(strategy, data, cfg) -> BacktestResult`
- `quant_eval.evaluate(bt_result) -> EvalReport`
- `quant_riskcheck.scan(strategy, report, limits) -> RiskDecision`

---

## 8. 流程编排设计（Nightly Evolution）

## 8.1 主流程
1. 读取 `TaskConfig`。
2. Planner 生成初始种群。
3. Coder 生成槽位化策略。
4. Evaluator 批量回测并产出诊断。
5. Mutator/Crossover 生成下一代。
6. 达到终止条件后进入 Risk Gate。
7. 输出 Top-K 候选并提交人工审阅。
8. Memory Distillation 更新知识库。

## 8.2 终止条件
- 达到最大代数。
- 连续 N 代最优 fitness 无显著提升。
- 超过夜间时间窗口。

## 8.3 失败处理
- 子任务失败重试（幂等）。
- 单个策略异常不阻塞全局任务。
- 任务级失败触发告警并输出失败快照。

---

## 9. 部署与运行设计

## 9.1 环境分层
- Dev：功能开发与单元测试。
- Staging：全链路回放与压力测试。
- Prod-Research：夜间进化生产运行（不下实盘单）。

## 9.2 调度策略
- 每日收盘后触发夜间任务。
- 支持按市场时区分批执行。
- 批任务最大运行时长可配置。

## 9.3 资源与扩展
- 回测计算与 LLM 推理分离部署。
- 通过队列并行评估个体。
- 高负载时降级策略：减少代数/缩小种群。

---

## 10. 可观测性与运维设计

## 10.1 日志
- 任务日志：状态、耗时、失败原因。
- 个体日志：fitness、变异点、淘汰标签。
- 审计日志：人工审批与发布操作。

## 10.2 指标监控
- 任务级：成功率、平均耗时、重试率。
- 策略级：Top-K 稳定性、约束触发率。
- 风险级：违规拦截次数、可疑策略比例。

## 10.3 告警
- 任务超时。
- 数据质量未达标。
- 候选策略全部被风控拒绝。

---

## 11. 安全、合规与治理

## 11.1 安全控制
- 代码执行沙箱隔离。
- 依赖白名单与文件访问限制。
- Prompt/工具调用审计。

## 11.2 合规控制
- 防未来函数、防数据泄露。
- 交易约束策略化（仓位/杠杆/行业集中度）。
- 审批前禁止“可发布”标记。

## 11.3 版本与回滚
- 每个候选策略必须可追溯到父代与配置版本。
- 上线失败可一键回滚到稳定版本。

---

## 12. 验收设计

## 12.1 验收门槛
- 双市场验证通过。
- 风险硬约束全部通过。
- 关键指标较基线有统计意义提升。

## 12.2 验收产物
1. Top-K 策略包（代码/配置/报告）。
2. lineage 图与变异日志。
3. 风控与合规扫描报告。
4. 管理摘要（收益-风险-解释性）。

---

## 13. 实施计划（8 周）

- **第 1-2 周**：需求冻结、数据契约、基线策略。
- **第 3-4 周**：跑通 CSE 主闭环与基础回测。
- **第 5-6 周**：接入风控闸门、记忆蒸馏、审计日志。
- **第 7-8 周**：连续夜间运行、稳定性修复、试点验收。

---

## 14. 建议目录结构（MVP）

```text
nanobot/
  skills/evoquant/
    SKILL.md
    prompts/
    templates/
  tools/
    quant_data.py
    quant_backtest.py
    quant_eval.py
    quant_riskcheck.py
  memory/evoquant/
    alpha_zoo.jsonl
    hall_of_shame.jsonl
    meta_rules.jsonl
  runs/evoquant/
    YYYYMMDD/
      task_config.json
      candidates/
      reports/
      logs/
```

---

## 15. 关键设计决策总结

1. **先研究后交易**：首期不接实盘下单，聚焦稳定研究闭环。  
2. **先可控后智能**：槽位化、白名单化变异优先于自由生成。  
3. **先审计后放权**：所有进化与审批动作必须可追溯。  
4. **先鲁棒后收益**：跨市场、跨 Regime 稳健性优先于短期高收益。

> 结论：本系统设计将 CSE 的“规划-进化-记忆”能力工程化落地到 nanobot，使其成为一个可持续迭代的投研方法论引擎，而非一次性策略生成器。
