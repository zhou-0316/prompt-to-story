import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    name: str
    provider: str
    available: bool
    
class LLMManager:
    def __init__(self):
        self.models = self._initialize_models()
        
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """檢查哪些模型可用"""
        models = {}
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            models['gpt-3.5-turbo'] = ModelConfig('GPT-3.5', 'openai', True)
            models['gpt-4'] = ModelConfig('GPT-4', 'openai', True)
        
        # Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            models['claude-3-haiku'] = ModelConfig('Claude 3 Haiku', 'anthropic', True)
        
        # Google
        if os.getenv('GOOGLE_API_KEY'):
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            models['gemini-pro'] = ModelConfig('Gemini Pro', 'google', True)
            
        return models
    
    def get_available_models(self) -> List[str]:
        """獲取所有可用的模型列表"""
        return [name for name, config in self.models.items() if config.available]
    
    def generate_plot(self, model_name: str, prompt: str) -> str:
        """使用指定模型生成故事情節"""
        if model_name not in self.models:
            return f"Model {model_name} not available"
        
        config = self.models[model_name]
        
        try:
            if config.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a creative story writer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200
                )
                return response.choices[0].message.content
                
            elif config.provider == 'anthropic':
                message = self.anthropic_client.messages.create(
                    model=model_name,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
                
            elif config.provider == 'google':
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
                
        except Exception as e:
            return f"Error with {model_name}: {str(e)}"
    
    def generate_story(self, model_name: str, plot: str, style: str = "narrative") -> str:
        """根據情節生成完整故事"""
        prompt = f"""Based on this plot: {plot}
        
        Write a complete short story in {style} style.
        Make it engaging and about 500 words.
        """
        
        # 使用相同的生成邏輯，但 max_tokens 更大
        if model_name not in self.models:
            return f"Model {model_name} not available"
        
        config = self.models[model_name]
        
        try:
            if config.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a creative story writer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000
                )
                return response.choices[0].message.content
                
            # ... 其他模型的實現類似
            
        except Exception as e:
            return f"Error: {str(e)}"
