import streamlit as st
from datetime import datetime
import random
from utils.llm_manager import LLMManager
from utils.story_processor import StoryProcessor

# 初始化
st.set_page_config(page_title="Story Generator Hub", layout="wide")

if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()
    st.session_state.processor = StoryProcessor()
    st.session_state.generated_plots = []
    st.session_state.selected_plots = []
    st.session_state.clustered_plots = []

st.title("🎭 Story Generator Hub")
st.markdown("Generate creative stories using multiple AI models")

# 側邊欄 - 模型選擇
with st.sidebar:
    st.header("Settings")
    available_models = st.session_state.llm_manager.get_available_models()
    
    if not available_models:
        st.error("No models available. Please check your API keys in .env file")
    else:
        st.success(f"✅ {len(available_models)} models available")

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
            "A mysterious adventure in a futuristic city",
            height=100
        )
        
        # 選擇模型
        if available_models:
            selected_models = st.multiselect(
                "Select models for plot generation (max 5):",
                available_models,
                default=available_models[:min(3, len(available_models))]
            )
            
            if st.button("🎲 Random Selection"):
                num_models = min(5, len(available_models))
                selected_models = random.sample(available_models, 
                                              random.randint(1, num_models))
                st.rerun()
    
    with col2:
        st.info("""
        **Tips:**
        - Select multiple models for diverse plots
        - Use random selection for surprise
        - Each model will generate 2-3 plot variations
        """)
    
    if st.button("Generate Plots", type="primary", disabled=not available_models):
        with st.spinner("Generating plots..."):
            plots = []
            
            # 為每個選定的模型生成情節
            for model in selected_models:
                for i in range(2):  # 每個模型生成2個情節
                    plot_prompt = f"{base_prompt} - Create a unique plot outline (variation {i+1})"
                    plot_text = st.session_state.llm_manager.generate_plot(
                        model, plot_prompt
                    )
                    plots.append({
                        'model': model,
                        'plot': plot_text,
                        'id': f"{model}_{i}"
                    })
            
            st.session_state.generated_plots = plots
            
            # 自動分群
            if len(plots) > 0:
                st.session_state.clustered_plots = st.session_state.processor.cluster_plots(plots)
    
    # 顯示生成的情節
    if st.session_state.generated_plots:
        st.subheader("Generated Plots")
        for i, plot in enumerate(st.session_state.generated_plots):
            with st.expander(f"Plot {i+1} - {plot['model']}"):
                st.write(plot['plot'])

# Tab 2: 選擇情節
with tab2:
    st.header("Step 2: Select Plot Groups")
    
    if st.session_state.clustered_plots:
        st.subheader("Clustered Plot Groups")
        
        selected_groups = []
        for i, group in enumerate(st.session_state.clustered_plots):
            st.write(f"**Group {i+1}: {group['theme']}**")
            
            # 顯示該群組的情節
            for idx in group['plot_indices']:
                if idx <= len(st.session_state.generated_plots):
                    plot = st.session_state.generated_plots[idx-1]
                    if st.checkbox(f"{plot['model']}: {plot['plot'][:100]}...", 
                                 key=f"plot_{idx}"):
                        if plot not in st.session_state.selected_plots:
                            st.session_state.selected_plots.append(plot)
            
            st.divider()
    else:
        st.info("Please generate plots first in Tab 1")

# Tab 3: 生成故事
with tab3:
    st.header("Step 3: Generate Complete Story")
    
    if st.session_state.selected_plots:
        st.subheader("Selected Plots")
        for plot in st.session_state.selected_plots:
            st.info(f"{plot['model']}: {plot['plot'][:150]}...")
        
        # 選擇用於生成故事的模型
        story_models = st.multiselect(
            "Select models for story generation (max 3):",
            available_models,
            default=available_models[:min(1, len(available_models))]
        )
        
        story_style = st.selectbox(
            "Story style:",
            ["Narrative", "Mystery", "Sci-Fi", "Fantasy", "Romance"]
        )
        
        if st.button("Generate Story", type="primary"):
            with st.spinner("Generating story..."):
                # 合併選定的情節
                combined_plot = " ".join([p['plot'] for p in st.session_state.selected_plots])
                
                stories = []
                for model in story_models:
                    story = st.session_state.llm_manager.generate_story(
                        model, combined_plot, story_style.lower()
                    )
                    stories.append({
                        'model': model,
                        'story': story,
                        'metadata': {
                            'title': f"{story_style} Story",
                            'model': model,
                            'date': datetime.now().strftime("%Y-%m-%d"),
                            'plot': combined_plot[:200]
                        }
                    })
                
                # 顯示生成的故事
                for story_data in stories:
                    st.subheader(f"Story by {story_data['model']}")
                    
                    # Markdown 輸出
                    markdown_content = st.session_state.processor.format_to_markdown(
                        story_data['story'],
                        story_data['metadata']
                    )
                    
                    st.markdown(markdown_content)
                    
                    # 下載按鈕
                    st.download_button(
                        label=f"Download {story_data['model']} story",
                        data=markdown_content,
                        file_name=f"story_{story_data['model']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
    else:
        st.info("Please select plots in Tab 2 first")
