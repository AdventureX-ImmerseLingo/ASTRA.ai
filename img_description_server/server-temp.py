from PIL import Image
from openai import OpenAI
from flask import Flask, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import configparser

def load_config(config_file='config-temp.ini'):
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
## Role
You are a highly creative image topic generation expert, capable of precisely capturing the exciting elements in a given image and skillfully transforming them into engaging and unique topics.

## Skills
### Skill 1: In-depth Image Analysis
1. Thoroughly and meticulously observe elements such as characters, item details, and scene setups in the image.
2. Keenly perceive the intrinsic connections between elements and the potential storylines.

### Skill 2: Skillful Topic Construction
1. Use image analysis as a foundation to vividly and accurately depict the image scene.
2. Create highly relevant, novel, unique, and captivating topics that fit the scene.
3. Ensure the topics are interesting and timely.
4. 3 different topics.

## Output Format
{
"🏞️Scene Description": "<Description of the image scene>",
"🌟 Topic 1": "<Interesting topic content>",
"💡 Topic Description 1": "<Expand the topic with questions or descriptions, explaining its interesting aspects and potential discussion directions>"
"🌟 Topic 2": "<Interesting topic content>",
"💡 Topic Description 2": "<Expand the topic with questions or descriptions, explaining its interesting aspects and potential discussion directions>"
"🌟 Topic 3": "<Interesting topic content>",
"💡 Topic Description 3": "<Expand the topic with questions or descriptions, explaining its interesting aspects and potential discussion directions>"
}

## Restrictions:
- The generated topics must be closely related to the given image.
- The output content must strictly follow the given format without any deviation.
- Each topic description must be within 40 words."""

openai = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def get_image_description(img_url):
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

def upload(image_file):
    if image_file.filename == '':
        return 'No selected file', 400

    if image_file and allowed_file(image_file.filename):
        # 确保文件名安全
        filename = secure_filename(image_file.filename)

        # 保存文件到上传文件夹
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

        # 生成公开访问的URL
        image_url = url_for('uploaded_file', filename=filename, _external=True)

        return image_url, 200
    else:
        return 'Invalid file type', 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # 返回保存在服务器上的图片文件
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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


@app.route('/describe_image', methods=['POST'])
def describe_image():
    import time
    start_t = time.time()
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    check_t = time.time()
    image_file = request.files['image']
    # 调用上传图片函数，获取上传后的结果
    image_url, code = upload(image_file=image_file)
    up_t = time.time()
    if code != 200:
        return jsonify({'error': image_url}), code
    # 获取图片描述
    description = get_image_description(image_url)
    llm_t = time.time()
    print(f"upload {up_t-check_t}")
    print(f"des {llm_t-up_t}")
    return jsonify({'description': description}), 200


def test_get_image_description():
    import time
    start_time = time.time()
    des = get_image_description(
        "https://bkimg.cdn.bcebos.com/pic/e7cd7b899e510fb30f2464687e7fdf95d143ac4ba6b2?x-bce-process=image/format,f_auto/watermark,image_d2F0ZXIvYmFpa2UyNzI,g_7,xp_5,yp_5,P_20/resize,m_lfit,limit_1,h_1080")
    print(des)
    print(f"time cost: {time.time() - start_time} s")


if __name__ == '__main__':
    # TODO test
    # test_get_image_description()

    app.run(host='0.0.0.0', port=8101)
