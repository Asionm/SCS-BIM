# Smart Construction Scheduling (SCS-BIM)

[中文](README.md) | [English](README_en.md)

## Project Overview

This project is an intelligent construction scheduling platform for building engineering. Users simply upload a standard IFC (Industry Foundation Classes) building information model, and the system will automatically:

* Parse component types, floor levels, and physical quantities from the model
* Use language models to auto-generate component classification, construction phases, and floor mappings
* Match components with labor quotas to estimate workdays
* Generate logical construction sequences and task dependencies
* Estimate construction duration based on labor input
* Output a Gantt chart and support CSV schedule export

The platform integrates IFC parsing, LLM reasoning, labor quota estimation, and Gantt visualization. It is designed for design firms, construction teams, and BIM engineers to efficiently generate construction schedules.

---

## Installation & Running Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Asionm/SCS-BIM
cd SCS-BIM
```

### 2. Install Dependencies

It is recommended to use Python 3.10+ and a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Backend Server

Ensure OpenAI or local Ollama is properly configured in `config.py`:

```bash
python app.py
```

Default backend address: `http://localhost:5000`

### 4. Launch Frontend

Open `index.html` in your browser, upload an `.ifc` file, and the system will process and visualize the construction schedule as a Gantt chart.

---

## Project Structure

```
SCS-BIM/
│
├── app.py                 # Flask app: upload handler, scheduling, WebSocket
├── config.py              # LLM configuration for OpenAI or Ollama
├── export_sequence.py     # Generate tasks and Gantt schedule
├── generate_bill.py       # Extract quantities from IFC and generate bill
├── index.html             # Frontend interface for upload and Gantt display
├── LLM.py                 # Language model prompts for classification, quota, and sequence
├── pre_process.py         # Extract metadata from IFC files
├── quota_match.py         # Match components to quota and calculate workdays
├── requirements.txt       # Python dependency list
├── test.py                # Optional: test/demo entry
└── static/
    └── ...                # Uploads and configuration templates
```

---

## Configuration

This project supports both OpenAI and locally hosted Ollama as LLM backends. Configuration is defined in `config.py` under the `LangChainConfig` class.

### 1. Choose LLM Provider

```python
LangChainConfig(provider="openai")   # Default, use OpenAI
LangChainConfig(provider="ollama")   # Use locally hosted Ollama
```

### 2. OpenAI Settings

Set the following if using OpenAI:

```python
LangChainConfig(
    provider="openai",
    api_key="your-openai-key",                   # Or use OPENAI_API_KEY env var
    model_name="gpt-4o",                         # e.g., gpt-4o, gpt-3.5-turbo
    openai_base_url="https://api.openai.com"     # Replace if using a proxy
)
```

### 3. Ollama Settings

For local inference with Ollama (e.g., `mistral`, `llama3`):

```python
LangChainConfig(
    provider="ollama",
    ollama_model="mistral",
    ollama_host="http://localhost:11434"
)
```

Ensure Ollama is running and the model is loaded.

---

## Features

### 1. IFC Upload & Preprocessing

* Supports `.ifc` model upload
* Extracts floors, components, quantities, and metadata

### 2. LLM-based Structure Generation

* Auto-generates structured JSON for phases, categories, and floors
* Uses OpenAI or Ollama for semantic understanding
* Supports error-tolerant inference and default values

### 3. Bill of Quantities Generation

* Analyzes component volume, area, length, and count
* Structured output of component quantities

### 4. Quota Matching & Workday Estimation

* Maps components to labor quota items
* Calculates workdays per unit quantity
* Supports adjustable labor input with marginal efficiency (diminishing returns)

### 5. Construction Sequence Generation

* Automatically generates task IDs, phases, dependencies
* Uses LLM to infer logical construction order
* Supports parallel stages and floor iteration

### 6. Schedule Visualization

* Outputs CSV compatible with Microsoft Project
* Interactive Gantt chart via dhtmlxGantt
* Supports daily, weekly, monthly, quarterly, and yearly views

---

## Demo

<video controls width="800">
  <source src="https://github.com/Asionm/SCS-BIM/raw/main/docs/demo.mp4" type="video/mp4">
  您的浏览器不支持视频播放。
</video>



