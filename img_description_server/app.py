from PIL import Image
from openai import OpenAI
from flask import Flask, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import configparser

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

PROMPT = "Briefly describe the information in this picture. If this is a photo you see, what might you do next? Please provide four options."

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


@app.route('/describe_image', methods=['POST'])
def describe_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    # 调用上传图片函数，获取上传后的结果
    image_url, code = upload(image_file=image_file)
    if code != 200:
        return jsonify({'error': image_url}), code
    # 获取图片描述
    description = get_image_description(image_url)

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
