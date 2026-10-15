import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

response = client.responses.create(
    model=os.getenv("MODEL_ID"),
    instructions="你是一个智能问答助手，回答我关于大模型学习相关的问题, 给我一个精简的概括性回答！",
    input="responses接口和之前的chat.completions接口有什么区别？"
)

print(response.output_text)
