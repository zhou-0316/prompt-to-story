# 01

我來為這個程式碼添加詳細的中文註解：

```python
import streamlit as st
from datetime import datetime
import random
from utils.llm_manager import LLMManager
from utils.story_processor import StoryProcessor

# ========== 初始化設定 ==========
# 設定 Streamlit 頁面配置
st.set_page_config(
    page_title="PlotWeaver",  # 瀏覽器標籤標題
    layout="wide",            # 使用寬版面配置
    page_icon="🎭"           # 頁面圖標
)

# 初始化 session state（保存應用程式狀態）
if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()        # LLM 管理器實例
    st.session_state.processor = StoryProcessor()      # 故事處理器實例
    st.session_state.generated_plots = []              # 儲存生成的情節
    st.session_state.selected_plots = []               # 儲存選中的情節
    st.session_state.clustered_plots = []              # 儲存分群後的情節

# 主標題和描述
st.title("🎭 PlotWeaver")
st.markdown("Generate creative stories using multiple AI models from YourAPI and Stima")

# ========== 側邊欄配置 ==========
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 獲取可用的模型列表
    available_models = st.session_state.llm_manager.get_available_models()
    
    # 檢查是否有可用模型
    if not available_models:
        # 沒有可用模型時顯示錯誤和設定指引
        st.error("❌ No models available")
        st.info("""
        Please add your Stima API key in Secrets:
        
        1. Click 'Manage app' (bottom right)
        2. Go to Settings → Secrets
        3. Add: STIMA_API_KEY = "your_key"
        
        Get your API key from:
        https://stima.tech
        """)
    else:
        # 有可用模型時顯示成功訊息
        st.success(f"✅ {len(available_models)} models available")
        
        # 展開式選單顯示所有可用模型
        with st.expander("📋 Available Models"):
            for model in available_models:
                st.write(f"• {model['display_name']}")
    
    st.divider()
    
    # ========== API 連接狀態檢查 ==========
    st.subheader("📊 API Status")
    try:
        # 檢查 LLM 管理器是否有 client 屬性且不為空
        if hasattr(st.session_state.llm_manager, 'client') and st.session_state.llm_manager.client:
            st.success("✅ Stima API Connected")
        else:
            st.error("❌ Stima API Not Connected")
            st.info("Please check your API key")
    except:
        # 錯誤處理：根據是否有可用模型判斷連接狀態
        if available_models:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Connected")

# ========== 主要內容區：三個標籤頁 ==========
tab1, tab2, tab3 = st.tabs(["📝 Generate Plots", "✅ Select Plots", "📖 Generate Story"])

# ========== Tab 1: 生成情節 ==========
with tab1:
    st.header("Step 1: Generate Story Plots")
    
    # 建立兩欄佈局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 基本故事主題輸入框
        base_prompt = st.text_area(
            "Enter your story theme or idea:",
            "A mysterious adventure in a futuristic city where AI and humans coexist",  # 預設值
            height=100
        )
        
        # 模型選擇區域
        if available_models:
            # 創建顯示名稱到實際 key 的對應字典
            model_options = {model['display_name']: model['key'] 
                           for model in available_models}
            
            # 多選框：選擇要使用的模型
            selected_display_names = st.multiselect(
                "Select models for plot generation (max 5):",
                list(model_options.keys()),
                default=list(model_options.keys())[:min(3, len(model_options))]  # 預設選前3個
            )
            
            # 將顯示名稱轉換回實際的模型 keys
            selected_models = [model_options[name] for name in selected_display_names]
            
            # 建立兩個按鈕欄
            col_a, col_b = st.columns(2)
            with col_a:
                # 隨機選擇模型按鈕
                if st.button("🎲 Random Selection"):
                    num_models = min(5, len(available_models))
                    random_models = random.sample(list(model_options.keys()), 
                                                random.randint(2, num_models))
                    st.rerun()  # 重新執行應用程式以更新介面
            
            with col_b:
                # 設定每個模型生成的情節數量
                num_variations = st.number_input("Plots per model:", 
                                               min_value=1, max_value=3, value=2)
    
    with col2:
        # 顯示使用提示
        st.info("""
        **💡 Tips:**
        - YourAPI supports GPT, Claude, Gemini, Llama models
        - Stima provides various open-source models
        - Mix different models for creative diversity
        """)
    
    # ========== 生成情節按鈕和處理邏輯 ==========
    if st.button("🚀 Generate Plots", type="primary", disabled=not available_models):
        with st.spinner("Generating plots from multiple models..."):
            plots = []  # 儲存所有生成的情節
            progress_bar = st.progress(0)  # 進度條
            total_tasks = len(selected_models) * num_variations  # 總任務數
            current_task = 0
            
            # 遍歷每個選定的模型
            for model_key in selected_models:
                # 獲取模型顯示名稱
                model_name = next(m['display_name'] for m in available_models 
                                if m['key'] == model_key)
                
                # 為每個模型生成指定數量的變化版本
                for i in range(num_variations):
                    current_task += 1
                    progress_bar.progress(current_task / total_tasks)  # 更新進度條
                    
                    # 構建情節生成提示詞
                    plot_prompt = f"""Create a unique story plot based on: {base_prompt}
                    
                    Variation {i+1}: Focus on a different aspect or perspective.
                    Be creative and original. About 50-100 words."""
                    
                    # 調用 LLM 生成情節
                    plot_text = st.session_state.llm_manager.generate_plot(
                        model_key, plot_prompt
                    )
                    
                    # 儲存生成的情節
                    plots.append({
                        'model': model_name,
                        'plot': plot_text,
                        'id': f"{model_key}_{i}"  # 唯一識別碼
                    })
            
            progress_bar.empty()  # 清除進度條
            st.session_state.generated_plots = plots  # 保存到 session state
            
            # ========== 使用 AI 自動分群情節 ==========
            if len(plots) > 0:
                with st.spinner("Analyzing and clustering plots..."):
                    # 調用 AI 分群功能
                    st.session_state.clustered_plots = st.session_state.llm_manager.cluster_plots_with_ai(plots)
                st.success(f"✅ Generated {len(plots)} plots and organized them into {len(st.session_state.clustered_plots)} groups")
    
    # ========== 顯示生成的情節 ==========
    if st.session_state.generated_plots:
        st.divider()
        st.subheader("📚 Generated Plots")
        
        # 使用展開器顯示每個情節
        for i, plot in enumerate(st.session_state.generated_plots):
            with st.expander(f"Plot {i+1} - {plot['model']}", expanded=(i==0)):  # 第一個預設展開
                st.write(plot['plot'])
                st.caption(f"Model: {plot['model']} | ID: {plot['id']}")

# ========== Tab 2: 選擇情節 ==========
with tab2:
    st.header("Step 2: Select Plot Groups")
    
    if st.session_state.clustered_plots:
        st.info(f"Found {len(st.session_state.clustered_plots)} plot groups. Select the plots you want to use for story generation.")
        
        # 清除選擇按鈕
        if st.button("🔄 Clear Selection"):
            st.session_state.selected_plots = []
            st.rerun()
        
        # 遍歷每個情節群組
        for group_idx, group in enumerate(st.session_state.clustered_plots):
            with st.expander(f"**Group {group_idx+1}: {group['theme']}**", expanded=True):
                # 顯示群組共同元素（如果有）
                if 'common_elements' in group:
                    st.caption(f"Common elements: {group['common_elements']}")
                
                st.write("**Plots in this group:**")
                
                # 顯示該群組中的所有情節
                for idx in group['plot_indices']:
                    if idx <= len(st.session_state.generated_plots):
                        plot = st.session_state.generated_plots[idx-1]
                        
                        # 建立選擇框和內容欄
                        col1, col2 = st.columns([1, 10])
                        with col1:
                            # 勾選框用於選擇情節
                            is_selected = st.checkbox("", key=f"plot_select_{idx}",
                                                    value=(plot in st.session_state.selected_plots))
                        with col2:
                            st.write(f"**{plot['model']}**")
                            st.write(plot['plot'])
                        
                        # 更新選中的情節列表
                        if is_selected and plot not in st.session_state.selected_plots:
                            st.session_state.selected_plots.append(plot)
                        elif not is_selected and plot in st.session_state.selected_plots:
                            st.session_state.selected_plots.remove(plot)
                
                st.divider()
        
        # 顯示已選擇的情節數量
        if st.session_state.selected_plots:
            st.success(f"✅ Selected {len(st.session_state.selected_plots)} plots")
    else:
        st.info("📝 Please generate plots first in Tab 1")

# ========== Tab 3: 生成完整故事 ==========
with tab3:
    st.header("Step 3: Generate Complete Story")
    
    if st.session_state.selected_plots:
        st.subheader("📋 Selected Plots")
        
        # 顯示已選擇的情節（可展開）
        with st.expander("View selected plots", expanded=False):
            for idx, plot in enumerate(st.session_state.selected_plots):
                st.write(f"{idx+1}. **{plot['model']}**: {plot['plot']}")
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 選擇用於生成故事的模型
            if available_models:
                # 創建模型選項字典
                story_model_options = {model['display_name']: model['key'] 
                                     for model in available_models}
                
                # 多選框：選擇生成故事的模型（最多3個）
                selected_story_displays = st.multiselect(
                    "Select models for story generation (max 3):",
                    list(story_model_options.keys()),
                    default=list(story_model_options.keys())[:min(2, len(story_model_options))],
                    max_selections=3
                )
                
                # 轉換為實際的模型 keys
                story_models = [story_model_options[name] for name in selected_story_displays]
            
            # 故事風格選擇
            story_style = st.selectbox(
                "Story style:",
                ["Narrative", "Mystery", "Sci-Fi", "Fantasy", "Romance", 
                 "Thriller", "Comedy", "Drama", "Horror", "Adventure"]
            )
            
            # 故事長度選擇
            story_length = st.select_slider(
                "Story length:",
                options=["Short (500 words)", "Medium (1000 words)", "Long (1500 words)"],
                value="Medium (1000 words)"
            )
        
        with col2:
            # 顯示生成提示
            st.info("""
            **📖 Story Generation:**
            - Multiple models create different versions
            - Each brings unique perspective
            - Export as Markdown files
            """)
        
        # ========== 生成故事按鈕和處理邏輯 ==========
        if st.button("✨ Generate Stories", type="primary"):
            with st.spinner("Creating your stories..."):
                # 合併所有選定的情節
                combined_plots = "\n".join([f"- {p['plot']}" for p in st.session_state.selected_plots])
                
                stories = []  # 儲存生成的故事
                progress = st.progress(0)  # 進度條
                
                # 使用每個選定的模型生成故事
                for idx, model_key in enumerate(story_models):
                    progress.progress((idx + 1) / len(story_models))
                    
                    # 獲取模型名稱
                    model_name = next(m['display_name'] for m in available_models 
                                     if m['key'] == model_key)
                    
                    st.info(f"Generating story with {model_name}...")
                    
                    # 調用 LLM 生成故事
                    story = st.session_state.llm_manager.generate_story(
                        model_key, combined_plots, story_style.lower()
                    )
                    
                    # 儲存故事和相關元數據
                    stories.append({
                        'model': model_name,
                        'story': story,
                        'metadata': {
                            'title': f"{story_style} Story",
                            'model': model_name,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'style': story_style,
                            'based_on_plots': len(st.session_state.selected_plots)
                        }
                    })
                
                progress.empty()  # 清除進度條
                st.success("✅ Stories generated successfully!")
                
                # ========== 顯示生成的故事 ==========
                for story_data in stories:
                    st.divider()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # 故事標題
                        st.subheader(f"📖 {story_data['metadata']['title']} by {story_data['model']}")
                    
                    with col2:
                        # 準備 Markdown 格式的內容供下載
                        markdown_content = f"""# {story_data['metadata']['title']}

**Generated by:** {story_data['metadata']['model']}  
**Date:** {story_data['metadata']['date']}  
**Style:** {story_data['metadata']['style']}  
**Based on:** {story_data['metadata']['based_on_plots']} selected plots  

---

{story_data['story']}

---

*This story was generated using AI through Story Generator Hub.*  
*Powered by YourAPI & Stima API*
"""
                        
                        # 下載按鈕
                        st.download_button(
                            label=f"📥 Download",
                            data=markdown_content,
                            file_name=f"story_{story_data['metadata']['style'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            key=f"download_{story_data['model']}_{idx}"
                        )
                    
                    # 顯示故事內容
                    with st.container():
                        st.markdown(story_data['story'])
                    
    else:
        # 沒有選擇情節時的提示
        st.info("✋ Please select plots in Tab 2 first")
        
        # 提供快速開始選項
        if st.session_state.generated_plots:
            if st.button("🚀 Quick Start - Select All Plots"):
                # 選擇所有已生成的情節
                st.session_state.selected_plots = st.session_state.generated_plots.copy()
                st.rerun()
```

