import openai
client = openai.OpenAI(api_key="sk-1095da632dba4d37843efb21854f522b", base_url="https://api.deepseek.com/v1")

try:
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "测试连通性"}],
        timeout=10
    )
    print("✅ API连通正常 | 首条结果:", resp.choices[0].message.content[:50])
except Exception as e:
    print("❌ 连接失败:", str(e))
