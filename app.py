from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
import tempfile
import json

from LLM import match_quota_name, generate_construction_sequence, extract_json_from_text, generate_project_info
from pre_process import preprocess_ifc_model_full
from generate_bill import generateBillWithConfig
from quota_match import update_project_work_days
from export_sequence import generate_ms_project_tasks, generate_simple_schedule
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # 允许所有跨域请求，开发环境用
socketio = SocketIO(app, cors_allowed_origins="*")

# 用于保存上传文件的临时目录
UPLOAD_FOLDER = './static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 保存为临时文件，保证唯一
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(temp_path)

    # 返回文件路径或者文件名给客户端
    return jsonify({"message": "File uploaded", "filepath": temp_path})

@socketio.on('start_processing')
def handle_start_processing(data):
    filepath = data.get('filepath')
    if not filepath or not os.path.isfile(filepath):
        emit('error', {'message': 'File not found or filepath missing'})
        return
    DEBUG_MODE = False
    DEBUG_CSV_PATH = 'simple_schedule.csv'
    import traceback
    try:
        # Debug 模式下直接读取 CSV，返回数据
        if DEBUG_MODE:
            import csv
            schedule = []
            with open(DEBUG_CSV_PATH, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    schedule.append({
                        "name": row.get("名称"),
                        "start": row.get("开始时间"),
                        "end": row.get("结束时间")
                    })
            emit('done', {'schedule': schedule})

        emit('progress', {'step': 'preprocess', 'message': '开始预处理IFC文件'})
        info_text = preprocess_ifc_model_full(filepath)
        print(json.dumps(info_text, ensure_ascii=False, indent=4), '\n\n\n')
        result = generate_project_info(info_text)
        project_info = extract_json_from_text(result)
        emit('progress', {'step': 'generate_bill', 'message': '生成工程量清单'})
        project_info = generateBillWithConfig(filepath, project_info)
        print(json.dumps(project_info, ensure_ascii=False, indent=4), '\n\n\n')
        emit('progress', {'step': 'load_quota', 'message': '加载定额数据'})
        quota_path = os.path.join(app.config['UPLOAD_FOLDER'], 'quota.json')
        with open(quota_path, "r", encoding="utf-8") as f:
            quota_data = json.load(f)
        quota_dict = {item["name"]: item for item in quota_data}

        emit('progress', {'step': 'match_work_days', 'message': '匹配工日'})
        categories = set(item.get("category") for item in project_info.get('quantities', []) if item.get("category"))
        category_to_quota = {cat: match_quota_name(cat, quota_dict) for cat in categories}

        updated_project_data = update_project_work_days(project_info, quota_dict, category_to_quota, num_workers=10)
        print(json.dumps(updated_project_data, ensure_ascii=False, indent=4), '\n\n\n')
        emit('progress', {'step': 'generate_sequence', 'message': '生成施工顺序'})
        construction_seq_text = generate_construction_sequence(str(category_to_quota.keys()))
        construction_seq = extract_json_from_text(construction_seq_text)
        print(json.dumps(construction_seq, ensure_ascii=False, indent=4), '\n\n\n')
        emit('progress', {'step': 'generate_schedule', 'message': '生成施工进度'})
        result = generate_ms_project_tasks(construction_seq, updated_project_data)
        simple_schedule = generate_simple_schedule(result["tasks"])
        emit('done', {'schedule': simple_schedule})

    except Exception as e:
        print(traceback.format_exc())
        emit('error', {'message': str(e)})
    finally:
        # 处理完成后删除临时文件（如果需要）
        try:
            os.remove(filepath)
        except Exception:
            pass



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

