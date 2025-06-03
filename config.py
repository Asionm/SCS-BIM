import os
from langchain.llms import OpenAI
from langchain.llms import Ollama

class LangChainConfig:
    def __init__(
            self,
            provider="ollama",  # 支持 "openai" 或 "ollama"
            api_key=None,
            model_name=None,
            temperature=0.0,
            max_tokens=4096,              # 新增：最大生成长度限制
            openai_base_url=None,        # 第三方OpenAI兼容API基础URL，比如Azure端点
            ollama_model='mistral',
            ollama_host="http://localhost:11434"  # Ollama默认服务地址
    ):
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_tokens = max_tokens

        if self.provider == "openai":
            if api_key is None:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API Key不能为空，传入api_key或设置环境变量OPENAI_API_KEY")
            self.api_key = api_key
            self.model_name = model_name or "gpt-4o-mini"
            self.openai_base_url = openai_base_url  # 保存第三方base_url
            self.ollama_model = None
            self.ollama_host = None

        elif self.provider == "ollama":
            self.api_key = None
            self.model_name = None
            self.ollama_model = ollama_model or "llama2"
            self.ollama_host = ollama_host

        else:
            raise ValueError(f"不支持的provider: {provider}")

    def get_llm(self):
        if self.provider == "openai":
            kwargs = {
                "model_name": self.model_name,
                "temperature": self.temperature,
                "openai_api_key": self.api_key,
                "max_tokens": self.max_tokens,
            }
            if self.openai_base_url:
                kwargs["base_url"] = self.openai_base_url  # 传入第三方基础地址
            return OpenAI(**kwargs)

        elif self.provider == "ollama":
            return Ollama(
                model=self.ollama_model,
                temperature=self.temperature,
                base_url=self.ollama_host,
                max_tokens=self.max_tokens
            )
        else:
            raise ValueError(f"不支持的provider: {self.provider}")


# 用法示例：
config = LangChainConfig(
    provider="openai",
    api_key="xxx",
    model_name="deepseek-ai/DeepSeek-V3",
    openai_base_url="xxx"
)
llm = config.get_llm()

# 或 Ollama
# config = LangChainConfig(provider="ollama", ollama_model="mistral")
# llm = config.get_llm()

