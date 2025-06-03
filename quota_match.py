def update_project_work_days(project_data, quota_data, category_to_quota_map, num_workers=1):
    """
    根据定额库和构件映射更新项目数据中的工日信息，并考虑工人数量对总工期的影响。

    :param project_data: 已加载的项目 JSON 数据（字典）
    :param quota_data: 已加载的定额库 JSON 数据（字典）
    :param category_to_quota_map: 构件类别到定额名称的映射字典
    :param num_workers: 参与施工的工人数量（默认 1）
    :return: 更新后的项目数据（包含计算后的工日和预计天数）
    """

    def worker_efficiency(n):
        """
        根据工人数返回效率因子。模拟边际效应递减。
        可调整逻辑：这里简单使用 log 函数模拟递减效益。
        """
        import math
        return math.log(n + 1, 2)  # log2(n + 1)，避免 n=0 时出错

    efficiency = worker_efficiency(num_workers)

    for item in project_data["quantities"]:
        category = item["category"]
        quota_name = category_to_quota_map.get(category)

        if quota_name and quota_name in quota_data:
            quota = quota_data[quota_name]
            unit = quota["unit"]
            work_day_per_10 = quota["labor_days"]

            work_day = None
            if "m³" in unit and item.get("volume_m3"):
                volume = item["volume_m3"]
                work_day = (work_day_per_10 / 10) * volume
            elif "m²" in unit and item.get("area_m2"):
                area = item["area_m2"]
                work_day = (work_day_per_10 / 10) * area

            if work_day is not None:
                item["work_day"] = round(work_day, 2)
                item["estimated_days"] = round(work_day / efficiency, 2)  # 实际工期估算（天）
            else:
                item["work_day"] = None
                item["estimated_days"] = None
        else:
            item["work_day"] = None
            item["estimated_days"] = None

    return project_data