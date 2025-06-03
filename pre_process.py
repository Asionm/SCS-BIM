import ifcopenshell

def preprocess_ifc_model_full(ifc_path):
    """
    预处理IFC模型，提取项目元数据、单位、楼层和构件类别等基础信息

    参数:
        ifc_path (str): IFC文件路径

    返回:
        dict: 含项目元数据、单位、楼层列表、构件类别列表的字典
    """
    ifc_file = ifcopenshell.open(ifc_path)
    metadata = {}
    # 项目信息
    project = ifc_file.by_type("IfcProject")
    if project:
        proj = project[0]
        metadata["project_name"] = proj.LongName or proj.Name or "未命名项目"
        metadata["project_description"] = getattr(proj, "Description", "")
        metadata["project_identifier"] = getattr(proj, "Identifier", "")
        # 创建者和创建时间
        owner_hist = getattr(proj, "OwnerHistory", None)
        if owner_hist:
            user = getattr(owner_hist.OwningUser, "Identification", "") if owner_hist.OwningUser else ""
            metadata["owner_user"] = user
            creation_date = getattr(owner_hist, "CreationDate", None)
            metadata["creation_date"] = creation_date
    # 单位信息
    units = {"length": None, "area": None, "volume": None}
    unit_assignments = ifc_file.by_type("IfcUnitAssignment")
    if unit_assignments:
        for unit in unit_assignments[0].Units:
            if unit.UnitType == "LENGTHUNIT":
                units["length"] = getattr(unit, "Name", str(unit))
            elif unit.UnitType == "AREAUNIT":
                units["area"] = getattr(unit, "Name", str(unit))
            elif unit.UnitType == "VOLUMEUNIT":
                units["volume"] = getattr(unit, "Name", str(unit))
    metadata["units"] = units

    # 建筑物信息
    buildings = ifc_file.by_type("IfcBuilding")
    if buildings:
        bld = buildings[0]
        metadata["building_name"] = getattr(bld, "Name", "")
        metadata["building_elevation"] = getattr(bld, "ElevationOfRefHeight", None)

    # 楼层列表
    building_storeys = ifc_file.by_type("IfcBuildingStorey")
    metadata["levels"] = [storey.Name if storey.Name else "未命名楼层" for storey in building_storeys]

    # 构件类别列表（去重）
    products = ifc_file.by_type("IfcProduct")
    category_set = set(prod.is_a() for prod in products)
    metadata["categories"] = sorted(list(category_set))

    return metadata

