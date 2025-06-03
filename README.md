# 建筑工程施工进度智能编排 (SCS-BIM)
[English ](README_en.md)|[中文](README.md)
## 项目简介
本项目是一个面向建筑工程的施工进度智能编制平台，用户只需上传一份标准 IFC 建筑信息模型文件，系统将自动完成以下任务：

* 解析模型中的构件类型、楼层信息和物理量数据；
* 调用语言模型自动生成构件分类、施工阶段和楼层映射；
* 基于定额库匹配构件对应的工日信息；
* 自动生成合理的施工顺序和任务依赖；
* 根据工日和人员配置估算施工周期；
* 输出甘特图并支持 CSV 进度计划导出。

平台结合 IFC 模型解析、语言模型推理、定额工日估算和甘特图可视化，面向设计单位、施工单位和 BIM 工程师，帮助高效编制建筑施工进度计划。

## 安装与运行指南
### 1. 克隆项目

```bash
git clone https://github.com/Asionm/SCS-BIM
cd SCS-BIM
```

### 2. 安装依赖

建议使用 Python 3.10+ 与虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Windows 使用 venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 启动后端服务

确保本地 Ollama 或 OpenAI 接口可用，并配置好 `config.py` 中的 API 相关信息：

```bash
python app.py
```

默认服务地址为：`http://localhost:5000`

### 4. 启动前端页面

打开源码中的index.html访问， 上传 `.ifc` 文件，平台将自动处理并展示施工甘特图计划。


## 项目结构
以下是根据你项目的文件结构撰写的 `README.md` 中的 **项目结构（Project Structure）** 部分：

---

## 项目结构 | Project Structure
```
SCS-BIM/
│
├── app.py                 # Flask 主程序，处理上传、进度推送和任务调度
├── config.py              # LLM 接口配置，支持 OpenAI 与 Ollama 切换
├── export_sequence.py     # 生成任务列表与施工甘特图数据
├── generate_bill.py       # 从 IFC 提取构件工程量并生成清单
├── index.html             # 前端页面（上传 + 甘特图展示）
├── LLM.py                 # 调用大语言模型，生成施工结构与匹配定额项
├── pre_process.py         # IFC 文件预处理，提取项目信息与构件类别
├── quota_match.py         # 根据定额库计算工日与施工周期
├── requirements.txt       # Python 依赖列表
├── test.py                # 示例/测试脚本入口（可选）
├── README.md              # 项目说明文档
└── static/
    └── ...                # 上传文件与模板配置文件存放目录
```

## 配置说明

本项目支持使用 OpenAI 或本地部署的 Ollama 作为语言模型调用源，相关设置集中在 `config.py` 中的 `LangChainConfig` 类中。

### 1. 模型提供方选择

在 `config.py` 中可以通过 `provider` 参数切换：

```python
LangChainConfig(provider="openai")     # 使用 OpenAI（默认使用环境变量中的 API Key）
LangChainConfig(provider="ollama")     # 使用本地部署的 Ollama 模型
```

### 2. OpenAI 配置项

如使用 OpenAI，请确保设置以下内容：

```python
LangChainConfig(
    provider="openai",
    api_key="your-openai-key",                 # 或设置环境变量 OPENAI_API_KEY
    model_name="gpt-4o",                       # 可替换为 gpt-4o, gpt-3.5-turbo 等
    openai_base_url="https://api.openai.com"   # 如使用第三方兼容接口，请替换此地址
)
```

### 3. Ollama 配置项

如使用 Ollama 本地模型（推荐部署 `mistral`, `llama3` 等）：

```python
LangChainConfig(
    provider="ollama",
    ollama_model="mistral",                     # 模型名称
    ollama_host="http://localhost:11434"        # Ollama 默认服务地址
)
```

确保本地 Ollama 服务已运行并已加载相应模型。

## 功能介绍

### 1. IFC 文件上传与预处理

* 支持上传标准 `.ifc` 格式建筑信息模型文件
* 自动提取项目信息、楼层结构、构件类型等基础数据

### 2. 工程信息结构生成（LLM 支持）

* 利用大语言模型（如 OpenAI 或 Ollama）
* 自动生成构件分类、施工阶段、楼层映射等结构化 JSON 配置
* 支持语义补全和容错推理

### 3. 工程量清单智能生成

* 分析模型中构件的体积、面积、数量等信息
* 结合结构配置输出标准工程量清单

### 4. 定额匹配与工日估算

* 将构件类别自动匹配到定额库中对应的条目
* 结合单位工程量计算总工日，并根据工人数量估算施工周期
* 支持边际效率模拟（工人增加不线性提速）

### 5. 施工顺序自动推理

* 使用语言模型分析施工阶段间的依赖关系
* 自动构建任务 ID、施工阶段、组件及其先后顺序

### 6. 进度计划输出与可视化

* 生成可导入 Microsoft Project 的任务表（CSV 格式）
* 提供基于 dhtmlxGantt 的甘特图展示
* 支持日 / 周 / 月 / 季度 / 年视图切换


## 示例展示
<video controls width="800">
  <source src="https://github.com/Asionm/SCS-BIM/blob/main/docs/demo.mp4" type="video/mp4">
  您的浏览器不支持视频播放。
</video>