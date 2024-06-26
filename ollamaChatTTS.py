import streamlit as st
import random
import os

import ollama as ol
from voice import record_voice
from llmChat import print_chat_message
import requests
import base64

st.header(':rainbow[:speech_balloon: HAI-多模态AGENT]')

tab_chat, tab_ChatTTS, tab_setup = st.tabs(
    ["读图大师", "ChatTTS 设置", "Ollama 设置"]
)

def generate_seed():
    new_seed = random.randint(1, 100000000)
    st.session_state.Audio_Seed = new_seed

def generate_seed2():
    new_seed = random.randint(1, 100000000)
    st.session_state.Text_Seed = new_seed

def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    with tab_setup:
        return st.selectbox("语言 Language", ["zh"] + lang_options)

def OllamaModel():
    ollama_models = [m['name'] for m in ol.list()['models']]
    with tab_setup:
        return st.selectbox("模型 Ollama Models", ollama_models)

def OllamaServer():
    OllamaServer = st.text_input("Ollama Server URL", "http://127.0.0.1:6399")

def ChatTTSServer():
    ChatTTSServer = st.text_input("ChatTTS Server URL", "http://150.109.229.220:9966/tts")
    col1, col2 = st.columns(2)
    with col1:
        audio_seed_input = st.number_input("音色 Audio Seed", value=42, key='Audio_Seed')
        st.button(":game_die: Audio Seed", on_click=generate_seed, use_container_width=True)
        Audio_temp = st.slider('语调 Audio temperature ', min_value=0.01, max_value=1.0, value=0.3, step=0.05, key="Audiotemperature")
        oral_input = st.slider(label="口语化 Oral", min_value=0, max_value=9, value=2, step=1)
        laugh_input = st.slider(label="笑声 Laugh", min_value=0, max_value=2, value=0, step=1)
        Refine_text = st.checkbox("格式化文本 Refine text", value=True, key='Refine_text')
    with col2:
        text_seed_input = st.number_input("Text Seed", value=42, key='Text_Seed')
        st.button(":game_die: Text Seed", on_click=generate_seed2, use_container_width=True)
        Top_P = st.slider('top_P', min_value=0.1, max_value=0.9, value=0.3, step=0.1, key="top_P")
        Top_K = st.slider('top_K', min_value=1, max_value=20, value=20, step=1, key="top_K") 
        bk_input = st.slider(label="停顿 Break", min_value=0, max_value=7, value=4, step=1)
        TTSServer = ChatTTSServer
    return TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text

def save_uploaded_file(uploaded_file):
    try:
        os.makedirs('uploaded_files', exist_ok=True)
        file_path = os.path.join('uploaded_files', uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        return file_path, encoded_string  # 返回文件路径和 base64 编码的图片
    except Exception as e:
        print(e)
        return None, None

def main():
    with tab_setup:
        server = OllamaServer()
        model = OllamaModel()
        language = language_selector()

    with tab_ChatTTS:
        TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text = ChatTTSServer()

    # with tab_upload:
    #     uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])
    #     if uploaded_file is not None:
    #         file_path, base64_image = save_uploaded_file(uploaded_file)
    #         if file_path:
    #             server_url = "http://127.0.0.1:8000/"  # Adjust as necessary
    #             full_path = f"{server_url}{file_path}"
    #             st.text_area("Image URL", full_path, height=100)
    #             st.session_state.base64_image = base64_image

    with tab_chat:

        uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])
        if uploaded_file is not None:
            file_path, base64_image = save_uploaded_file(uploaded_file)
            if file_path:
                server_url = "http://127.0.0.1:8000/"  # Adjust as necessary
                full_path = f"{server_url}{file_path}"
                # st.text_area("Image URL", full_path, height=100)
                st.image('./'+file_path)
                st.session_state.base64_image = base64_image
        
        col1, col2 = st.columns([4,1])
        with col1:
            text_input = st.text_input('', placeholder="点击输入，按回车发送", label_visibility='collapsed', key="text_input_key")
        with col2:
            question = record_voice(language=language)

        with st.container():
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}
            if model not in st.session_state.chat_history:
                st.session_state.chat_history[model] = []
            chat_history = st.session_state.chat_history[model]

            for message in chat_history:
                print_chat_message(message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text)

            if question or text_input:
                user_message = {
                    "role": "user", 
                    "content": question or text_input,
                    "ChatTTSServer": TTSServer,
                    "audio_seed_input": st.session_state.Audio_Seed,
                    "Audio_temp": Audio_temp,
                    "Top_P": Top_P,
                    "Top_K": Top_K,
                    "Refine_text": Refine_text,
                    "images": [st.session_state.base64_image] if "base64_image" in st.session_state else [],
                }
                print_chat_message(user_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text)
                chat_history.append(user_message)
                response = ol.chat(model=model, messages=chat_history)
                answer = response['message']['content']
                ai_message = {
                    "role": "assistant", 
                    "content": answer,
                    "ChatTTSServer": TTSServer,
                    "audio_seed_input": st.session_state.Audio_Seed,
                    "Audio_temp": Audio_temp,
                    "Top_P": Top_P,
                    "Top_K": Top_K,
                    "Refine_text": Refine_text,
                }
                print_chat_message(ai_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text)
                chat_history.append(ai_message)

                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]
                st.session_state.chat_history[model] = chat_history

if __name__ == "__main__":
    main()
