import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    name: str
    provider: str
    available: bool
    display_name: str
    
class LLMManager:
    def __init__(self):
        self.client = None
        self.models = self._initialize_models()
        self.is_connected = False  # 添加連接狀態標記
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """初始化 Stima API 和模型列表"""
        models = {}
        
        # Stima API 設定
        api_key = os.getenv('STIMA_API_KEY')
        if api_key and api_key != 'your_stima_api_key_here':  # 檢查是否為真實的 API key
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.stima.tech/v1"
                )
                self.is_connected = True  # 標記為已連接
                
                # 嘗試從 API 獲取模型列表
                try:
                    stima_models = self._fetch_stima_models()
                    if stima_models:  # 如果成功獲取模型列表
                        for model_id in stima_models:
                            models[model_id] = ModelConfig(
                                name=model_id,
                                provider='stima',
                                available=True,
                                display_name=model_id.upper().replace('-', ' ').title()
                            )
                    else:
                        raise Exception("No models fetched")
                except:
                    # 如果無法獲取，使用預設列表
                    default_stima_models = [
                        ('gpt-4o', 'GPT-4o'),
                        ('gpt-4o-mini', 'GPT-4o Mini'),
                        ('gpt-4-turbo', 'GPT-4 Turbo'),
                        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
                        ('claude-3-5-sonnet', 'Claude 3.5 Sonnet'),
                        ('claude-3-opus', 'Claude 3 Opus'),
                        ('claude-3-sonnet', 'Claude 3 Sonnet'),
                        ('claude-3-haiku', 'Claude 3 Haiku'),
                        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
                        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
                        ('llama-3.1-70b', 'Llama 3.1 70B'),
                        ('llama-3.1-8b', 'Llama 3.1 8B'),
                        ('mixtral-8x7b', 'Mixtral 8x7B'),
                        ('deepseek-chat', 'DeepSeek Chat'),
                    ]
                    
                    for model_id, display_name in default_stima_models:
                        models[model_id] = ModelConfig(
                            name=model_id,
                            provider='stima',
                            available=True,
                            display_name=display_name
                        )
            except Exception as e:
                print(f"Failed to initialize Stima client: {e}")
                self.is_connected = False
        
        return models
    
    def _fetch_stima_models(self) -> List[str]:
        """從 Stima API 獲取可用模型列表"""
        try:
            api_key = os.getenv('STIMA_API_KEY')
            if not api_key:
                return []
                
            headers = {
                'Authorization': f"Bearer {api_key}"
            }
            response = requests.get(
                "https://api.stima.tech/v1/models",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # 根據 Stima API 的實際返回格式
                models = [model['id'] for model in data.get('data', [])]
                return models if models else []
        except Exception as e:
            print(f"Failed to fetch models: {e}")
        return []
    
    def is_api_connected(self) -> bool:
        """檢查 API 是否已連接"""
        return self.is_connected and self.client is not None
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """獲取所有可用的模型列表"""
        return [
            {
                'key': key,
                'display_name': config.display_name
            }
            for key, config in self.models.items() 
            if config.available
        ]
    
    def generate_plot(self, model_key: str, prompt: str) -> str:
        """使用指定模型生成故事情節"""
        if not self.is_api_connected():
            return "Stima API not configured. Please check your API key."
        
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        config = self.models[model_key]
        
        try:
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": "You are a creative story writer. Create unique and engaging story plots in Traditional Chinese."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def generate_story(self, model_key: str, plot: str, style: str = "narrative") -> str:
        """根據情節生成完整故事"""
        if not self.is_api_connected():
            return "Stima API not configured. Please check your API key."
            
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        config = self.models[model_key]
        
        prompt = f"""Based on this plot: {plot}
        
        Write a complete short story in {style} style.
        Make it engaging and approximately 500-800 words.
        Include vivid descriptions, character development, and a satisfying conclusion.
        Write in Traditional Chinese.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": f"You are a skilled {style} story writer. Create immersive and captivating stories in Traditional Chinese."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def cluster_plots_with_ai(self, plots: List[Dict[str, str]]) -> List[Dict]:
        """使用 AI 模型將相似的情節分群"""
        if not self.is_api_connected():
            return self._simple_clustering(plots)
        
        # 選擇一個便宜的模型來做分類
        clustering_model = None
        preferred_models = ['gpt-3.5-turbo', 'gpt-4o-mini', 'claude-3-haiku', 'gemini-1.5-flash']
        
        for model in preferred_models:
            if model in self.models:
                clustering_model = model
                break
        
        if not clustering_model and self.models:
            clustering_model = list(self.models.keys())[0]
        
        if not clustering_model:
            return self._simple_clustering(plots)
        
        # 準備情節列表
        plot_text = "\n".join([f"{i+1}. {p['plot']}" for i, p in enumerate(plots)])
        
        prompt = f"""
        Analyze these story plots and group similar ones by theme, genre, or narrative elements.
        Return ONLY valid JSON format.
        
        Plots:
        {plot_text}
        
        Required JSON format:
        {{
            "groups": [
                {{
                    "theme": "Brief theme description in English",
                    "plot_indices": [1, 3, 5],
                    "common_elements": "What these plots share"
                }}
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=clustering_model,
                messages=[
                    {"role": "system", "content": "You are a literary analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            import json
            result_text = response.choices[0].message.content
            # 清理可能的 markdown 標記
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
                
            result = json.loads(result_text.strip())
            return result['groups']
            
        except Exception as e:
            print(f"AI clustering failed: {e}")
            return self._simple_clustering(plots)
    
    def _simple_clustering(self, plots: List[Dict[str, str]]) -> List[Dict]:
        """簡單的備用分群方法"""
        # 如果 AI 分群失敗，返回所有情節作為一個群組
        return [{
            "theme": "All generated plots",
            "plot_indices": list(range(1, len(plots) + 1)),
            "common_elements": "Various creative story ideas"
        }]
