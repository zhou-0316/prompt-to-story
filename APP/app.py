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
st.markdown("Generate creative stories using multiple AI models from Your API and Stima")

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