這個程式碼是一個完整的故事生成應用程式，主要功能包括：

1. **初始化階段**：設定頁面配置和初始化必要的元件
2. **側邊欄**：顯示配置資訊、可用模型和 API 連接狀態
3. **Tab 1**：使用多個 AI 模型生成故事情節，並自動分群
4. **Tab 2**：從分群後的情節中選擇要使用的內容
5. **Tab 3**：基於選定的情節，使用不同模型生成完整故事，並提供下載功能

# 02

我來為這個 `LLMManager` 類別添加詳細的中文註解：

```python
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
        self.client = None                              # OpenAI 客戶端實例
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
                                # 例如: 'gpt-4o-mini' -> 'GPT 4O Mini'
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
                        "content": "You are a creative story writer. Create unique and engaging story plots in Traditional Chinese."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=300,     # 限制輸出長度（約 150-200 字）
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
        prompt = f"""Based on this plot: {plot}
        
        Write a complete short story in {style} style.
        Make it engaging and approximately 500-800 words.
        Include vivid descriptions, character development, and a satisfying conclusion.
        Write in Traditional Chinese.
        """
        
        try:
            # 調用 OpenAI API 生成故事
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a skilled {style} story writer. Create immersive and captivating stories in Traditional Chinese."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,    # 較長的輸出限制（約 1000-1500 字）
                temperature=0.7     # 適中的創造性（平衡創意和連貫性）
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with {config.display_name}: {str(e)}"
    
    def cluster_plots_with_ai(self, plots: List[Dict[str, str]]) -> List[Dict]:
        """
        使用 AI 模型將相似的情節自動分群
        
        Args:
            plots (List[Dict[str, str]]): 情節列表，每個包含 'plot' 和 'model' 鍵
            
        Returns:
            List[Dict]: 分群結果，每個群組包含主題、情節索引和共同元素
        """
        # 檢查 API 連接
        if not self.is_api_connected():
            return self._simple_clustering(plots)  # 使用備用方案
        
        # ========== 選擇適合的模型進行分類 ==========
        clustering_model = None
        # 優先使用較便宜、速度快的模型
        preferred_models = [
            'gpt-3.5-turbo',     # 最便宜且快速
            'gpt-4o-mini',       # 輕量版 GPT-4
            'claude-3-haiku',    # Claude 輕量版
            'gemini-1.5-flash'   # Gemini 快速版
        ]
        
        # 尋找第一個可用的偏好模型
        for model in preferred_models:
            if model in self.models:
                clustering_model = model
                break
        
        # 如果沒有偏好模型，使用任何可用的模型
        if not clustering_model and self.models:
            clustering_model = list(self.models.keys())[0]
        
        # 如果沒有任何模型可用，使用備用方案
        if not clustering_model:
            return self._simple_clustering(plots)
        
        # ========== 準備分群提示詞 ==========
        # 將所有情節格式化為編號列表
        plot_text = "\n".join([f"{i+1}. {p['plot']}" for i, p in enumerate(plots)])
        
        # 構建要求 AI 分群的提示詞
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
            # 調用 AI 進行分群分析
            response = self.client.chat.completions.create(
                model=clustering_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a literary analyst. Return only valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,     # 足夠返回分群結果
                temperature=0.3     # 低溫度以獲得更一致的輸出
            )
            
            # ========== 解析 JSON 回應 ==========
            import json
            result_text = response.choices[0].message.content
            
            # 清理可能的 markdown 標記（有些模型會加上 ```json``` 包裝）
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            # 解析 JSON 並返回群組列表
            result = json.loads(result_text.strip())
            return result['groups']
            
        except Exception as e:
            # 如果 AI 分群失敗，使用備用方案
            print(f"AI clustering failed: {e}")
            return self._simple_clustering(plots)
    
    def _simple_clustering(self, plots: List[Dict[str, str]]) -> List[Dict]:
        """
        簡單的備用分群方法
        當 AI 分群失敗時使用，將所有情節放在同一個群組
        
        Args:
            plots (List[Dict[str, str]]): 情節列表
            
        Returns:
            List[Dict]: 包含單一群組的列表
        """
        return [{
            "theme": "All generated plots",                           # 群組主題
            "plot_indices": list(range(1, len(plots) + 1)),          # 包含所有情節索引
            "common_elements": "Various creative story ideas"         # 共同元素描述
        }]
```

