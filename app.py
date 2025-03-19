from flask import Flask, render_template, request, jsonify, Response
from openai import OpenAI
import pandas as pd
import socket
import time
import webbrowser

# ================= 配置区 =================
API_KEY = "sk-1095da632dba4d37843efb21854f522b"  # 你的DeepSeek API密钥
BASE_URL = "https://api.deepseek.com/v1"         # DeepSeek API地址
MODEL_NAME = "deepseek-chat"                     # 模型名称
MAX_RETRIES = 3                                  # 最大重试次数

# ================= 端口自动分配 =================
def find_available_port(start_port=50000, max_attempts=100):
    """自动寻找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise ValueError("未找到可用端口")

# ================= Flask应用初始化 =================
app = Flask(__name__)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ================= 前端页面 =================
@app.route('/')
def home():
    return render_template('index.html')

# ================= 核心匹配逻辑 =================
def generate_match_result(user_info, candidate_info):
    """生成匹配结果（流式）"""
    from prompt import keywords_prompt  # 确保存在prompt.py
    
    prompt = f"""
    {keywords_prompt}
    ## 用户信息
    {user_info}
    ## 候选人信息
    {candidate_info}
    请根据以上信息生成匹配分析，并明确推荐微信号。
    """
    
    for attempt in range(MAX_RETRIES):
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                temperature=0.7,
                max_tokens=500
            )
            return stream
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)

# ================= API接口 =================
@app.route('/api/match', methods=['POST'])
def match():
    """单个匹配接口"""
    data = request.json
    try:
        stream = generate_match_result(
            data['user_info'], 
            data['candidate_info']
        )
        
        def generate():
            for chunk in stream:
                yield chunk.choices[0].delta.content or ""
                
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_process():
    """批量处理Excel文件"""
    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "仅支持.xlsx格式"}), 400
    
    try:
        df = pd.read_excel(file)
        results = []
        for _, row in df.iterrows():
            stream = generate_match_result(row['user_info'], row['candidate_info'])
            full_response = "".join([chunk.choices[0].delta.content or "" for chunk in stream])
            results.append(full_response)
            time.sleep(1)  # 避免速率限制
        
        result_df = pd.DataFrame({"匹配结果": results})
        output_path = "batch_result.xlsx"
        result_df.to_excel(output_path, index=False)
        
        return jsonify({"download_url": f"/download/{output_path}"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= 启动服务 =================
if __name__ == '__main__':
    port = find_available_port()
    print(f"🚀 服务启动于: http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")  # 自动打开浏览器
    app.run(host='0.0.0.0', port=port, debug=False)  # 必须关闭debug模式
