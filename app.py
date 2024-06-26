import requests
from flask import Flask, request, jsonify, send_file
import logging
import re
import os
import time
import plotly.graph_objects as go
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.static_folder = 'static'
logging.basicConfig(level=logging.DEBUG)

@app.route('/v2/images/generations', methods=['POST'])
def generate_image_cf():
    # 获取前端请求中的数据
    data = request.json
    logging.debug(f"Received request data: {data}")

    # 提取 Cloudflare 账户 ID 和 API 令牌
    cloudflare_account_id = data.get('CLOUDFLARE_ACCOUNT_ID')
    cloudflare_api_token = data.get('cloudflare_api_token')
    prompt = data.get('prompt')

    if not cloudflare_account_id or not cloudflare_api_token or not prompt:
        return jsonify({'error': 'Missing required parameters'}), 400

    # 构造 Cloudflare API 请求
    url = f"https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {cloudflare_api_token}"}
    payload = {"prompt": prompt}

    # 发送请求到 Cloudflare API
    response = requests.post(url, headers=headers, json=payload)
    logging.debug(f"Response status code: {response.status_code}")

    # 检查响应状态码
    if response.status_code != 200:
        return jsonify({'error': 'Failed to generate image'}), response.status_code

    # 获取完整的响应内容
    response_data = response.content
    logging.debug(f"Response content: {response_data}")

    # 生成图像文件名
    img_filename = f'image_{int(time.time())}.png'
    save_path = os.path.join(app.static_folder, img_filename)

    # 将图像保存到 'static' 目录
    with open(save_path, 'wb') as f:
        f.write(response_data)

    # 构造返回给前端的数据
    img_url = f'https://mistpe-flask-spacesdhuitu.hf.space/static/{img_filename}'
    result = {
        "created": int(time.time()),
        "data": [
            {"url": img_url}
        ]
    }
    return jsonify(result)

def preprocess_prompt(prompt):
    # 使用非捕获组 (?:...) 来匹配任意字符
    pattern = r'@startmindmap\n((?:.*?\n)*?)@endmindmap'
    match = re.search(pattern, prompt, re.DOTALL)
    if (match):
        mindmap_content = match.group(1)
        processed_prompt = f"@startmindmap\n{mindmap_content}\n@endmindmap"
    else:
        processed_prompt = prompt
    return processed_prompt

@app.route('/v1/images/generations', methods=['POST'])
def generate_image_plantuml():
    # 获取前端请求中的数据
    data = request.json
    logging.debug(f"Received request data: {data}")

    # 预处理 prompt
    processed_prompt = preprocess_prompt(data['prompt'])
    logging.debug(f"Processed prompt: {processed_prompt}")

    # 将数据发送到 https://plantuml-server-jetty.onrender.com/coder 接口
    response = requests.post('https://plantuml-server-jetty.onrender.com/coder', data=processed_prompt.encode('utf-8'))
    logging.debug(f"Response status code: {response.status_code}")

    # 检查响应状态码
    if response.status_code != 200:
        return jsonify({'error': 'Failed to generate image'}), response.status_code

    # 获取完整的响应内容
    response_data = response.content
    logging.debug(f"Response content: {response_data}")

    created = 1589478378 # 假设这是一个固定值
    url = f"https://plantuml-server-jetty.onrender.com/png/{response_data.decode('utf-8')}"

    # 构造返回给前端的数据
    result = {
        "created": created,
        "data": [
            {
                "url": url
            }
        ]
    }
    return jsonify(result)

@app.route('/api/3d-surface', methods=['POST'])
def generate_3d_surface():
    data = request.json
    prompt = data['prompt']

    # 提取#start和#end之间的代码
    start_index = prompt.find("#start") + len("#start")
    end_index = prompt.find("#end")
    code = prompt[start_index:end_index].strip()

    # 创建一个字典来存储局部变量
    local_vars = {}

    # 执行前端传入的代码,并传入局部变量字典
    exec(code, globals(), local_vars)

    # 从局部变量字典中获取 'fig' 对象
    fig = local_vars.get('fig')

    # 检查 'fig' 是否已定义
    if fig is None:
        return jsonify({"error": "No figure 'fig' defined in the provided code."}), 400

    # 保存图表为 HTML 文件
    html_filename = f'3d_surface_plot_{int(time.time())}.html'
    fig.write_html(f'static/{html_filename}')

    # 构建 HTML 文件的 URL
    html_url = f'https://mistpe-flask-space-3djiaohu2.hf.space/static/{html_filename}'

    # 保存 fig 对象为图像文件
    img_filename = f'3d_surface_plot_{int(time.time())}.png'
    fig.write_image(f'static/{img_filename}')

    # 构建图像文件的 URL
    img_url = f'https://mistpe-flask-space-3djiaohu2.hf.space/static/{img_filename}'

    # 返回 JSON 格式的响应, 包含 HTML 和图像的访问链接
    return jsonify({
        "created": int(time.time()),
        "data": [
            {"url": img_url},
            {"url": html_url}
        ]
    })

@app.route('/api/3d-sphere', methods=['POST'])
def generate_3d_sphere():
    # 获取请求中的代码
    code = request.json['prompt']

    # 判断代码是否以'''python开头和'''结尾
    if code.startswith("```python") and code.endswith("```"):
        # 如果是,则删除开头和结尾的字符串
        code = '\n'.join(code.split('\n')[1:-1])

    # 在主线程中执行代码生成 3D 图像
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    exec(code)

    # 将 3D 图像保存为 PNG 格式
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # 生成图像文件名
    img_filename = f'3d_sphere_{int(time.time())}.png'
    save_path = os.path.join(app.static_folder, img_filename)

    # 将图像保存到 'static' 目录
    with open(save_path, 'wb') as f:
        f.write(buf.getvalue())

    # 返回 JSON 格式的响应,包含图像的访问链接
    img_url = f'https://mistpe-flask-space.hf.space/static/{img_filename}'
    return {
        "created": int(time.time()),
        "data": [
            {
                "url": img_url
            }
        ]
    }

if __name__ == '__main__':
    # 确保 static 目录存在
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=7860, debug=True)