這個 `LLMManager` 類別的主要功能包括：

1. **模型管理**：動態載入和管理多個 AI 模型
2. **API 連接**：處理 Stima API 的連接和認證
3. **情節生成**：使用不同模型生成故事情節
4. **故事生成**：基於情節生成完整故事
5. **智能分群**：使用 AI 自動將相似情節分組
6. **錯誤處理**：完善的錯誤處理和備用方案

# 03

您的設定有一些需要調整的地方。讓我分析並提供建議：

## 🔍 問題分析

### 1. **max_tokens=50000 太高了**
大多數模型都有輸出限制：
- GPT-3.5-turbo: 最多 4,096 tokens
- GPT-4/GPT-4o: 最多 4,096 tokens 輸出
- Claude 3 系列: 最多 4,096 tokens 輸出
- Gemini: 最多 8,192 tokens

### 2. **字數要求過高**
- 3000-8000 中文字約需要 4,500-12,000 tokens
- 這超過了大多數模型的單次輸出限制

## ✅ 建議的修改版本

```python
def generate_story(self, model_key: str, plot: str, style: str = "narrative", length: str = "medium") -> str:
    """
    根據情節生成完整故事
    
    Args:
        model_key (str): 模型的 key
        plot (str): 故事情節
        style (str): 故事風格（預設為 narrative）
        length (str): 故事長度 ("short", "medium", "long")
        
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
    
    # 根據長度設定字數和 token 限制
    length_settings = {
        "short": {
            "words": "500-800",
            "max_tokens": 1500,
            "description": "簡短精煉"
        },
        "medium": {
            "words": "1000-1500", 
            "max_tokens": 2500,
            "description": "中等長度"
        },
        "long": {
            "words": "1500-2500",
            "max_tokens": 4000,
            "description": "較長篇幅"
        }
    }
    
    setting = length_settings.get(length, length_settings["medium"])
    
    # 風格對應的中文描述
    style_map = {
        "narrative": "敘事",
        "mystery": "懸疑",
        "sci-fi": "科幻",
        "fantasy": "奇幻",
        "romance": "浪漫",
        "thriller": "驚悚",
        "comedy": "喜劇",
        "drama": "戲劇",
        "horror": "恐怖",
        "adventure": "冒險"
    }
    
    chinese_style = style_map.get(style.lower(), style)
    
    # 構建故事生成的提示詞
    prompt = f"""根據以下情節：{plot}
    
    請以{chinese_style}風格撰寫一篇{setting['description']}的短篇故事。
    
    要求：
    1. 字數約 {setting['words']} 字
    2. 包含生動的場景描寫和細膩的心理刻畫
    3. 角色性格鮮明，有適當的發展變化
    4. 情節起承轉合，結構完整
    5. 結局令人滿意，留有回味空間
    
    請使用繁體中文書寫，文筆流暢優美。
    """
    
    try:
        # 調用 OpenAI API 生成故事
        response = self.client.chat.completions.create(
            model=config.name,
            messages=[
                {
                    "role": "system", 
                    "content": f"您是一位專業的{chinese_style}小說作家，擅長用繁體中文創作引人入勝的故事。您的文筆細膩，善於營造氛圍，能夠讓讀者身臨其境。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=setting['max_tokens'],  # 根據長度動態設定
            temperature=0.7,                   # 適中的創造性
            top_p=0.9,                         # 增加多樣性
            frequency_penalty=0.3,              # 減少重複
            presence_penalty=0.3                # 鼓勵新話題
        )
        
        story = response.choices[0].message.content
        
        # 檢查是否因 token 限制而被截斷
        if response.choices[0].finish_reason == "length":
            story += "\n\n[註：由於長度限制，故事可能未完整呈現]"
        
        return story
        
    except Exception as e:
        return f"Error with {config.display_name}: {str(e)}"
```

