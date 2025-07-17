from flask import Flask, request, jsonify, send_from_directory
import os
import torch
from PIL import Image
from datetime import datetime
import mysql.connector

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
LABELS_FOLDER = os.path.join(RESULT_FOLDER, 'labels')
MODEL_PATH = 'models/yolov5s.pt'
YOLOV5_PATH = 'yolov5'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LABELS_FOLDER, exist_ok=True)

model = torch.hub.load(YOLOV5_PATH, 'custom', path=MODEL_PATH, source='local')

# MySQL データベースの設定
db_config = {
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'database': 'trashnavi'
}

def save_to_mysql(filename, num_objects, status, result_image_path, detections):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    query = "INSERT INTO detections (filename, num_objects, status, result_image_path, detections) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (filename, num_objects, status, result_image_path, detections))
    connection.commit()
    cursor.close()
    connection.close()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/detect', methods=['POST'])
def detect_objects():
    if 'image' not in request.files:
        return jsonify({'error': '画像ファイルが見つかりません'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'ファイル名が空です'}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    img = Image.open(filepath).convert("RGB")
    results = model(img)
    detections = results.pandas().xyxy[0].to_dict()
    num_objects = len(detections)

    print(f"検出数: {num_objects}")
    print(detections)

    if num_objects == 0:
        status = "何もなし"
    elif 1 <= num_objects <= 4:
        status = "やんわり注意"
    else:
        status = "注意通告"

    results.save(save_dir=LABELS_FOLDER)
    result_image_path = f"/{LABELS_FOLDER}/{filename.split('.')[0]}.jpg"

    # MySQL に保存
    save_to_mysql(filename, num_objects, status, result_image_path, str(detections))

    return jsonify({
        'filename': filename,
        'num_objects': num_objects,
        'status': status,
        'result_image': result_image_path,
        'detections': detections
    })

@app.route('/results/labels/<path:filename>', methods=['GET'])
def get_result_image(filename):
    return send_from_directory(LABELS_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
