import json
import ifcopenshell
from collections import defaultdict

def generateBillWithConfig(ifc_path: str, config: dict):
    ifc_file = ifcopenshell.open(ifc_path)

    category_map = {}
    for comp in config.get("components", []):
        for cat in comp.get("revit_categories", []):
            category_map[cat] = (comp["name"], comp["phase"])

    level_map = config.get("level_mapping", {})

    all_products = ifc_file.by_type("IfcProduct")
    stats = defaultdict(lambda: {"count": 0, "volume": 0.0, "area": 0.0, "length": 0.0})

    def get_storey(element):
        if hasattr(element, "ContainedInStructure") and element.ContainedInStructure:
            for rel in element.ContainedInStructure:
                s = rel.RelatingStructure
                if s.is_a("IfcBuildingStorey"):
                    return s.Name
        return "未指定楼层"

    for prod in all_products:
        if not prod.is_a("IfcElement"):
            continue

        revit_cat = prod.is_a()
        if revit_cat not in category_map:
            continue

        business_name, phase = category_map[revit_cat]

        volume = 0
        area = 0
        length = 0
        for definition in getattr(prod, "IsDefinedBy", []):
            if definition.is_a("IfcRelDefinesByProperties"):
                pset = definition.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet"):
                    for prop in getattr(pset, "HasProperties", []):
                        if prop.is_a("IfcPropertySingleValue"):
                            val = prop.NominalValue
                            if val is None:
                                continue
                            if prop.Name == "体积" and hasattr(val, "wrappedValue"):
                                volume = val.wrappedValue
                            elif prop.Name == "面积" and hasattr(val, "wrappedValue"):
                                area = val.wrappedValue
                            elif prop.Name == "长度" and hasattr(val, "wrappedValue"):
                                length = val.wrappedValue

        storey = get_storey(prod)
        if storey == "未指定楼层":
            continue  # 跳过该元素

        level_name = level_map.get(storey, storey)

        key = (phase, level_name, business_name, revit_cat)
        stat = stats[key]
        stat["count"] += 1
        stat["volume"] += volume
        stat["area"] += area
        stat["length"] += length

    # ========== 参数 ==========
    excavation_depth = config.get("default_excavation_depth", 3.0)
    default_excavation_area = config.get("default_excavation_area", 0.0)

    # 用墙体体积作为参考的梁柱估算比例
    column_ratio_wall = config.get("default_column_volume_ratio_by_wall", 0.2)
    beam_ratio_wall = config.get("default_beam_volume_ratio_by_wall", 0.3)

    # 若无墙体则使用楼板兜底
    column_ratio_slab = config.get("default_column_volume_ratio", 0.1)
    beam_ratio_slab = config.get("default_beam_volume_ratio", 0.15)

    # ========== 土方工程估算 ==========
    earthwork_components = [c for c in config.get("components", []) if "土方" in c["phase"] or "土方" in c["name"]]
    if not earthwork_components:
        default_earthwork = {
            "name": "土方工程",
            "revit_categories": ["IfcEarthworks"],
            "phase": "土方工程"
        }
        for cat in default_earthwork["revit_categories"]:
            if cat not in category_map:
                category_map[cat] = (default_earthwork["name"], default_earthwork["phase"])
        earthwork_components = [default_earthwork]

    for earthwork in earthwork_components:
        default_level = next(
            (v for k, v in level_map.items() if "地基" in v or "基础" in v or "土方" in v),
            "地基"
        )
        key = (earthwork["phase"], default_level, earthwork["name"], earthwork["revit_categories"][0])
        if key not in stats:
            stats[key] = {"count": 0, "volume": 0.0, "area": 0.0, "length": 0.0}
        stat = stats[key]

        if stat["area"] == 0.0:
            estimated_area = sum(
                k_data["area"]
                for (k_phase, k_level, k_name, k_cat), k_data in stats.items()
                if k_cat == "IfcSlab" and k_level in ("1F", "室外地坪")
            )
            if estimated_area == 0.0:
                estimated_area = default_excavation_area
            stat["area"] = estimated_area

        if stat["volume"] == 0.0 and stat["area"] > 0:
            stat["volume"] = stat["area"] * excavation_depth

    # ========== 梁柱估算逻辑：优先墙体体积 ==========
    wall_volume_by_level = defaultdict(float)
    slab_volume_by_level = defaultdict(float)

    for (phase, level, category, revit_cat), data in stats.items():
        if revit_cat in ("IfcWall", "IfcWallStandardCase"):
            wall_volume_by_level[level] += data["volume"]
        elif revit_cat == "IfcSlab":
            slab_volume_by_level[level] += data["volume"]

    has_column = any(revit_cat == "IfcColumn" for (_, _, _, revit_cat) in stats)
    has_beam = any(revit_cat == "IfcBeam" for (_, _, _, revit_cat) in stats)

    if not has_column:
        for level in set(wall_volume_by_level.keys()).union(slab_volume_by_level.keys()):
            base_volume = wall_volume_by_level.get(level, 0.0)
            if base_volume == 0.0:
                base_volume = slab_volume_by_level.get(level, 0.0)
                ratio = column_ratio_slab
            else:
                ratio = column_ratio_wall
            stats[("主体工程", level, "柱", "IfcColumn")] = {
                "count": 0,
                "volume": base_volume * ratio,
                "area": 0.0,
                "length": 0.0
            }

    if not has_beam:
        for level in set(wall_volume_by_level.keys()).union(slab_volume_by_level.keys()):
            base_volume = wall_volume_by_level.get(level, 0.0)
            if base_volume == 0.0:
                base_volume = slab_volume_by_level.get(level, 0.0)
                ratio = beam_ratio_slab
            else:
                ratio = beam_ratio_wall
            stats[("主体工程", level, "梁", "IfcBeam")] = {
                "count": 0,
                "volume": base_volume * ratio,
                "area": 0.0,
                "length": 0.0
            }

    # ========== 输出结果 ==========
    result_list = []
    for (phase, level, category, revit_cat), data in stats.items():
        result_list.append({
            "phase": phase,
            "level": level,
            "category": category,
            "revit_category": revit_cat,
            "count": data["count"],
            "volume_m3": round(data["volume"], 3),
            "area_m2": round(data["area"], 3) if data["area"] > 0 else None,
            "length_m": round(data["length"], 3) if data["length"] > 0 else None,
        })

    output = {
        "project_name": config.get("project_name", ""),
        "quantities": result_list,
        "user_input": {
            "default_excavation_depth": excavation_depth,
            "default_excavation_area": default_excavation_area,
            "default_column_volume_ratio_by_wall": column_ratio_wall,
            "default_beam_volume_ratio_by_wall": beam_ratio_wall,
            "default_column_volume_ratio": column_ratio_slab,
            "default_beam_volume_ratio": beam_ratio_slab
        }
    }

    return output
