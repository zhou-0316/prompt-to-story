import streamlit as st
from datetime import datetime
import random
from utils.llm_manager import LLMManager
from utils.story_processor import StoryProcessor

# 初始化
st.set_page_config(page_title="Story Generator Hub", layout="wide", page_icon="🎭")

if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()
    st.session_state.processor = StoryProcessor()
    st.session_state.generated_plots = []
    st.session_state.selected_plots = []
    st.session_state.clustered_plots = []

st.title("🎭 PlotWeaver")
st.markdown("Generate creative stories using multiple AI models from YourAPI and Stima")

# 側邊欄 - 模型資訊
with st.sidebar:
    st.header("⚙️ Configuration")
    
    available_models = st.session_state.llm_manager.get_available_models()
    
    if not available_models:
        st.error("❌ No models available")
        st.info("""
        Please add your API keys in `.env` file:
        - YOURAPI_KEY
        - STIMA_API_KEY
        """)
    else:
        st.success(f"✅ {len(available_models)} models available")
        
        with st.expander("View Available Models"):
            for model in available_models:
                st.write(f"• {model['display_name']}")
    
    st.divider()
    
    # API 資訊
    st.subheader("📊 API Status")
    col1, col2 = st.columns(2)
    with col1:
        if 'yourapi' in st.session_state.llm_manager.clients:
            st.success("YourAPI ✓")
        else:
            st.error("YourAPI ✗")
    
    with col2:
        if 'stima' in st.session_state.llm_manager.clients:
            st.success("Stima ✓")
        else:
            st.error("Stima ✗")

# 主要內容區
tab1, tab2, tab3 = st.tabs(["📝 Generate Plots", "✅ Select Plots", "📖 Generate Story"])

# Tab 1: 生成情節
with tab1:
    st.header("Step 1: Generate Story Plots")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 基本 prompt
        base_prompt = st.text_area(
            "Enter your story theme or idea:",
            "A mysterious adventure in a futuristic city where AI and humans coexist",
            height=100
        )
        
        # 選擇模型
        if available_models:
            # 創建顯示名稱到 key 的映射
            model_options = {model['display_name']: model['key'] 
                           for model in available_models}
            
            selected_display_names = st.multiselect(
                "Select models for plot generation (max 5):",
                list(model_options.keys()),
                default=list(model_options.keys())[:min(3, len(model_options))]
            )
            
            # 轉換回實際的 model keys
            selected_models = [model_options[name] for name in selected_display_names]
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🎲 Random Selection"):
                    num_models = min(5, len(available_models))
                    random_models = random.sample(list(model_options.keys()), 
                                                random.randint(2, num_models))
                    st.rerun()
            
            with col_b:
                num_variations = st.number_input("Plots per model:", 
                                               min_value=1, max_value=3, value=2)
    
    with col2:
        st.info("""
        **💡 Tips:**
        - YourAPI supports GPT, Claude, Gemini, Llama models
        - Stima provides various open-source models
        - Mix different models for creative diversity
        """)
    
    if st.button("🚀 Generate Plots", type="primary", disabled=not available_models):
        with st.spinner("Generating plots from multiple models..."):
            plots = []
            progress_bar = st.progress(0)
            total_tasks = len(selected_models) * num_variations
            current_task = 0
            
            # 為每個選定的模型生成情節
            for model_key in selected_models:
                model_name = next(m['display_name'] for m in available_models 
                                if m['key'] == model_key)
                
                for i in range(num_variations):
                    current_task += 1
                    progress_bar.progress(current_task / total_tasks)
                    
                    plot_prompt = f"""Create a unique story plot based on: {base_prompt}
                    
                    Variation {i+1}: Focus on a different aspect or perspective.
                    Be creative and original. About 50-100 words."""
                    
                    plot_text = st.session_state.llm_manager.generate_plot(
                        model_key, plot_prompt
                    )
                    
                    plots.append({
                        'model': model_name,
                        'plot': plot_text,
                        'id': f"{model_key}_{i}"
                    })
            
            progress_bar.empty()
            st.session_state.generated_plots = plots
            
            # 使用 AI 自動分群
            if len(plots) > 0:
                with st.spinner("Analyzing and clustering plots..."):
                    st.session_state.clustered_plots = st.session_state.llm_manager.cluster_plots_with_ai(plots)
                st.success(f"✅ Generated {len(plots)} plots and organized them into {len(st.session_state.clustered_plots)} groups")
    
    # 顯示生成的情節
    if st.session_state.generated_plots:
        st.divider()
        st.subheader("📚 Generated Plots")
        
        for i, plot in enumerate(st.session_state.generated_plots):
            with st.expander(f"Plot {i+1} - {plot['model']}", expanded=(i==0)):
                st.write(plot['plot'])
                st.caption(f"Model: {plot['model']} | ID: {plot['id']}")

