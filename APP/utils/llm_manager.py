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
        self.clients = {}
        self.models = self._initialize_models()
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """檢查哪些模型可用"""
        models = {}
        
        # YourAPI 設定
        if os.getenv('YOURAPI_KEY'):
            self.clients['yourapi'] = OpenAI(
                api_key=os.getenv('YOURAPI_KEY'),
                base_url="https://api.yourapi.cn/v1"
            )
            
            # YourAPI 支援的模型列表（根據 pricing 頁面）
            yourapi_models = [
                ('gpt-4o', 'GPT-4o'),
                ('gpt-4o-mini', 'GPT-4o Mini'),
                ('gpt-4-turbo', 'GPT-4 Turbo'),
                ('gpt-4', 'GPT-4'),
                ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
                ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet'),
                ('claude-3-opus-20240229', 'Claude 3 Opus'),
                ('claude-3-sonnet-20240229', 'Claude 3 Sonnet'),
                ('claude-3-haiku-20240307', 'Claude 3 Haiku'),
                ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
                ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
                ('deepseek-chat', 'DeepSeek Chat'),
                ('deepseek-coder', 'DeepSeek Coder'),
                ('llama-3.1-405b-instruct', 'Llama 3.1 405B'),
                ('llama-3.1-70b-instruct', 'Llama 3.1 70B'),
                ('llama-3.1-8b-instruct', 'Llama 3.1 8B'),
            ]
            
            for model_id, display_name in yourapi_models:
                models[f'yourapi_{model_id}'] = ModelConfig(
                    name=model_id,
                    provider='yourapi',
                    available=True,
                    display_name=f"[YourAPI] {display_name}"
                )
        
        # Stima API 設定
        if os.getenv('STIMA_API_KEY'):
            self.clients['stima'] = OpenAI(
                api_key=os.getenv('STIMA_API_KEY'),
                base_url="https://api.stima.tech/v1"
            )
            
            # 嘗試從 API 獲取模型列表
            try:
                stima_models = self._fetch_stima_models()
                for model_id in stima_models:
                    models[f'stima_{model_id}'] = ModelConfig(
                        name=model_id,
                        provider='stima',
                        available=True,
                        display_name=f"[Stima] {model_id}"
                    )
            except:
                # 如果無法獲取，使用預設列表
                default_stima_models = [
                    'gpt-4o',
                    'gpt-4o-mini',
                    'gpt-3.5-turbo',
                    'claude-3-5-sonnet',
                    'gemini-1.5-pro',
                    'llama-3.1-70b',
                ]
                for model_id in default_stima_models:
                    models[f'stima_{model_id}'] = ModelConfig(
                        name=model_id,
                        provider='stima',
                        available=True,
                        display_name=f"[Stima] {model_id}"
                    )
        
        return models
    
    def _fetch_stima_models(self) -> List[str]:
        """從 Stima API 獲取可用模型列表"""
        try:
            headers = {
                'Authorization': f"Bearer {os.getenv('STIMA_API_KEY')}"
            }
            response = requests.get(
                "https://api.stima.tech/models",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # 假設返回格式是 {"models": [{"id": "model-name", ...}]}
                return [model['id'] for model in data.get('data', [])]
        except:
            pass
        return []
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """獲取所有可用的模型列表，返回包含 key 和顯示名稱的字典"""
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
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        config = self.models[model_key]
        provider = config.provider
        
        if provider not in self.clients:
            return f"Provider {provider} not configured"
        
        try:
            client = self.clients[provider]
            response = client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": "You are a creative story writer. Create unique and engaging story plots."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def generate_story(self, model_key: str, plot: str, style: str = "narrative") -> str:
        """根據情節生成完整故事"""
        if model_key not in self.models:
            return f"Model {model_key} not available"
        
        config = self.models[model_key]
        provider = config.provider
        
        if provider not in self.clients:
            return f"Provider {provider} not configured"
        
        prompt = f"""Based on this plot: {plot}
        
        Write a complete short story in {style} style.
        Make it engaging and approximately 500 words.
        Include vivid descriptions, character development, and a satisfying conclusion.
        """
        
        try:
            client = self.clients[provider]
            response = client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": f"You are a skilled {style} story writer. Create immersive and captivating stories."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def cluster_plots_with_ai(self, plots: List[Dict[str, str]]) -> List[Dict]:
        """使用 AI 模型將相似的情節分群"""
        # 選擇一個可用的模型來做分類（優先使用便宜的）
        preferred_models = [
            'yourapi_gpt-3.5-turbo',
            'stima_gpt-3.5-turbo',
            'yourapi_deepseek-chat',
            'yourapi_gpt-4o-mini',
        ]
        
        clustering_model = None
        for model in preferred_models:
            if model in self.models:
                clustering_model = model
                break
        
        if not clustering_model:
            # 如果沒有偏好的模型，使用第一個可用的
            if self.models:
                clustering_model = list(self.models.keys())[0]
            else:
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
                    "theme": "Brief theme description",
                    "plot_indices": [1, 3, 5],
                    "common_elements": "What these plots share"
                }}
            ]
        }}
        """
        
        try:
            config = self.models[clustering_model]
            client = self.clients[config.provider]
            
            response = client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": "You are a literary analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
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
