import json
import csv
import re
from collections import defaultdict
from datetime import timedelta, date

def generate_ms_project_tasks(template, project_data):
    quantities = project_data["quantities"]
    project_name = project_data["project_name"]

    by_level_category = defaultdict(dict)
    for item in quantities:
        level = item["level"]
        category = item["category"]
        by_level_category[level][category] = item

    def sort_levels(levels):
        def level_key(lv):
            match = re.search(r"(\d+)", lv)
            return int(match.group(1)) if match else 0
        return sorted(set(levels), key=level_key)

    all_levels = sort_levels(by_level_category.keys())

    task_rows = []
    id_map = {}
    row_id = 1

    for i, level in enumerate(all_levels):
        prev_level = all_levels[i - 1] if i > 0 else ""

        for step_def in template["phase_sequence"]:
            task_id = step_def["id"].replace("{level}", level).replace("{prev_level}", prev_level)
            desc = step_def["description"].replace("{level}", level)
            depends_raw = step_def.get("depends_on", "")
            depends_id = depends_raw.replace("{level}", level).replace("{prev_level}", prev_level)

            categories = []
            revit_categories = []
            total_work_day = 0.0

            for comp in step_def["components"]:
                cat = comp["category"]
                item = by_level_category[level].get(cat)
                if item:
                    categories.append(cat)
                    revit_categories.append(item.get("revit_category", "未知"))
                    wd = item.get("estimated_days")
                    if wd is not None:
                        total_work_day += wd

            if categories:
                row = {
                    "ID": row_id,
                    "TaskID": task_id,
                    "Name": desc,
                    "Duration": round(total_work_day, 2),
                    "Predecessors": "",  # 先留空，后面填
                    "Level": level,
                    "Phase": step_def["phase"],
                    "Category": " / ".join(categories),
                    "RevitCategory": " / ".join(revit_categories)
                }
                id_map[task_id] = row_id
                task_rows.append(row)
                row_id += 1

    # 填充 Predecessors，保证替换 prev_level 一致
    for i, level in enumerate(all_levels):
        prev_level = all_levels[i - 1] if i > 0 else ""
        for row in task_rows:
            if row["Level"] == level:
                for step_def in template["phase_sequence"]:
                    expected_id = step_def["id"].replace("{level}", level).replace("{prev_level}", prev_level)
                    if expected_id == row["TaskID"]:
                        depends_raw = step_def.get("depends_on", "")
                        if depends_raw:
                            depends_id = depends_raw.replace("{level}", level).replace("{prev_level}", prev_level)
                            if depends_id in id_map:
                                row["Predecessors"] = id_map[depends_id]

    return {
        "project_name": project_name,
        "tasks": task_rows
    }

def generate_simple_schedule(tasks, project_start_date=None):
    id_to_task = {task["ID"]: task for task in tasks}
    scheduled = {}

    if project_start_date is None:
        project_start_date = date.today()

    def compute_timing(task_id):
        task = id_to_task[task_id]
        pred_id = task.get("Predecessors")
        duration = task["Duration"] or 0
        if pred_id:
            if pred_id not in scheduled:
                compute_timing(pred_id)
            start = scheduled[pred_id]["end"]
        else:
            start = project_start_date
        end = start + timedelta(days=duration)
        scheduled[task_id] = {
            "name": task["Name"],
            "start": start,
            "end": end
        }

    for task_id in id_to_task:
        if task_id not in scheduled:
            compute_timing(task_id)

    output = []
    for task_id in sorted(scheduled):
        row = scheduled[task_id]
        output.append({
            "name": row["name"],
            "start": row["start"].isoformat(),
            "end": row["end"].isoformat()
        })

    return output


def main():
    # 读取模板
    with open("static/template.json", "r", encoding="utf-8") as f:
        template = json.load(f)

    # 读取项目数据
    with open("static/updated_project.json", "r", encoding="utf-8") as f:
        project_data = json.load(f)

    # 生成任务计划
    result = generate_ms_project_tasks(template, project_data)

    # 写入详细任务文件（供 MS Project 使用）
    with open("ms_project_tasks.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ID", "TaskID", "Name", "Duration", "Predecessors",
            "Level", "Phase", "Category", "RevitCategory"
        ])
        writer.writeheader()
        for row in result["tasks"]:
            row_copy = row.copy()
            # Duration为0时设为空
            if row_copy["Duration"] == 0:
                row_copy["Duration"] = ""
            writer.writerow(row_copy)

    # 写入简化计划（仅名称、真实时间）
    simple_schedule = generate_simple_schedule(result["tasks"])
    with open("simple_schedule.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["名称", "开始时间", "结束时间"])
        writer.writeheader()
        for row in simple_schedule:
            writer.writerow(row)

    print("✅ 已生成 ms_project_tasks.csv 和 simple_schedule.csv（含真实日期）")