## 🔧 如果您真的需要長篇故事（3000-8000字）

可以考慮**分段生成**的方式：

```python
def generate_long_story(self, model_key: str, plot: str, style: str = "narrative") -> str:
    """
    生成長篇故事（透過分段生成）
    """
    if not self.is_api_connected():
        return "Stima API not configured. Please check your API key."
    
    if model_key not in self.models:
        return f"Model {model_key} not available"
    
    config = self.models[model_key]
    
    # 將故事分成多個部分生成
    story_parts = []
    
    # 第一部分：開頭（起）
    part1_prompt = f"""根據情節：{plot}
    請撰寫故事的開頭部分（起），約1500-2000字。
    包含：背景介紹、主要角色登場、初始衝突。
    使用{style}風格，繁體中文。"""
    
    # 第二部分：發展（承）
    part2_prompt = f"""延續上文，撰寫故事的發展部分（承），約1500-2000字。
    深化衝突，展開情節，角色關係變化。"""
    
    # 第三部分：高潮（轉）
    part3_prompt = f"""延續上文，撰寫故事的高潮部分（轉），約1500-2000字。
    衝突達到頂點，關鍵轉折出現。"""
    
    # 第四部分：結局（合）
    part4_prompt = f"""延續上文，撰寫故事的結局部分（合），約1500-2000字。
    解決衝突，收束情節，留下餘韻。"""
    
    prompts = [part1_prompt, part2_prompt, part3_prompt, part4_prompt]
    
    try:
        for i, prompt in enumerate(prompts):
            # 為後續部分提供前文摘要
            if i > 0:
                previous_summary = f"前文摘要：{story_parts[-1][:200]}..."
                prompt = f"{previous_summary}\n\n{prompt}"
            
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {"role": "system", "content": f"您是{style}故事作家"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            story_parts.append(response.choices[0].message.content)
        
        # 合併所有部分
        full_story = "\n\n".join(story_parts)
        return full_story
        
    except Exception as e:
        return f"Error: {str(e)}"
```

