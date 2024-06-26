import requests
from flask import Flask, request, jsonify
import logging
import os
import time

app = Flask(__name__)
app.static_folder = 'static'
logging.basicConfig(level=logging.DEBUG)

@app.route('/v1/images/generations', methods=['POST'])
def generate_image():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
