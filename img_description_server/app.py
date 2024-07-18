from PIL import Image
from openai import OpenAI
from flask import Flask, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import os
import io
import configparser
import json

def load_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['DEFAULT']

app = Flask(__name__)

# 加载配置
config = load_config()
app.config['UPLOAD_FOLDER'] = 'uploads'  # 保存上传图片的文件夹路径

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 设置OpenAI API密钥和URL
BASE_URL = config['BASE_URL']
API_KEY = config['API_KEY']
MODEL = config['MODEL']

PROMPT = """
Now that you're a robot with visual abilities, I'm going to give you a picture, which is what you see in the first person. Can you tell me what you see? And think about it, would you like someone to initiate a conversation with you at this time, and if so, what topic would this person initiate
Format of output

## Restrictions:
- Each topic description must be within 40 words.
- Avoid any mention of camera angles, lighting, or other photographic techniques.
- Give 3 topics.

## Output Format:
The output structure is referred to in json below:
{
  "scene": "<>",
  "start_talk": true,
  "topics": [
    {
      "content": "<>",
      "description": "<>"
    },
    {
      "content": "<>",
      "description": "<>"
    },
    {
      "content": "<>",
      "description": "<>"
    }
  ]
}
"""

openai = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def parser_image_description_resp(response_content):
    """
    解析 OpenAI 的响应
    """
    # 将 JSON 字符串解析为字典
    response_dict = json.loads(response_content)

    # 提取特定的字段
    scenario = response_dict['scene']
    start_talk = response_dict['start_talk']
    topics = response_dict['topics']

    return scenario, start_talk, topics

def request_image_description(img_url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_url
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    return response.choices[0].message.content

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def upside_down_image(image_)

def upload(image_file):
    """
    上下颠倒图片并保存
    """
    if image_file.filename == '':
        return 'No selected file', 400

    if image_file and allowed_file(image_file.filename):
        # 确保文件名安全
        filename = secure_filename(image_file.filename)

        # 使用Pillow加载图像
        image = Image.open(image_file)
        
        # 翻转图像
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)
        
        # 保存翻转后的图像到内存中的字节流
        img_byte_arr = io.BytesIO()
        flipped_image.save(img_byte_arr, format=image.format)
        img_byte_arr.seek(0)

        # 将翻转后的图像保存到上传文件夹
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(image_path, 'wb') as f:
            f.write(img_byte_arr.getvalue())

        # 生成公开访问的URL
        image_url = url_for('uploaded_file', filename=filename, _external=True)

        return image_url, 200
    else:
        return 'Invalid file type', 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # 返回保存在服务器上的图片文件
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/describe_image', methods=['POST'])
def describe_image():
    if 'image' not in request.files:
        error = 'No image provided'
        print(f"{error}")
        return jsonify({'error': error}), 400
    image_file = request.files['image']
    # 调用上传图片函数，获取上传后的结果
    image_url, code = upload(image_file=image_file)
    print(f"{image_url}, {code}")
    if code != 200:
        return jsonify({'error': image_url}), code
    try:
        # 获取图片描述
        resp = request_image_description(image_url)
        scenario, start_talk, topics = parser_image_description_resp(resp)
        return jsonify({
            'scenario': scenario,
            'start_talk': start_talk,
            'topics': topics
            }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400

@app.route('/describe_image_url', methods=['POST'])
def describe_image_url():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON in request body"}), 400
    
    # 处理数据
    image_url = data.get('image_url')
    if not image_url:
        error = 'No image_url provided'
        print(f"{error}")
        return jsonify({'error': error}), 400
    print(f"{image_url}")
    try:
        # 获取图片描述
        resp = request_image_description(image_url)
        scenario, start_talk, topics = parser_image_description_resp(resp)
        return jsonify({
            'scenario': scenario,
            'start_talk': start_talk,
            'topics': topics
            }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400

@app.route('/hello', methods=['POST'])
def hello():
    data = request.get_json()
    username = data.get('username')
    if username:
        print(f"{username}")
        response = {
            'message': f'Success, {username} hello'
        }
        code = 200
    else:
        response = {
            'message': 'Username not provided'
        }
        code = 400
    return jsonify(response), code


def test_request_image_description():
    import time
    start_time = time.time()
    resp = request_image_description(
        "https://bkimg.cdn.bcebos.com/pic/e7cd7b899e510fb30f2464687e7fdf95d143ac4ba6b2?x-bce-process=image/format,f_auto/watermark,image_d2F0ZXIvYmFpa2UyNzI,g_7,xp_5,yp_5,P_20/resize,m_lfit,limit_1,h_1080")
    scenario, topics = parser_image_description_resp(resp)
    print(f"{resp}")
    print(f"{scenario}")
    print(f"{topics}")
    print(f"time cost: {time.time() - start_time} s")


if __name__ == '__main__':
    # TODO test
    # test_request_image_description()

    app.run(host='0.0.0.0', port=8101)
