import gradio as gr
import os
from openai import OpenAI
from typing import List, Dict
import json
import random

# 設定 API
api_key = os.environ.get('STIMA_API_KEY', '')
client = None
available_models = []

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.stima.tech/v1"
    )
    available_models = [
        'gpt-3.5-turbo',
        'gpt-4o-mini',
        'claude-3-haiku',
        'gemini-1.5-flash',
        'deepseek-chat',
    ]

# 全局變數儲存狀態
generated_plots = []
selected_plots = []

def generate_plots(theme, num_models, num_plots_per_model):
    """生成故事情節"""
    global generated_plots
    
    if not client:
        return "❌ Please set STIMA_API_KEY", ""
    
    if not theme:
        return "❌ Please enter a theme", ""
    
    generated_plots = []
    results = []
    
    # 隨機選擇模型
    selected_models = random.sample(available_models, 
                                  min(num_models, len(available_models)))
    
    for model in selected_models:
        for i in range(num_plots_per_model):
            try:
                prompt = f"""Create a unique story plot based on: {theme}
                Variation {i+1}. Be creative and original. About 50-100 words."""
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a creative story writer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.8
                )
                
                plot = response.choices[0].message.content
                generated_plots.append({
                    'model': model,
                    'plot': plot,
                    'id': f"{model}_{i}"
                })
                results.append(f"**[{model}]**\n{plot}\n")
                
            except Exception as e:
                results.append(f"Error with {model}: {str(e)}\n")
    
    # 分群
    clustered = cluster_plots(generated_plots)
    
    return "\n---\n".join(results), clustered

def cluster_plots(plots):
    """簡單分群"""
    if not plots:
        return "No plots to cluster"
    
    output = "## Clustered Plots\n\n"
    
    # 簡單按模型分組
    models = {}
    for i, plot in enumerate(plots):
        model = plot['model']
        if model not in models:
            models[model] = []
        models[model].append(f"{i+1}. {plot['plot'][:100]}...")
    
    for model, plot_list in models.items():
        output += f"### {model}\n"
        for plot in plot_list:
            output += f"- {plot}\n"
        output += "\n"
    
    return output

def generate_story(selected_indices, style, length):
    """生成完整故事"""
    global generated_plots
    
    if not client:
        return "❌ Please set STIMA_API_KEY"
    
    if not generated_plots:
        return "❌ Please generate plots first"
    
    # 解析選擇的索引
    try:
        indices = [int(i.strip())-1 for i in selected_indices.split(',') 
                  if i.strip().isdigit()]
    except:
        return "❌ Invalid indices. Use format: 1,3,5"
    
    if not indices:
        return "❌ Please select plot indices (e.g., 1,3,5)"
    
    # 獲取選中的情節
    selected = [generated_plots[i]['plot'] 
               for i in indices if 0 <= i < len(generated_plots)]
    
    if not selected:
        return "❌ No valid plots selected"
    
    combined_plots = "\n".join(selected)
    
    # 選擇一個模型生成故事
    model = random.choice(available_models)
    
    try:
        word_count = {"Short": 500, "Medium": 1000, "Long": 1500}[length]
        
        prompt = f"""Based on these plots:
        {combined_plots}
        
        Write a complete {style.lower()} story.
        Make it approximately {word_count} words.
        Include vivid descriptions and character development."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a skilled {style} writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        story = response.choices[0].message.content
        
        return f"# Generated {style} Story\n\n*Model: {model}*\n\n---\n\n{story}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Gradio 介面
with gr.Blocks(title="Story Generator Hub", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎭 Story Generator Hub
    
    Generate creative stories using AI models via Stima API.
    """)
    
    with gr.Tab("📝 Generate Plots"):
        with gr.Row():
            with gr.Column(scale=2):
                theme_input = gr.Textbox(
                    label="Story Theme",
                    placeholder="A mysterious adventure in a futuristic city...",
                    lines=2
                )
                
                with gr.Row():
                    num_models = gr.Slider(
                        minimum=1, maximum=5, value=3, step=1,
                        label="Number of Models"
                    )
                    num_plots = gr.Slider(
                        minimum=1, maximum=3, value=2, step=1,
                        label="Plots per Model"
                    )
                
                generate_btn = gr.Button("🎲 Generate Plots", variant="primary")
            
            with gr.Column(scale=1):
                gr.Markdown("""
                ### 💡 Tips
                - Enter any theme or idea
                - More models = more diversity
                - Each model generates unique plots
                """)
        
        plots_output = gr.Markdown(label="Generated Plots")
        clusters_output = gr.Markdown(label="Clustered Plots")
        
        generate_btn.click(
            generate_plots,
            inputs=[theme_input, num_models, num_plots],
            outputs=[plots_output, clusters_output]
        )
    
    with gr.Tab("📖 Generate Story"):
        with gr.Row():
            with gr.Column():
                indices_input = gr.Textbox(
                    label="Select Plot Indices",
                    placeholder="Enter numbers separated by commas: 1,3,5",
                    info="Based on the numbered plots above"
                )
                
                with gr.Row():
                    style_select = gr.Dropdown(
                        choices=["Narrative", "Mystery", "Sci-Fi", "Fantasy", 
                                "Romance", "Thriller", "Comedy"],
                        value="Narrative",
                        label="Story Style"
                    )
                    length_select = gr.Radio(
                        choices=["Short", "Medium", "Long"],
                        value="Medium",
                        label="Story Length"
                    )
                
                story_btn = gr.Button("✨ Generate Story", variant="primary")
            
            with gr.Column():
                gr.Markdown("""
                ### 📚 Instructions
                1. Generate plots first
                2. Note the plot numbers
                3. Enter numbers (e.g., 1,3,5)
                4. Choose style and length
                5. Generate your story!
                """)
        
        story_output = gr.Markdown(label="Generated Story")
        
        story_btn.click(
            generate_story,
            inputs=[indices_input, style_select, length_select],
            outputs=story_output
        )
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## About Story Generator Hub
        
        This application uses multiple AI models to generate creative stories.
        
        ### Features:
        - 🤖 Multiple model support via Stima API
        - 📚 Plot generation and clustering
        - ✨ Full story generation
        - 🎨 Multiple story styles
        
        ### API Setup:
        - Get your API key from [Stima](https://stima.tech)
        - Add it to Space secrets as `STIMA_API_KEY`
        
        ### Models Available:
        - GPT-3.5/4
        - Claude
        - Gemini
        - Llama
        - DeepSeek
        """)

if __name__ == "__main__":
    demo.launch()