## 📝 主程式調整建議

在 `app.py` 中，您也需要相應調整：

```python
# Tab 3 中的故事長度選擇
story_length = st.select_slider(
    "Story length:",
    options=["Short (500-800字)", "Medium (1000-1500字)", "Long (1500-2500字)"],
    value="Medium (1000-1500字)"
)

# 提取長度類型
length_type = "short" if "Short" in story_length else "long" if "Long" in story_length else "medium"

# 生成故事時傳入長度參數
story = st.session_state.llm_manager.generate_story(
    model_key, combined_plots, story_style.lower(), length_type
)
```

這樣的設定會更實際且不會超過 API 限制！


# 04

當然可以！這是個很好的想法，讓使用者可以根據需求選擇不同的生成方式。我來幫您整合兩種方法：

## 📝 更新的 `llm_manager.py`

```python
def generate_story(self, model_key: str, plot: str, style: str = "narrative", length: str = "medium") -> str:
    """
    根據情節生成完整故事（標準版本）
    
    Args:
        model_key (str): 模型的 key
        plot (str): 故事情節
        style (str): 故事風格（預設為 narrative）
        length (str): 故事長度 ("short", "medium", "long")
        
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
    
    # 根據長度設定字數和 token 限制
    length_settings = {
        "short": {
            "words": "500-800",
            "max_tokens": 1500,
            "description": "簡短精煉"
        },
        "medium": {
            "words": "1000-1500", 
            "max_tokens": 2500,
            "description": "中等長度"
        },
        "long": {
            "words": "1500-2500",
            "max_tokens": 4000,
            "description": "較長篇幅"
        }
    }
    
    setting = length_settings.get(length, length_settings["medium"])
    
    # 風格對應的中文描述
    style_map = {
        "narrative": "敘事",
        "mystery": "懸疑",
        "sci-fi": "科幻",
        "fantasy": "奇幻",
        "romance": "浪漫",
        "thriller": "驚悚",
        "comedy": "喜劇",
        "drama": "戲劇",
        "horror": "恐怖",
        "adventure": "冒險"
    }
    
    chinese_style = style_map.get(style.lower(), style)
    
    # 構建故事生成的提示詞
    prompt = f"""根據以下情節：{plot}
    
    請以{chinese_style}風格撰寫一篇{setting['description']}的短篇故事。
    
    要求：
    1. 字數約 {setting['words']} 字
    2. 包含生動的場景描寫和細膩的心理刻畫
    3. 角色性格鮮明，有適當的發展變化
    4. 情節起承轉合，結構完整
    5. 結局令人滿意，留有回味空間
    
    請使用繁體中文書寫，文筆流暢優美。
    """
    
    try:
        # 調用 OpenAI API 生成故事
        response = self.client.chat.completions.create(
            model=config.name,
            messages=[
                {
                    "role": "system", 
                    "content": f"您是一位專業的{chinese_style}小說作家，擅長用繁體中文創作引人入勝的故事。您的文筆細膩，善於營造氛圍，能夠讓讀者身臨其境。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=setting['max_tokens'],  # 根據長度動態設定
            temperature=0.7,                   # 適中的創造性
            top_p=0.9,                         # 增加多樣性
            frequency_penalty=0.3,              # 減少重複
            presence_penalty=0.3                # 鼓勵新話題
        )
        
        story = response.choices[0].message.content
        
        # 檢查是否因 token 限制而被截斷
        if response.choices[0].finish_reason == "length":
            story += "\n\n[註：由於長度限制，故事可能未完整呈現]"
        
        return story
        
    except Exception as e:
        return f"Error with {config.display_name}: {str(e)}"

def generate_long_story(self, model_key: str, plot: str, style: str = "narrative", 
                       progress_callback=None) -> str:
    """
    生成超長篇故事（透過分段生成，3000-8000字）
    
    Args:
        model_key (str): 模型的 key
        plot (str): 故事情節
        style (str): 故事風格
        progress_callback: 進度回調函數（用於更新UI）
        
    Returns:
        str: 生成的長篇故事
    """
    # 檢查 API 連接狀態
    if not self.is_api_connected():
        return "Stima API not configured. Please check your API key."
    
    if model_key not in self.models:
        return f"Model {model_key} not available"
    
    config = self.models[model_key]
    
    # 風格對應的中文描述
    style_map = {
        "narrative": "敘事",
        "mystery": "懸疑",
        "sci-fi": "科幻",
        "fantasy": "奇幻",
        "romance": "浪漫",
        "thriller": "驚悚",
        "comedy": "喜劇",
        "drama": "戲劇",
        "horror": "恐怖",
        "adventure": "冒險"
    }
    
    chinese_style = style_map.get(style.lower(), style)
    
    # 將故事分成四個部分生成
    story_parts = []
    part_names = ["起（開端）", "承（發展）", "轉（高潮）", "合（結局）"]
    
    # 定義每個部分的提示詞
    prompts = [
        # 第一部分：起
        f"""根據情節：{plot}
        
        請撰寫一篇{chinese_style}風格長篇故事的第一部分【起】。
        
        這部分需要包含：
        1. 故事背景的詳細介紹
        2. 主要角色的登場和性格刻畫
        3. 初始情況的建立
        4. 引發故事的事件或衝突
        
        字數要求：1500-2000字
        請使用繁體中文，文筆生動細膩。""",
        
        # 第二部分：承
        f"""請延續前文，撰寫故事的第二部分【承】。
        
        這部分需要包含：
        1. 情節的深入發展
        2. 角色關係的變化
        3. 衝突的逐步升級
        4. 新的挑戰或發現
        
        字數要求：1500-2000字
        保持{chinese_style}風格，繁體中文。""",
        
        # 第三部分：轉
        f"""請延續前文，撰寫故事的第三部分【轉】。
        
        這部分需要包含：
        1. 故事達到高潮
        2. 關鍵的轉折點
        3. 重大真相的揭露
        4. 角色的重要決定
        
        字數要求：1500-2000字
        保持{chinese_style}風格，繁體中文。""",
        
        # 第四部分：合
        f"""請延續前文，撰寫故事的最後部分【合】。
        
        這部分需要包含：
        1. 衝突的解決
        2. 故事線的收束
        3. 角色的成長或改變
        4. 意味深長的結局
        
        字數要求：1500-2000字
        保持{chinese_style}風格，繁體中文。"""
    ]
    
    try:
        context = ""  # 用於保存前文摘要
        
        for i, (prompt, part_name) in enumerate(zip(prompts, part_names)):
            # 更新進度（如果有回調函數）
            if progress_callback:
                progress_callback(f"正在生成：{part_name}", (i + 1) / 4)
            
            # 為後續部分添加前文摘要
            if i > 0 and context:
                full_prompt = f"""前文摘要：
{context}

{prompt}"""
            else:
                full_prompt = prompt
            
            # 生成當前部分
            response = self.client.chat.completions.create(
                model=config.name,
                messages=[
                    {
                        "role": "system", 
                        "content": f"""您是一位專業的{chinese_style}長篇小說作家。
您擅長創作結構完整、情節緊湊的故事。
請確保每個部分都與前文緊密銜接，保持風格一致。"""
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                max_tokens=3000,        # 每部分的最大 token 數
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            part_content = response.choices[0].message.content
            story_parts.append(f"\n\n【{part_name}】\n\n{part_content}")
            
            # 生成當前部分的摘要作為下一部分的上下文
            if i < 3:  # 不是最後一部分
                summary_response = self.client.chat.completions.create(
                    model=config.name,
                    messages=[
                        {
                            "role": "system", 
                            "content": "請簡要總結故事內容，保留關鍵情節和角色狀態，約100-150字。"
                        },
                        {
                            "role": "user", 
                            "content": f"請總結以下內容：\n{part_content}"
                        }
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                context = summary_response.choices[0].message.content
        
        # 合併所有部分
        full_story = "".join(story_parts)
        
        # 添加字數統計
        word_count = len(full_story.replace(" ", "").replace("\n", ""))
        full_story = f"【故事全文】（共 {word_count} 字）\n{full_story}"
        
        return full_story
        
    except Exception as e:
        return f"Error generating long story with {config.display_name}: {str(e)}"
```

