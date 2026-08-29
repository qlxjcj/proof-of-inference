---
title: Proof of Inference - Agent Tank Hackathon Product Plan
type: feat
status: active
date: 2026-08-28
---

# Proof of Inference - Agent Tank Hackathon Product Plan

## Overview

Proof of Inference 是一个 AI 推理证明挖矿协议，为 Agent Tank Hackathon (9月3日-17日) 构建。核心创新：矿工通过做有用的 AI 推理工作来挖矿，而不是浪费算力的哈希计算。

**Hackathon 信息：**
- 主题：Agentic Economy（代理经济）
- 奖励：5% GenLayer Points
- 时间：9月3日 - 9月17日（两周）

## Problem Frame

### 当前状态
- ✅ 核心智能合约已完成（256行）
- ✅ 21个测试用例全部通过
- ✅ 基础前端界面已完成
- ⚠️ 需要完善产品功能和演示

### 核心价值主张
1. **有用的工作**：矿工做真实 AI 推理，不是浪费算力
2. **隐私保护**：输入数据不上链，只有结果公开
3. **经济激励**：赏金系统激励高质量推理
4. **可验证性**：5个独立验证者共识 = 计算正确性证明

## Requirements Trace

- R1. 核心挖矿机制：提交任务 → 矿工竞争 → 验证共识 → 领取奖励
- R2. 隐私保护：输入数据不公开，只有结果上链
- R3. 经济模型：赏金激励，惩罚低质量提交
- R4. 用户体验：简洁的前端界面，易于演示
- R5. 创新性：展示 Agentic Economy 的新范式

## Scope Boundaries

### 必须完成（MVP）
- 核心挖矿流程完整可用
- 前端界面可演示
- 测试覆盖关键路径
- 部署到测试网

### 延后实现（Nice to Have）
- 矿工信誉系统
- 多轮竞标机制
- 链下数据存储优化
- 移动端适配

## Context & Research

### 技术栈
- **智能合约**：Python + GenLayer SDK
- **共识机制**：gl.nondet.exec_prompt + gl.eq_principle.prompt_comparative
- **前端**：HTML + JavaScript + ethers.js
- **测试**：pytest + gltest direct mode

### 现有代码模式
- 参考 `luxury-authenticity/` 的共识机制
- 参考 `prediction-market/` 的资金管理
- 参考 `device-market/` 的用户交互模式

## Key Technical Decisions

1. **共识机制**：使用 GenLayer 原生 AI 共识，5个验证者独立推理
2. **隐私策略**：输入数据通过 IPFS hash 引用，不直接上链
3. **经济模型**：赏金制，获胜矿工获得全部赏金
4. **验证逻辑**：AI 评估结果一致性，选择最佳提交

## Two-Week Roadmap

### Week 1: 核心功能完善 (9月3日-9月10日)

#### Day 1-2: 合约增强
- [ ] 添加矿工信誉系统（基于历史胜率）
- [ ] 实现任务超时机制（防止任务永久悬挂）
- [ ] 添加最小赏金限制（防止垃圾任务）
- [ ] 优化 gas 消耗

#### Day 3-4: 隐私功能
- [ ] 实现 IPFS 数据引用（不直接存储数据）
- [ ] 添加数据加密选项（可选）
- [ ] 实现零知识证明验证（ZK-proof 集成）

#### Day 5-7: 前端优化
- [ ] 重构前端为 React/Vue 组件
- [ ] 添加实时任务状态更新
- [ ] 实现钱包连接和交易签名
- [ ] 添加任务浏览和筛选功能

### Week 2: 演示准备 (9月11日-9月17日)

#### Day 8-10: 测试和部署
- [ ] 完善单元测试（目标：30+ 测试用例）
- [ ] 集成测试（端到端流程）
- [ ] 部署到 GenLayer 测试网
- [ ] 性能测试和优化

#### Day 11-12: 演示材料
- [ ] 制作演示视频（3-5分钟）
- [ ] 准备 Demo Day 演示脚本
- [ ] 编写项目文档和 README
- [ ] 准备 Q&A 问题清单

#### Day 13-14: 最终优化
- [ ] Bug 修复和细节优化
- [ ] 用户体验改进
- [ ] 准备提交材料

## Implementation Units

### Unit 1: 矿工信誉系统
**Goal:** 建立矿工历史表现追踪，提高网络质量

**Files:**
- Modify: `proof_of_inference.py`
- Test: `tests/direct/test_proof_of_inference.py`

