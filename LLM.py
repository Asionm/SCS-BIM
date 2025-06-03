# 接口1：实际工程内容与IFC的对应关系生成
# prompt1
'''
请根据以下输入的信息<info>{{info}}</info>，生成一个JSON格式的工程信息描述，包含以下内容：

{
  "project_name": "工程名称，字符串",
  "default_excavation_depth": 数值，单位米，示例：3.0,
  "default_column_volume_ratio_by_wall": 数值，示例：0.2,
  "default_beam_volume_ratio_by_wall": 数值，示例：0.3,
  "components": [
    {
      "name": "组件名称，例如楼板、楼梯等",
      "revit_categories": ["Ifc类别名称列表，如IfcWall", "IfcWallStandardCase"],
      "phase": "施工阶段，如主体工程、砌筑工程等"
    }
  ],
  "level_mapping": {
    "IFC楼层名称": "对应的工程楼层名称",
    "标高 1": "1F",
    "标高 2": "2F",
    "标高 3": "3F",
    "...": "..."
  }
}

请注意：
1. 楼层映射中，室外或地下等特殊层级可根据实际情况选择性包含或排除。
2. 组件列表应涵盖本项目的主要结构和施工单元，不包含非土建专业内容，如门窗安装、水电设备等。
3. 输出应保持标准JSON格式，字段名及类型应严格遵守示例规范。
4. 若信息中缺少某些字段，可根据上下文合理推断或使用默认值。
5. 结构清晰，避免添加无关描述或多余信息。

请严格按照上述格式输出，确保方便后续程序解析。
'''
from langchain import LLMChain, PromptTemplate
from config import config
import re
import json

def extract_json_from_text(text: str):
    # 匹配第一个 {...}，不支持深度嵌套
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("未找到JSON格式内容")
    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {e}")

def generate_project_info(info: str) -> str:
    prompt_text = """
    请根据以下输入的信息<info>{info}</info>，生成一个JSON格式的工程信息描述，包含以下内容：

    {{
      "project_name": "工程名称，字符串",
      "default_excavation_depth": 数值，单位米，示例：3.0,
      "default_column_volume_ratio_by_wall": 数值，示例：0.2,
      "default_beam_volume_ratio_by_wall": 数值，示例：0.3,
      "components": [
        {{
          "name": "组件名称，例如楼板、楼梯等",
          "revit_categories": ["Ifc类别名称列表，如IfcWall", "IfcWallStandardCase"],
          "phase": "施工阶段，如主体工程、砌筑工程等"
        }}
      ],
      "level_mapping": {{
        "IFC楼层名称": "对应的工程楼层名称",
        "标高 1": "1F",
        "标高 2": "2F",
        "标高 3": "3F",
        "..."
      }}
    }}

    请注意：
    1. 楼层映射中，室外地坪直接去掉。
    2. 组件列表应涵盖本项目的主要结构和施工单元，不包含非土建专业内容，如门窗安装、水电设备等。与土建无关的直接删除！！！
    3. 输出应保持标准JSON格式，字段名及类型应严格遵守示例规范。
    4. 若信息中缺少某些字段，可根据上下文合理推断或使用默认值。
    5. 结构清晰，避免添加无关描述或多余信息。

    请严格按照上述格式输出，确保方便后续程序解析，请严格只输出JSON格式的结果，不要包含任何代码块标记（比如```json```）。
    """

    prompt = PromptTemplate(input_variables=["info"], template=prompt_text)
    llm = config.get_llm()
    chain = LLMChain(llm=llm, prompt=prompt)

    result = chain.run(info=info)
    return result


# 接口2：工程与定额关系匹配
# prompt2
'''
请根据下面的定额库内容，从中找到与目标实体名称 "**{{entity}}**" 最相近的定额名称，并只返回该定额的名称字符串。

要求：
1. 只输出定额名称，无其他文本。
2. 定额库包含若干定额项，名称和相关信息已列出。
3. 依据名称或语义匹配选择最合适的定额。
4. 不返回多个结果，只返回一个最匹配的名称。

定额库内容如下：
<quota>
{{quota}}
</quota>

'''
def match_quota_name(entity: str, quota: str) -> str:
    prompt_text = '''
请根据下面的定额库内容，从中找到与目标实体名称 "**{entity}**" 最相近的定额名称，并只返回该定额的名称字符串。

要求：
1. 只输出定额名称，无其他文本。
2. 定额库包含若干定额项，名称和相关信息已列出。
3. 依据名称或语义匹配选择最合适的定额。
4. 不返回多个结果，只返回一个最匹配的名称。

定额库内容如下：
<quota>
{quota}
</quota>
'''
    prompt = PromptTemplate(input_variables=["entity", "quota"], template=prompt_text)
    llm = config.get_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(entity=entity, quota=quota)
    return result.strip()

