import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
import requests
from dotenv import load_dotenv

# 載入環境變數檔案 (.env)
load_dotenv()

@dataclass
class ModelConfig:
    """
    模型配置資料類別
    用於儲存每個 AI 模型的配置資訊
    """
    name: str           # 模型的實際名稱（API 使用的名稱）
    provider: str       # 提供者名稱（如 'stima'）
    available: bool     # 模型是否可用
    display_name: str   # 顯示給使用者看的友善名稱
    
class LLMManager:
    """
    LLM (大型語言模型) 管理器
    負責管理和調用各種 AI 模型，透過 Stima API 提供統一的介面
    """
    
    def __init__(self):
        """初始化 LLM 管理器"""
        self.client = None                             # OpenAI 客戶端實例
        self.models = self._initialize_models()        # 初始化可用模型字典
        self.is_connected = False                      # API 連接狀態標記
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """
        初始化 Stima API 和模型列表
        
        Returns:
            Dict[str, ModelConfig]: 模型配置字典，key 為模型名稱，value 為 ModelConfig 物件
        """
        models = {}  # 儲存所有模型配置的字典
        
        # ========== Stima API 設定 ==========
        # 從環境變數取得 API 金鑰
        api_key = os.getenv('STIMA_API_KEY')
        
        # 檢查 API 金鑰是否有效（非空且不是預設值）
        if api_key and api_key != 'your_stima_api_key_here':
            try:
                # 初始化 OpenAI 客戶端，指向 Stima API endpoint
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.stima.tech/v1"  # Stima API 的基礎 URL
                )
                self.is_connected = True  # 標記為已成功連接
                
                # ========== 動態獲取模型列表 ==========
                try:
                    # 嘗試從 Stima API 動態獲取可用模型
                    stima_models = self._fetch_stima_models()
                    
                    if stima_models:  # 如果成功獲取到模型列表
                        # 為每個模型建立 ModelConfig 物件
                        for model_id in stima_models:
                            models[model_id] = ModelConfig(
                                name=model_id,
                                provider='stima',
                                available=True,
                                # 將模型 ID 轉換為友善的顯示名稱
                                # 例如: 'gpt-4o-mini' -> 'GPT 4o Mini'
                                display_name=model_id.upper().replace('-', ' ').title()
                            )
                    else:
                        raise Exception("No models fetched")
                        
                except:
                    # ========== 使用預設模型列表（備用方案）==========
                    # 如果無法從 API 獲取，使用硬編碼的預設列表
                    default_stima_models = [
                        ('gpt-4o', 'GPT-4o'),                    # OpenAI 最新模型
                        ('gpt-4o-mini', 'GPT-4o Mini'),          # 輕量版 GPT-4o
                        ('gpt-4-turbo', 'GPT-4 Turbo'),          # GPT-4 Turbo
                        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),      # GPT-3.5
                        ('claude-3-5-sonnet', 'Claude 3.5 Sonnet'),  # Anthropic 最新模型
                        ('claude-3-opus', 'Claude 3 Opus'),          # Claude 3 高階版
                        ('claude-3-sonnet', 'Claude 3 Sonnet'),      # Claude 3 中階版
                        ('claude-3-haiku', 'Claude 3 Haiku'),        # Claude 3 輕量版
                        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),        # Google Gemini Pro
                        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),    # Google Gemini Flash
                        ('llama-3.1-70b', 'Llama 3.1 70B'),          # Meta Llama 大模型
                        ('llama-3.1-8b', 'Llama 3.1 8B'),            # Meta Llama 小模型
                        ('mixtral-8x7b', 'Mixtral 8x7B'),            # Mistral 混合專家模型
                        ('deepseek-chat', 'DeepSeek Chat'),          # DeepSeek 對話模型
                    ]
                    
                    # 將預設模型加入到 models 字典
                    for model_id, display_name in default_stima_models:
                        models[model_id] = ModelConfig(
                            name=model_id,
                            provider='stima',
                            available=True,
                            display_name=display_name
                        )
                        
            except Exception as e:
                # 初始化失敗的錯誤處理
                print(f"Failed to initialize Stima client: {e}")
                self.is_connected = False  # 標記為未連接
        
        return models
    
    def _fetch_stima_models(self) -> List[str]:
        """
        從 Stima API 動態獲取可用模型列表
        
        Returns:
            List[str]: 可用模型 ID 的列表，如果失敗則返回空列表
        """
        try:
            # 獲取 API 金鑰
            api_key = os.getenv('STIMA_API_KEY')
            if not api_key:
                return []
            
            # 設定 HTTP 請求標頭，包含認證資訊
            headers = {
                'Authorization': f"Bearer {api_key}"
            }
            
            # 發送 GET 請求到 Stima API 的 models endpoint
            response = requests.get(
                "https://api.stima.tech/v1/models",
                headers=headers,
                timeout=5  # 5 秒超時限制
            )
            
            # 檢查回應狀態
            if response.status_code == 200:
                data = response.json()
                # 從回應中提取模型 ID
                # API 回應格式: {"data": [{"id": "model-name", ...}, ...]}
                models = [model['id'] for model in data.get('data', [])]
                return models if models else []
                
        except Exception as e:
            print(f"Failed to fetch models: {e}")
            
        return []
    
    def is_api_connected(self) -> bool:
        """
        檢查 API 是否已成功連接
        
        Returns:
            bool: True 表示已連接，False 表示未連接
        """
        return self.is_connected and self.client is not None
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        獲取所有可用的模型列表（供 UI 顯示使用）
        
        Returns:
            List[Dict[str, str]]: 模型資訊列表，每個元素包含 key 和 display_name
        """
        return [
            {
                'key': key,                           # 模型的內部 key
                'display_name': config.display_name   # 顯示給使用者的名稱
            }
            for key, config in self.models.items() 
            if config.available  # 只返回可用的模型
        ]
    
    def generate_plot(self, model_key: str, prompt: str) -> str:
        """
        使用指定模型生成故事情節
        
        Args:
            model_key (str): 模型的 key（如 'gpt-4o'）
            prompt (str): 生成情節的提示詞
            
        Returns:
            str: 生成的情節文字，或錯誤訊息
        """
        # 檢查 API 連接狀態
        if not self.is_api_connected():
            return "Stima API not configured. Please check your API key."
        
        # 檢查模型是否存在
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        # 獲取模型配置
        config = self.models[model_key]
        
        try:
            # 調用 OpenAI API 生成情節
            response = self.client.chat.completions.create(
                model=config.name,  # 使用實際的模型名稱
                messages=[
                    {
                        "role": "system", 
                        "content": "您是一位富有創意的故事作家。請用繁體中文創作出獨特且引人入勝的故事情節。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=3000,     # 限制輸出長度（約 150-200 字）
                temperature=0.8     # 創造性程度（0.8 表示較高創造性）
            )
            
            # 返回生成的內容
            return response.choices[0].message.content
            
        except Exception as e:
            # 錯誤處理：返回錯誤訊息
            return f"Error with {config.display_name}: {str(e)}"
    
    def generate_story(self, model_key: str, plot: str, style: str = "narrative") -> str:
        """
        根據情節生成完整故事
        
        Args:
            model_key (str): 模型的 key
            plot (str): 故事情節
            style (str): 故事風格（預設為 narrative）
            
        Returns:
            str: 生成的完整故事，或錯誤訊息
        """
        # 檢查 API 連接狀態
        if not self.is_api_connected():
            return "Stima API not configured. Please check your API key."
        
        # 檢查模型是否存在
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        config = self.models[model_key]
        
        # 構建故事生成的提示詞
        prompt = f"""根據以下情節：{plot}
        
        請以 {style} 風格撰寫一篇完整的短篇故事。
        內容需引人入勝，字數約每個情節 3000 至 8000 字。
        包含生動的場景描寫、角色發展及令人滿意的結局。
        請使用繁體中文書寫。
        """
        
        try:
            # 調用 OpenAI API 生成故事
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {
                        "role": "system", 
                        "content": f"您是一位技藝精湛的 {style} 風格故事創作者。請用繁體中文創作引人入勝、令人沉浸其中的故事。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=50000,    # 較長的輸出限制
                temperature=0.7     # 適中的創造性（平衡創意和連貫性）
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def cluster_plots_with_ai(self, plots: List[Dict[str, 
