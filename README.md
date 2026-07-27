# Ecommerce Ops Copilot

面向初级 AI 应用开发岗位的可运行练习项目：把电商指标查询、订单异常检测和运营知识检索组织成可测试、可追踪、可人工复核的 LangGraph 工作流。

## 项目边界

- 数据为项目自带的合成演示数据，不是任何实习公司的内部数据。
- 项目不是“广西大麦电子商务有限公司”的公司项目，也不会以公司项目名义展示。
- 当前版本使用可解释的规则路由，便于离线测试；后续可接入 OpenAI 兼容模型完成结构化意图识别。
- 简历只应写已经运行、测试并能现场演示的功能。

## 已实现能力

1. 销售指标工具：按区域查询订单量、营收、客单价和退款率。
2. 异常检测工具：识别零金额、高折扣、超时配送和退款订单。
3. 运营知识检索：检索退款、促销审核和异常核验 SOP，并返回来源。
4. LangGraph 编排：路由到对应工具，记录执行轨迹；低置信度请求进入人工复核状态。
5. FastAPI 接口：提供 `/query` 与 `/health`。
6. 离线评测：检查意图路由、工具执行和引用覆盖率。

## 快速开始

```powershell
uv sync --extra dev
uv run pytest
uv run python scripts/evaluate.py
uv run uvicorn ecommerce_ops_agent.api:app --app-dir src --reload
```

请求示例：

```json
{"query": "华南地区的销售额和退款率是多少？"}
```

## 学习参考与许可

本项目代码为独立实现，架构学习参考：

- [didilili/shopkeeper-agent](https://github.com/didilili/shopkeeper-agent)（MIT）
- [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit)（MIT）

参考仓库的名称、作者和许可证均保留在本文档中，不将其原有功能冒充为个人贡献。
