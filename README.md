# zs_study_hello_agents

不使用任何框架，手写一个能调用工具的 ReAct Agent。约 120 行 Python。

## 它是什么

它是ReAct 范式 —— Reasoning + Acting。他的核心是思考 + 行动，当用户发来一个请求，模型会先思考，决定要不要调工具，拿回结果再思考，直到它不再要工具、直接给答案。严格说，**我实现的是 Acting 那一半**：Reasoning 是模型内部产生的（我 `print` 的时候能看到 `reasoning_content`），我的循环只用它的结果。

## 怎么跑起来

- Python 3.12
- 依赖：

```bash
pip install openai tavily-python python-dotenv
```

- 复制 `.env.example` 为 `.env`，填入四个变量：

```
API_KEY=
BASE_URL=
MODEL_ID=
TAVILY=
```

- 运行：

```bash
.venv/Scripts/python.exe first_agent.py
```

循环上限在 `config.py` 的 `MAX_ITER`（当前为 5）。

> 模型调用走自定义 `base_url`（OpenAI 兼容网关），不是 OpenAI 官方托管服务，因此 `MODEL_ID` 需要显式指定。

## 它是怎么工作的

1. 组装 `messages`（system + user），带上 `tools` 说明书，调一次 `chat.completions`。
2. 模型返回两种可能：
   - 直接给 `content` → 结束，打印答案
   - 返回 `tool_calls` → 进入分发
3. 遍历 `tool_calls`，解析出工具名和参数（`arguments` 是 **JSON 字符串**，需要 `json.loads`），用 `tool_map` 按名字找到对应函数执行。
4. 每条调用的结果作为一条 `role: "tool"` 的消息 append 回 `messages`，并带上对应的 `tool_call_id`。
5. 回到第 1 步。

**注意：这个接口是无状态的** —— 每一轮都要把整段历史重新发一遍。模型唯一的「记忆」就是 `messages` 本身。

## 我做的三个关键选择

**1. 循环用 `for _ in range(MAX_ITER)` 配 `for...else`，而不是 `while True`。**

模型可能陷入「搜了不满意 → 再搜」而不收敛。没有上限的话，程序会挂死，同时一直在烧 token、撑爆上下文。

**2. 分发用 `tool_map` 字典（名称 → 函数对象），而不是 if-else。**

加第三个工具时，循环体一行都不用改。另外，模型可能虚构 schema 里没有的工具名，所以用 `.get()` 取，取不到时**回灌一条「没有这个工具，可用的是这些」的 tool 消息** —— 不是抛异常，而是**把一次错误变成一轮对话**，让模型自己纠正。实测中模型收到后会自己改用别的工具，程序不崩。

**3. 工具返回值做了裁剪。**

Tavily 的原始返回里有很多当前用不上的字段，只保留 `title` / `url` / `content` / `score`。因为 `messages` 每轮都要整体重发，不裁剪就是 N 倍开销。

这里踩过一个坑：留下 `url` 的初衷是「让模型能给出处」，但实测模型一个链接都没给 —— **工具提供字段不等于模型会用它**，最终是在 system prompt 里明确要求后才生效的。

## 目前做不到什么

- **没有上下文管理**：工具返回的长内容会一直堆在 `messages` 里，多轮之后会撑满。
- **不校验工具结果**：实测中把时间工具摘掉后，模型降级去搜索网页、拿到缓存内容，**自信地给出了一个错误的日期**。模型没有能力判断结果是否过期。
- **没有超时和重试**：工具是外部服务，挂了就卡在那里（返回为空的情况做了兜底）。
- **`arguments` 的 JSON 解析没有兜底**：官方文档明确说明模型不总是生成合法 JSON，这里目前会直接抛异常。
- **迭代耗尽时收尾难看**：`MAX_ITER` 用满时只打印一行提示，模型这一轮已经生成的内容不会被输出。

## 模型的实际输出回答

本轮 tool_calls 数量： 2
		以下是今天（2026年10月15日）值得关注的 AI 新闻速览：

**🔒 安全与监管**
- OpenAI 在其办公室内发现一个隐蔽录音装置，用自家模型分析后确认是本人员工安放，已移交 FBI 并将该员工解雇；目前未发现模型权重或客户数据外泄。据 OpenAI Newsroom 报道。
- Anthropic 发布报告警告：AI 模型或仅需数月就具备"自我复制"能力，且一旦扩散极难彻底关停，连智能烤箱、廉价电视盒子等物联网设备都可能运行推理。据 AIBase 报道 [AI最新资讯](https://news.aibase.com/zh/news)。

**💥 行业重大动向**
- Character.AI 成立五年后申请 Chapter 11 破产，拟以 2000 万美元将部分资产出售给 Disney。据 404 Media 报道（via [AIHOT 日报](https://aihot.news/daily)）。
- IDC 报告显示，英伟达在中国 AI 芯片市场份额跌至 34%，华为追到 28%。据 AIBase 报道。
- 英伟达拟以约 130 亿美元收购 Hugging Face。据财联社报道（via [AI工具集](https://ai-bot.cn/daily-ai-news)）。
- 苹果与个性化音频初创公司 Huxe 达成"反向收购雇佣"，收编核心团队并获其知识产权非独占许可。据 MacRumors 报道。

**🧠 模型与产品**
- 面壁智能开源端侧多模态模型 MiniCPM-V 4.7，含 35B-A3B 与 1B 两版本，3GB 内存即可流畅运行，主打端侧 MoE 多模态。据 OpenBMB 社区发布。
- Liquid AI 发布开源权重端侧推理模型 LFM2.5-24B-A2B（总参数 24B、激活 2B）。
- Claude 管理智能体上线动态工作流，单次最高可并行调度 1000 个 AI Agents。据 AIBase 报道。
- 科大讯飞推出星火 X2.5，基于全国产算力训练，MoE 架构，参数 293B-A30B，重点提升代码生成与智能体能力。

**🚀 硬件与终端**
- 千问发布 AI 眼镜 N1/N1Pro，及与 Bose 合作的耳夹式 AI 耳机；N1Pro 支持心率、血氧、皮肤温度监测及虹膜识别支付。据 AIBase 报道 [AI资讯](https://www.aibase.com/zh/news)。
- 高通 CEO 称 AI 巨头或于 2028 年杀入手机市场，把千亿大模型塞进掌心。据 AIBase 报道。

**📌 其他**
- 微软发布 Edge 155 稳定版，增强 AI 标签页整理并支持 JPEG XL 解码。
- 据 [AI产品榜早报](https://www.aicpb.com/news)：OpenAI 首款 AI 硬件产品或为智能笔（富士康代工）；通义千问开源图像生成模型 Qwen-Image-2512；智能眼镜被纳入 2026 国家补贴。

> 提示：以上综合自多个来源，部分条目为近日动态，建议点击来源链接核对最新细节。需要我针对某条新闻深入展开吗？

