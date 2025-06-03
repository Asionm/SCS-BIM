from LLM import generate_project_info, extract_json_from_text, match_quota_name, generate_construction_sequence
from export_sequence import generate_ms_project_tasks, generate_simple_schedule
from generate_bill import generateBillWithConfig
from pre_process import preprocess_ifc_model_full
import json

from quota_match import update_project_work_days


def main():
    info_text = preprocess_ifc_model_full('static/building.ifc')
    result = generate_project_info(info_text)
    project_info = extract_json_from_text(result)
    project_info = generateBillWithConfig('static/building.ifc', project_info)
    with open("static/quota.json", "r", encoding="utf-8") as f:
        quota_data = json.load(f)
        # 将列表转换为字典：{ "混凝土矩形柱": {...}, ... }
        quota_dict = {item["name"]: item for item in quota_data}
    # 从project_data中提取所有工程类别（category），去重
    categories = set()
    for item in project_info['quantities']:
        category = item.get("category")
        if category:
            categories.add(category)
    category_to_quota = {}
    for category in categories:
        quota_name = match_quota_name(category, quota_dict)
        category_to_quota[category] = quota_name
    print(category_to_quota)
    updated_project_data = update_project_work_days(project_info, quota_dict, category_to_quota, num_workers=10)
    print(updated_project_data)
    construction_seq = generate_construction_sequence(str(category_to_quota.values()))
    construction_seq = extract_json_from_text(construction_seq)
    print(construction_seq)
    result = generate_ms_project_tasks(construction_seq, updated_project_data)
    simple_schedule = generate_simple_schedule(result["tasks"])
    print(simple_schedule)



if __name__ == "__main__":
    main()
