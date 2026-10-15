import os
import config
import json
from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient
from datetime import datetime, timezone, timedelta

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

tavily = TavilyClient(
    api_key=os.getenv("TAVILY")
)


def run_search(query):
    raw = tavily.search(query=query)
    results = [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
            "score": item.get("score"),
        }
        for item in raw.get("results", [])
    ]
    return results


def get_current_time(offset_hours=8):
    """获取当前时间，默认东八区（UTC+8）"""
    tz = timezone(timedelta(hours=offset_hours))
    now = datetime.now(tz)
    return {
        "timezone": str(tz),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timestamp": int(now.timestamp())
    }


tool_map = {
    "search": run_search,
    "get_current_time": get_current_time
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "用于搜索最新的网页信息、新闻或事实性内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询语句，用自然语言描述你想查找的信息"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "显示当前时间的工具",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

messages = [
    {"role": "system", "content": "你是一个智能问答助手，精简概括性的回答我的问题！"},
    {"role": "user", "content": "今天有什么 AI 新闻？同时要标注来源示例[标题](链接) 或者「据 XX 报道」"}
]

for _ in range(config.MAX_ITER):
    response = client.chat.completions.create(
        model=os.getenv("MODEL_ID"),
        messages=messages,
        tools=tools,
        temperature=0.7
    )
    
    msg = response.choices[0].message
    messages.append(msg)
    
    # 调用工具退出判断
    if not msg.tool_calls:
        print(msg.content)
        break
    
    # 循环遍历模型的所用工具调用
    for tool_call in msg.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        func = tool_map.get(name)
        if func is None:
            result = f"没有名为 {name} 的工具。可用工具：{list(tool_map)}"
        else:
            result = func(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    print("本轮 tool_calls 数量：", len(msg.tool_calls) if msg.tool_calls else 0)

else:
    print("达到最大迭代次数，强制结束！")