## 📝 更新的 `app.py` (Tab 3 部分)

```python
# ========== Tab 3: 生成完整故事 ==========
with tab3:
    st.header("Step 3: Generate Complete Story")
    
    if st.session_state.selected_plots:
        st.subheader("📋 Selected Plots")
        
        # 顯示已選擇的情節（可展開）
        with st.expander("View selected plots", expanded=False):
            for idx, plot in enumerate(st.session_state.selected_plots):
                st.write(f"{idx+1}. **{plot['model']}**: {plot['plot']}")
        
        st.divider()
        
        # ========== 生成模式選擇 ==========
        generation_mode = st.radio(
            "選擇生成模式 Generation Mode:",
            options=["標準模式 Standard", "長篇模式 Extended"],
            horizontal=True,
            help="標準模式：500-2500字 | 長篇模式：3000-8000字（分段生成）"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 選擇用於生成故事的模型
            if available_models:
                story_model_options = {model['display_name']: model['key'] 
                                     for model in available_models}
                
                # 根據模式調整可選模型數量
                max_models = 3 if generation_mode == "標準模式 Standard" else 1
                
                selected_story_displays = st.multiselect(
                    f"Select models for story generation (max {max_models}):",
                    list(story_model_options.keys()),
                    default=list(story_model_options.keys())[:min(1, len(story_model_options))],
                    max_selections=max_models
                )
                
                story_models = [story_model_options[name] for name in selected_story_displays]
            
            # 故事風格選擇
            story_style = st.selectbox(
                "Story style 故事風格:",
                ["Narrative 敘事", "Mystery 懸疑", "Sci-Fi 科幻", 
                 "Fantasy 奇幻", "Romance 浪漫", "Thriller 驚悚", 
                 "Comedy 喜劇", "Drama 戲劇", "Horror 恐怖", "Adventure 冒險"]
            )
            # 提取英文風格名稱
            style_english = story_style.split()[0].lower()
            
            # 標準模式的長度選擇
            if generation_mode == "標準模式 Standard":
                story_length = st.select_slider(
                    "Story length 故事長度:",
                    options=["Short 短篇 (500-800字)", 
                            "Medium 中篇 (1000-1500字)", 
                            "Long 長篇 (1500-2500字)"],
                    value="Medium 中篇 (1000-1500字)"
                )
                # 提取長度類型
                if "Short" in story_length:
                    length_type = "short"
                elif "Long" in story_length:
                    length_type = "long"
                else:
                    length_type = "medium"
            else:
                st.info("長篇模式將生成 3000-8000 字的完整故事，分為起承轉合四個部分。")
        
        with col2:
            if generation_mode == "標準模式 Standard":
                st.info("""
                **📖 標準模式：**
                - 多個模型同時生成
                - 快速生成
                - 適合短中篇故事
                - 可下載為 Markdown
                """)
            else:
                st.info("""
                **📚 長篇模式：**
                - 單一模型分段生成
                - 起承轉合四部分
                - 3000-8000字長篇
                - 保持情節連貫性
                """)
        
        # ========== 生成故事按鈕 ==========
        if st.button("✨ Generate Stories", type="primary"):
            # 合併所有選定的情節
            combined_plots = "\n".join([f"- {p['plot']}" for p in st.session_state.selected_plots])
            
            if generation_mode == "標準模式 Standard":
                # ===== 標準模式生成 =====
                with st.spinner("Creating your stories..."):
                    stories = []
                    progress = st.progress(0)
                    
                    for idx, model_key in enumerate(story_models):
                        progress.progress((idx + 1) / len(story_models))
                        
                        model_name = next(m['display_name'] for m in available_models 
                                        if m['key'] == model_key)
                        
                        st.info(f"Generating story with {model_name}...")
                        
                        # 調用標準生成方法
                        story = st.session_state.llm_manager.generate_story(
                            model_key, combined_plots, style_english, length_type
                        )
                        
                        stories.append({
                            'model': model_name,
                            'story': story,
                            'metadata': {
                                'title': f"{story_style.split()[0]} Story",
                                'model': model_name,
                                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'style': story_style,
                                'length': story_length,
                                'based_on_plots': len(st.session_state.selected_plots)
                            }
                        })
                    
                    progress.empty()
                    st.success("✅ Stories generated successfully!")
                    
                    # 顯示生成的故事
                    for story_data in stories:
                        st.divider()
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader(f"📖 {story_data['metadata']['title']} by {story_data['model']}")
                        
                        with col2:
                            markdown_content = f"""# {story_data['metadata']['title']}

**Generated by:** {story_data['metadata']['model']}  
**Date:** {story_data['metadata']['date']}  
**Style:** {story_data['metadata']['style']}  
**Length:** {story_data['metadata']['length']}  
**Based on:** {story_data['metadata']['based_on_plots']} selected plots  

---

{story_data['story']}

---

*Generated by PlotWeaver*  
*Powered by Stima API*
"""
                            
                            st.download_button(
                                label=f"📥 Download",
                                data=markdown_content,
                                file_name=f"story_{style_english}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key=f"download_{story_data['model']}_{idx}"
                            )
                        
                        with st.container():
                            st.markdown(story_data['story'])
            
            else:
                # ===== 長篇模式生成 =====
                if len(story_models) > 0:
                    model_key = story_models[0]
                    model_name = next(m['display_name'] for m in available_models 
                                    if m['key'] == model_key)
                    
                    # 創建進度容器
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 定義進度回調函數
                        def update_progress(message, progress):
                            status_text.text(message)
                            progress_bar.progress(progress)
                        
                        # 調用長篇生成方法
                        long_story = st.session_state.llm_manager.generate_long_story(
                            model_key, 
                            combined_plots, 
                            style_english,
                            progress_callback=update_progress
                        )
                        
                        progress_bar.empty()
                        status_text.empty()
                    
                    st.success("✅ Long story generated successfully!")
                    
                    # 顯示長篇故事
                    st.divider()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"📚 Extended {story_style.split()[0]} Story by {model_name}")
                    
                    with col2:
                        markdown_content = f"""# Extended {story_style.split()[0]} Story

**Generated by:** {model_name}  
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Style:** {story_style}  
**Type:** Extended (3000-8000 words)  
**Based on:** {len(st.session_state.selected_plots)} selected plots  

---

{long_story}

---

*Generated by PlotWeaver - Extended Mode*  
*Powered by Stima API*
"""
                        
                        st.download_button(
                            label=f"📥 Download Extended",
                            data=markdown_content,
                            file_name=f"extended_story_{style_english}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    
                    with st.container():
                        st.markdown(long_story)
                else:
                    st.error("請至少選擇一個模型")
    
    else:
        st.info("✋ Please select plots in Tab 2 first")
        
        if st.session_state.generated_plots:
            if st.button("🚀 Quick Start - Select All Plots"):
                st.session_state.selected_plots = st.session_state.generated_plots.copy()
                st.rerun()
```

## 🎯 主要特點

1. **雙模式選擇**：使用者可以選擇標準模式或長篇模式
2. **標準模式**：支援多模型、快速生成、500-2500字
3. **長篇模式**：單一模型、分段生成、3000-8000字、顯示進度
4. **智能提示**：不同模式有不同的UI提示和限制
5. **進度顯示**：長篇模式會顯示生成進度（起承轉合）
6. **下載功能**：兩種模式都支援 Markdown 格式下載

這樣的設計給使用者最大的彈性，可以根據需求選擇最適合的生成方式！