# 接口3：施工顺序编制
# prompt3
'''
请根据以下提供的工程内容<project>{{project}}</project>，编制施工顺序计划，包含可同时进行的施工阶段。

输出格式应为JSON对象，示例如下：

{
  "repeat_by_floor": True,
  "phase_sequence": [
    {
      "id": "T-{level}-EXCAV",
      "phase": "土方工程",
      "description": "{level} 土方开挖",
      "components": [
        {"category": "土方工程"}
      ]
    },
    {
      "id": "T-{level}-SLAB",
      "phase": "主体工程",
      "description": "{level} 楼板施工",
      "components": [
        {"category": "楼板"}
      ],
      "depends_on": "T-{prev_level}-BEAM"
    },
    {
      "id": "T-{level}-COLUMN",
      "phase": "主体工程",
      "description": "{level} 柱施工",
      "components": [
        {"category": "柱"}
      ],
      "depends_on": "T-{level}-SLAB"
    },
    {
      "id": "T-{level}-WALL",
      "phase": "砌筑工程",
      "description": "{level} 砌筑墙施工",
      "components": [
        {"category": "砌筑墙"}
      ],
      "depends_on": "T-{level}-SLAB"
    },
    {
      "id": "T-{level}-BEAM",
      "phase": "主体工程",
      "description": "{level} 梁施工",
      "components": [
        {"category": "梁"}
      ],
      "depends_on": "T-{level}-COLUMN"
    },
    {
      "id": "T-{level}-STAIR",
      "phase": "主体工程",
      "description": "{level} 楼梯施工",
      "components": [
        {"category": "楼梯"}
      ],
      "depends_on": "T-{level}-BEAM"
    }
  ]
}

请注意：
1. 施工顺序应合理反映施工逻辑及依赖关系。
2. 支持并行施工的阶段可不设置依赖字段。
3. 保持输出JSON格式规范，字段名称和类型应与示例匹配。
4. {level} 和 {prev_level} 是楼层占位符，输出中保持此格式即可。
5. 输出中不要包含除JSON之外的任何说明或文本。

请严格按照上述格式输出施工顺序数据。
'''
def generate_construction_sequence(project: str) -> str:
    prompt_text = '''
    请根据以下提供的工程内容<project>{project}</project>，编制施工顺序计划，包含可同时进行的施工阶段。
    6. 注意柱子的施工取决于楼板是否建好，而不是取决于土方工程。没有如何东西是依赖EXCAV的，没有依赖也是可以的
    输出格式应为JSON对象，示例如下：

    {{
      "repeat_by_floor": true,
      "phase_sequence": [
        {{
          "id": "T-{{level}}-EXCAV",
          "phase": "土方工程",
          "description": "{{level}} 土方开挖",
          "components": [
            {{"category": "土方工程"}}
          ]
        }},
        {{
          "id": "T-{{level}}-SLAB",
          "phase": "主体工程",
          "description": "{{level}} 楼板施工",
          "components": [
            {{"category": "楼板"}}
          ],
          "depends_on": "T-{{prev_level}}-BEAM"
        }},
        {{
          "id": "T-{{level}}-COLUMN",
          "phase": "主体工程",
          "description": "{{level}} 柱施工",
          "components": [
            {{"category": "柱"}}
          ],
          "depends_on": "T-{{level}}-SLAB"
        }}
      ]
    }}

    请注意：
    1. 施工顺序应合理反映施工逻辑及依赖关系。
    2. 支持并行施工的阶段可不设置依赖字段。
    3. 保持输出JSON格式规范，字段名称和类型应与示例匹配。
    4. {{level}} 和 {{prev_level}} 是楼层占位符，输出中保持此格式即可。
    5. 输出中不要包含除JSON之外的任何说明或文本。
    6. 注意柱子的施工取决于楼板是否建好，而不是取决于土方工程

    请严格按照上述格式输出施工顺序数据。
    '''
    prompt = PromptTemplate(input_variables=["project"], template=prompt_text)
    llm = config.get_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run(project=project)
    return result.strip()
