import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY")
)

result = client.search(query="今天是哪一天？有什么AI新闻？", max_results=3)
print(result)
