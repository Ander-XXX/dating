from openai import OpenAI
import pandas as pd
from prompt import keywords_prompt
import time

# ================= 初始化配置 =================
API_KEY = "sk-1095da632dba4d37843efb21854f522b"
BASE_URL = "https://api.deepseek.com/v1"
MODEL_NAME = "deepseek-chat"
INPUT_FILE = '/Users/ander/Desktop/相亲/add.xlsx'
OUTPUT_PREFIX = "result_female"

# ================= 数据加载 =================
print("⏳ 加载数据...")
try:
    data = pd.read_excel(INPUT_FILE)
    my_infos = data['info'].tolist()
    candidates = data['candidate'].tolist()
    print(f"✅ 成功加载 {len(my_infos)} 条数据")
except Exception as e:
    print(f"❌ 数据加载失败: {e}")
    exit()

# ================= API客户端 =================
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ================= 处理逻辑 =================
def process_candidate(user_info: str, candidate_info: str) -> str:
    """处理单个候选人"""
    prompt = (
        f"{keywords_prompt}\n"
        "用户除了小red外最可能喜欢的人微信号是多少？注意 一定要告诉用户他的微信号是多少，否则用户找不到他。\n"
        "## 匹配规则解释（非用户需求）\n"
        "1. 如果用户没有提到经济考虑忽视此条，如果提到经济上的考虑，计算机博士未来毕业收入可能很高\n"
        "2. 对颜值要求微看意思是，希望对方稍微好看一点\n"
        f"## 用户的信息\n{user_info}\n"
        f"## 候选人信息\n{candidate_info}"
    )
    
    try:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    temperature=0.7,
                    max_tokens=500
                )
                
                full_response = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        print(content, end='', flush=True)  # 实时显示流式输出
                
                return full_response.strip()
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"⚠️ 请求失败，{wait}秒后重试... (错误: {str(e)})")
                    time.sleep(wait)
                    continue
                else:
                    raise
                
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"

# ================= 批量处理 =================
results = []
BATCH_SIZE = 10  # 每批处理数量
total_batches = (len(my_infos) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num in range(total_batches):
    start = batch_num * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(my_infos))
    
    print(f"\n🔧 处理批次 {batch_num+1}/{total_batches} ({start+1}-{end}条)")
    
    batch_results = []
    for idx in range(start, end):
        print(f"\n📌 处理第 {idx+1} 条 [{my_infos[idx][:30]}...]")
        result = process_candidate(my_infos[idx], candidates[idx])
        batch_results.append(result)
        print("\n" + "-"*50)
    
    # 实时保存每批结果
    df = pd.DataFrame({
        "用户信息": my_infos[start:end],
        "候选人信息": candidates[start:end],
        "匹配结果": batch_results
    })
    output_file = f"{OUTPUT_PREFIX}_batch_{batch_num+1}.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n💾 已保存批次结果到 {output_file}")
    
    results.extend(batch_results)

# ================= 最终汇总 =================
if results:
    final_df = pd.DataFrame({
        "用户信息": my_infos[:len(results)],
        "候选人信息": candidates[:len(results)],
        "匹配结果": results
    })
    final_output = f"{OUTPUT_PREFIX}_full_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    final_df.to_excel(final_output, index=False)
    print(f"\n🎉 全部处理完成！最终结果已保存至 {final_output}")
else:
    print("\n⚠️ 未生成任何结果，请检查输入数据或API配置")