**Approach:**
- 添加 MinerProfile 数据结构
- 追踪胜率、平均置信度、完成任务数
- 高信誉矿工获得优先权

**Test scenarios:**
- Happy path: 矿工完成任务后信誉更新
- Edge case: 新矿工初始信誉
- Error path: 验证失败对信誉的影响

### Unit 2: 任务超时机制
**Goal:** 防止任务永久悬挂，提高网络效率

**Files:**
- Modify: `proof_of_inference.py`
- Test: `tests/direct/test_proof_of_inference.py`

**Approach:**
- 添加 deadline 字段到 Task
- 实现 cancel_task 函数
- 超时后自动退款

**Test scenarios:**
- Happy path: 超时后 creator 可取消任务
- Edge case: 超时前尝试取消
- Error path: 非 creator 尝试取消

### Unit 3: IPFS 数据引用
**Goal:** 实现真正的隐私保护，数据不上链

**Files:**
- Modify: `proof_of_inference.py`
- Create: `utils/ipfs.py`
- Test: `tests/direct/test_ipfs.py`

**Approach:**
- 使用 IPFS hash 引用数据
- 矿工通过 hash 获取数据进行推理
- 验证者验证 hash 对应的数据

**Test scenarios:**
- Happy path: 提交 IPFS hash 并验证
- Edge case: 无效 hash 处理
- Error path: 数据不可用时的降级策略

### Unit 4: 前端界面重构
**Goal:** 提供专业的用户界面，便于演示

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/components/TaskList.jsx`
- Create: `frontend/src/components/SubmitTask.jsx`
- Create: `frontend/src/components/MiningPanel.jsx`

**Approach:**
- 使用 React + Tailwind CSS
- 实现响应式设计
- 添加实时状态更新

**Test scenarios:**
- Happy path: 用户提交任务并查看状态
- Edge case: 网络连接中断
- Error path: 交易失败提示

### Unit 5: 部署和测试
**Goal:** 部署到测试网，确保稳定运行

**Files:**
- Create: `scripts/deploy.py`
- Create: `scripts/testnet_test.py`
- Modify: `index.html` (更新合约地址)

**Approach:**
- 部署到 GenLayer testnet
- 执行端到端测试
- 记录性能指标

**Test scenarios:**
- Happy path: 完整挖矿流程
- Edge case: 多个矿工同时提交
- Error path: 网络拥堵处理

## Success Metrics

### 技术指标
- 测试覆盖率：>90%
- 合约大小：<500行
- 交易确认时间：<30秒
- 前端加载时间：<3秒

### 业务指标
- 演示视频：3-5分钟
- 用户流程：3步完成任务提交
- 创新点：展示 AI 挖矿新范式

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 共识机制失败 | Low | High | 实现降级策略，记录详细日志 |
| 前端兼容性 | Medium | Medium | 多浏览器测试，使用成熟框架 |
| 网络拥堵 | Medium | High | 实现重试机制，优化 gas |
| 时间不足 | Medium | High | 优先核心功能，延后优化 |

## Demo Day 演示脚本

### 开场（30秒）
"大家好，我是[名字]，今天展示 Proof of Inference - 一个 AI 推理证明挖矿协议。"

### 问题陈述（30秒）
"传统挖矿浪费算力做哈希计算。我们让矿工做有用的 AI 推理工作，同时保护数据隐私。"

### 演示流程（2分钟）
1. 展示提交任务界面
2. 演示矿工提交推理结果
3. 展示共识验证过程
4. 显示获胜矿工领取奖励

### 技术亮点（1分钟）
1. AI 共识机制：5个独立验证者
2. 隐私保护：数据不上链
3. 经济激励：赏金系统

### 结尾（30秒）
"Proof of Inference 将挖矿从浪费算力转变为产生价值。感谢大家！"

## Q&A 准备

### 常见问题
1. **Q: 如何保证推理质量？**
   A: 5个独立验证者共识，低质量结果会被淘汰

2. **Q: 隐私如何保护？**
   A: 数据通过 IPFS hash 引用，不上链，只有结果公开

3. **Q: 经济模型如何运作？**
   A: 用户提交赏金，获胜矿工获得赏金，激励高质量工作

4. **Q: 和传统挖矿的区别？**
   A: 传统挖矿浪费算力，我们产生真实价值

## Sources & References

- **GenLayer 文档**: https://docs.genlayer.com
- **Agent Tank Hackathon**: https://portal.genlayer.foundation/agent-tank/
- **参考项目**: luxury-authenticity, prediction-market, device-market
- **技术栈**: Python, GenLayer SDK, React, ethers.js
