import json
import os
import re
import uuid
import streamlit as st
import pandas as pd
from .custom import *
import copy
import io


def get_history_chats(path: str) -> list:
    
    os.makedirs(path, exist_ok=True)
    files = [f for f in os.listdir(f'./{path}') if f.endswith('.json')]
    files_with_time = [(f, os.stat(f'./{path}/' + f).st_ctime) for f in files]
    sorted_files = sorted(files_with_time, key=lambda x: x[1], reverse=True)
    chat_names = [os.path.splitext(f[0])[0] for f in sorted_files]
    return chat_names if chat_names else ['New Chat_' + str(uuid.uuid4())]


def save_data(path: str, file_name: str, history: list, contexts: dict, **kwargs):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(f"./{path}/{file_name}.json", 'w', encoding='utf-8') as f:
        json.dump({"history": history, "contexts": contexts, **kwargs}, f)


def remove_data(path: str, chat_name: str):
    try:
        os.remove(f"./{path}/{chat_name}.json")
    except FileNotFoundError:
        pass
    # clear cache
    try:
        st.session_state.pop('history' + chat_name)
        for item in ["context_select", "context_input", "context_level", *initial_content_all['paras']]:
            st.session_state.pop(item + chat_name + "value")
    except KeyError:
        pass


def load_data(path: str, file_name: str) -> dict:
    try:
        with open(f"./{path}/{file_name}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        content = copy.deepcopy(initial_content_all)
        with open(f"./{path}/{file_name}.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(content))
        return content


def show_each_message(message: str, role: str, idr: str, area=None):
    if area is None:
        area = [st.markdown] * 2
    if role == 'user':
        name = user_name
        background_color = user_background_color
        data_idr = idr + "_user"
        class_name = 'user'
    else:
        name = gpt_name
        background_color = gpt_background_color
        data_idr = idr + "_assistant"
        class_name = 'assistant'
    message = url_correction(message)
    area[0](f"\n<div class='avatar'><h2>{name}：</h2></div>", unsafe_allow_html=True)
    area[1](
        f"""<div class='content-div {class_name}' data-idr='{data_idr}' style='background-color: {background_color};'>\n\n{message}""",
        unsafe_allow_html=True)


def show_messages(current_chat: str, messages: list):
    id_role = 0
    id_assistant = 0
    for each in messages:
        if each["role"] == "user":
            idr = id_role
            id_role += 1
        elif each["role"] == "assistant":
            idr = id_assistant
            id_assistant += 1
        else:
            idr = False
        if idr is not False:
            show_each_message(each["content"], each["role"], str(idr))
        if each["role"] == "assistant":
            st.write("---")


# Extract history based on context_level
def get_history_input(history: list, level: int) -> list:
    if level != 0 and history:
        df_input = pd.DataFrame(history).query('role!="system"')
        df_input = df_input[-level * 2:]
        res = df_input.to_dict('records')
    else:
        res = []
    return res

# Extract text
def extract_chars(text: str, num: int) -> str:
    char_num = 0
    chars = ''
    for char in text:
        # Chinese characters count as two characters
        if '\u4e00' <= char <= '\u9fff':
            char_num += 2
        else:
            char_num += 1
        chars += char
        if char_num >= num:
            break
    return chars


@st.cache_data(max_entries=20, show_spinner=False)
def download_history(history: list):
    md_text = ""
    for msg in history:
        if msg['role'] == 'user':
            md_text += f'## {user_name}：\n{msg["content"]}\n'
        elif msg['role'] == 'assistant':
            md_text += f'## {gpt_name}：\n{msg["content"]}\n'
    output = io.BytesIO()
    output.write(md_text.encode('utf-8'))
    output.seek(0)
    return output

def url_correction(text: str) -> str:
    pattern = r'((?:http[s]?://|www\.)(?:[a-zA-Z0-9]|[$-_\~#!])+)'
    text = re.sub(pattern, r' \g<1> ', text)
    return text

def filename_correction(filename: str) -> str:
    pattern = r'[^\w\.-]'
    filename = re.sub(pattern, '', filename)
    return filename