# Tab 2: 選擇情節
with tab2:
    st.header("Step 2: Select Plot Groups")
    
    if st.session_state.clustered_plots:
        st.info(f"Found {len(st.session_state.clustered_plots)} plot groups. Select the plots you want to use for story generation.")
        
        # 清除之前的選擇
        if st.button("🔄 Clear Selection"):
            st.session_state.selected_plots = []
            st.rerun()
        
        for group_idx, group in enumerate(st.session_state.clustered_plots):
            with st.expander(f"**Group {group_idx+1}: {group['theme']}**", expanded=True):
                if 'common_elements' in group:
                    st.caption(f"Common elements: {group['common_elements']}")
                
                st.write("**Plots in this group:**")
                
                # 顯示該群組的情節
                for idx in group['plot_indices']:
                    if idx <= len(st.session_state.generated_plots):
                        plot = st.session_state.generated_plots[idx-1]
                        
                        col1, col2 = st.columns([1, 10])
                        with col1:
                            is_selected = st.checkbox("", key=f"plot_select_{idx}",
                                                    value=(plot in st.session_state.selected_plots))
                        with col2:
                            st.write(f"**{plot['model']}**")
                            st.write(plot['plot'])
                        
                        if is_selected and plot not in st.session_state.selected_plots:
                            st.session_state.selected_plots.append(plot)
                        elif not is_selected and plot in st.session_state.selected_plots:
                            st.session_state.selected_plots.remove(plot)
                
                st.divider()
        
        # 顯示已選擇的數量
        if st.session_state.selected_plots:
            st.success(f"✅ Selected {len(st.session_state.selected_plots)} plots")
    else:
        st.info("📝 Please generate plots first in Tab 1")

# Tab 3: 生成故事
with tab3:
    st.header("Step 3: Generate Complete Story")
    
    if st.session_state.selected_plots:
        st.subheader("📋 Selected Plots")
        
        # 顯示選中的情節
        with st.expander("View selected plots", expanded=False):
            for idx, plot in enumerate(st.session_state.selected_plots):
                st.write(f"{idx+1}. **{plot['model']}**: {plot['plot']}")
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 選擇用於生成故事的模型
            if available_models:
                story_model_options = {model['display_name']: model['key'] 
                                     for model in available_models}
                
                selected_story_displays = st.multiselect(
                    "Select models for story generation (max 3):",
                    list(story_model_options.keys()),
                    default=list(story_model_options.keys())[:min(2, len(story_model_options))],
                    max_selections=3
                )
                
                story_models = [story_model_options[name] for name in selected_story_displays]
            
            story_style = st.selectbox(
                "Story style:",
                ["Narrative", "Mystery", "Sci-Fi", "Fantasy", "Romance", 
                 "Thriller", "Comedy", "Drama", "Horror", "Adventure"]
            )
            
            story_length = st.select_slider(
                "Story length:",
                options=["Short (500 words)", "Medium (1000 words)", "Long (1500 words)"],
                value="Medium (1000 words)"
            )
        
        with col2:
            st.info("""
            **📖 Story Generation:**
            - Multiple models create different versions
            - Each brings unique perspective
            - Export as Markdown files
            """)
        
        if st.button("✨ Generate Stories", type="primary"):
            with st.spinner("Creating your stories..."):
                # 合併選定的情節
                combined_plots = "\n".join([f"- {p['plot']}" for p in st.session_state.selected_plots])
                
                stories = []
                progress = st.progress(0)
                
                for idx, model_key in enumerate(story_models):
                    progress.progress((idx + 1) / len(story_models))
                    
                    model_name = next(m['display_name'] for m in available_models 
                                     if m['key'] == model_key)
                    
                    st.info(f"Generating story with {model_name}...")
                    
                    story = st.session_state.llm_manager.generate_story(
                        model_key, combined_plots, story_style.lower()
                    )
                    
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
                
                progress.empty()
                st.success("✅ Stories generated successfully!")
                
                # 顯示生成的故事
                for story_data in stories:
                    st.divider()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"📖 {story_data['metadata']['title']} by {story_data['model']}")
                    
                    with col2:
                        # Markdown 格式化
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
        st.info("✋ Please select plots in Tab 2 first")
        
        # 提供快速開始選項
        if st.session_state.generated_plots:
            if st.button("🚀 Quick Start - Select All Plots"):
                st.session_state.selected_plots = st.session_state.generated_plots.copy()
                st.rerun()
