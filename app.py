import os.path
from audio_recorder_streamlit import audio_recorder
from libs.helper import *
import streamlit as st
import uuid
import pandas as pd
import openai
from requests.models import ChunkedEncodingError
from streamlit.components import v1
import tempfile
import requests

# Set the FastAPI endpoint URL
endpoint = "http://127.0.0.1:8000"
audio_url = f"{endpoint}/post-audio"
convert_audio_url = f"{endpoint}/convert-audio-to-text"
text_conversation_url = f"{endpoint}/text-conversation"
convert_text_speech_url = f"{endpoint}/convert-text-to-speech"
employee_type_url = f"{endpoint}/set-prompt"
reset_url = f"{endpoint}/reset"

st.set_page_config(
    page_title="ChatGPT Assistant",
    layout="wide",
    page_icon="🤖",
)

# Ensure set_context_list is defined globally
set_context_list = list(set_context_all.keys())

if "initial_settings" not in st.session_state:
    # History chat window
    st.session_state["path"] = "history_chats_file"
    st.session_state["history_chats"] = get_history_chats(st.session_state["path"])
    # ss parameter initialization
    st.session_state["delete_dict"] = {}
    st.session_state["delete_count"] = 0
    st.session_state["voice_flag"] = ""
    st.session_state["user_voice_value"] = ""
    st.session_state["error_info"] = ""
    st.session_state["current_chat_index"] = 0
    st.session_state["user_input_content"] = ""
    # Read global settings
    if os.path.exists("./set.json"):
        with open("./set.json", "r", encoding="utf-8") as f:
            data_set = json.load(f)
        for key, value in data_set.items():
            st.session_state[key] = value
    # Setup Complete
    st.session_state["initial_settings"] = True

with st.sidebar:
    # The purpose of creating a container is to cooperate with the listening operation of custom components
    chat_container = st.container()
    with chat_container:
        current_chat = st.radio(
            label="History chat window",
            format_func=lambda x: x.split("_")[0] if "_" in x else x,
            options=st.session_state["history_chats"],
            label_visibility="collapsed",
            index=st.session_state["current_chat_index"],
            key="current_chat"
            + st.session_state["history_chats"][st.session_state["current_chat_index"]],
            # on_change=current_chat_callback # Callback is not suitable here, and changes in window increase and decrease cannot be recognized
        )
    st.write("---")


# Write data to file
def write_data(new_chat_name=current_chat):
    
    st.session_state["contexts"] = {
        "context_select": st.session_state["context_select" + current_chat],
        "context_input": st.session_state["context_input" + current_chat],
        "context_level": st.session_state["context_level" + current_chat],
    }
    save_data(
        st.session_state["path"],
        new_chat_name,
        st.session_state["history" + current_chat],
        st.session_state["contexts"],
    )


def reset_chat_name_fun(chat_name):
    chat_name = chat_name + "_" + str(uuid.uuid4())
    new_name = filename_correction(chat_name)
    current_chat_index = st.session_state["history_chats"].index(current_chat)
    st.session_state["history_chats"][current_chat_index] = new_name
    st.session_state["current_chat_index"] = current_chat_index
    # Write to a new file
    write_data(new_name)
    # Transfer data
    st.session_state["history" + new_name] = st.session_state["history" + current_chat]
    for item in [
        "context_select",
        "context_input",
        "context_level",
    ]:
        st.session_state[item + new_name + "value"] = st.session_state[
            item + current_chat + "value"
        ]
    remove_data(st.session_state["path"], current_chat)


def create_chat_fun():
    new_chat_name = "New Chat_" + str(uuid.uuid4())
    st.session_state["history_chats"] = [new_chat_name] + st.session_state["history_chats"]
    st.session_state["current_chat_index"] = 0
    # Initialize default context for new chat
    st.session_state["context_select" + new_chat_name + "value"] = set_context_list[0]
    st.session_state["context_input" + new_chat_name + "value"] = ""
    st.session_state["context_level" + new_chat_name + "value"] = 3
    st.session_state["history" + new_chat_name] = []


def delete_chat_fun():
    if len(st.session_state["history_chats"]) == 1:
        create_chat_fun()
    pre_chat_index = st.session_state["history_chats"].index(current_chat)
    if pre_chat_index > 0:
        st.session_state["current_chat_index"] = pre_chat_index - 1
    else:
        st.session_state["current_chat_index"] = 0
    st.session_state["history_chats"].remove(current_chat)
    remove_data(st.session_state["path"], current_chat)


with st.sidebar:
    c1, c2 = st.columns(2)
    create_chat_button = c1.button(
        "New", use_container_width=True, key="create_chat_button"
    )
    if create_chat_button:
        create_chat_fun()
        st.rerun()

    delete_chat_button = c2.button(
        "delete", use_container_width=True, key="delete_chat_button"
    )
    if delete_chat_button:
        delete_chat_fun()
        st.rerun()

with st.sidebar:
    if ("set_chat_name" in st.session_state) and st.session_state[
        "set_chat_name"
    ] != "":
        reset_chat_name_fun(st.session_state["set_chat_name"])
        st.session_state["set_chat_name"] = ""
        st.rerun()

    st.write("\n")
    st.text_input("Set the window name:", key="set_chat_name", placeholder="Click Enter")

with st.sidebar:

    audio_response = st.toggle("Audio response", value=False)
    
    audio_prompt = None
    if "prev_speech_hash" not in st.session_state:
        st.session_state.prev_speech_hash = None

    speech_input = audio_recorder("Press to talk:", icon_size="3x", neutral_color="#6ca395", )
    if speech_input and st.session_state.prev_speech_hash != hash(speech_input):
        st.session_state.prev_speech_hash = hash(speech_input)
        with st.spinner("Transcribing..."):
            temp_input_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_input_file.write(speech_input)
            temp_input_file.close()
            with open(temp_input_file.name, "rb") as audio_file:
                text_response = requests.post(convert_audio_url, files={"file": audio_file})
        audio_prompt = text_response.json().get("text")

# Download Data
if "history" + current_chat not in st.session_state:
    for key, value in load_data(st.session_state["path"], current_chat).items():
        if key == "history":
            st.session_state[key + current_chat] = value
        else:
            for k, v in value.items():
                st.session_state[k + current_chat + "value"] = v

# Ensure that the page hierarchy of different chats is consistent, otherwise it will cause custom components to re-render
container_show_messages = st.container()
container_show_messages.write("")
# Dialogue display
with container_show_messages:
    if st.session_state["history" + current_chat]:
        show_messages(current_chat, st.session_state["history" + current_chat])

# Check if there are any conversations that need to be deleted
if any(st.session_state["delete_dict"].values()):
    for key, value in st.session_state["delete_dict"].items():
        try:
            deleteCount = value.get("deleteCount")
        except AttributeError:
            deleteCount = None
        if deleteCount == st.session_state["delete_count"]:
            delete_keys = key
            st.session_state["delete_count"] = deleteCount + 1
            delete_current_chat, idr = delete_keys.split(">")
            df_history_tem = pd.DataFrame(
                st.session_state["history" + delete_current_chat]
            )
            df_history_tem.drop(
                index=df_history_tem.query("role=='user'").iloc[[int(idr)], :].index,
                inplace=True,
            )
            df_history_tem.drop(
                index=df_history_tem.query("role=='assistant'")
                .iloc[[int(idr)], :]
                .index,
                inplace=True,
            )
            st.session_state["history" + delete_current_chat] = df_history_tem.to_dict(
                "records"
            )
            write_data()
            st.rerun()


def callback_fun(arg):
    # Clicking Create and Delete quickly and continuously will trigger an error callback, add a judgment
    if ("history" + current_chat in st.session_state) and (
        "frequency_penalty" + current_chat in st.session_state
    ):
        write_data()
        st.session_state[arg + current_chat + "value"] = st.session_state[
            arg + current_chat
        ]


def clear_button_callback():
    st.session_state["history" + current_chat] = []
    write_data()


def delete_all_chat_button_callback():
    
    folder_path = st.session_state["path"]
    file_list = os.listdir(folder_path)
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if file_name.endswith(".json") and os.path.isfile(file_path):
            os.remove(file_path)
    st.session_state["current_chat_index"] = 0
    st.session_state["history_chats"] = ["New Chat_" + str(uuid.uuid4())]

# Input content display
area_user_svg = st.empty()
area_user_content = st.empty()
# Reply display
area_gpt_svg = st.empty()
area_gpt_content = st.empty()
# Error display
area_error = st.empty()

st.write("\n")
st.header("Appraisal Assistant")
tap_input, tap_context, tab_func = st.tabs(
    ["💬 Chat", "🗒️ Employee Preset", "🛠️ Settings"]
)

with tap_context:
    set_context_list = list(set_context_all.keys())

    st.selectbox(
        label="Select prompt",
        options=set_context_list,
        key="context_select" + current_chat,
        index=set_context_list.index(st.session_state.get("context_select" + current_chat + "value", set_context_list[0])),
        on_change=callback_fun,
        args=("context_select",),
    )
    st.caption(set_context_all[st.session_state["context_select" + current_chat]])

    st.text_area(
        label="Additional Prompt: ",
        key="context_input" + current_chat,
        value=st.session_state.get("context_input" + current_chat + "value", ""),
        on_change=callback_fun,
        args=("context_input",),
    )

    st.slider(
        "Context Level",
        0,
        5,
        st.session_state.get("context_level" + current_chat + "value", 3),
        1,
        on_change=callback_fun,
        key="context_level" + current_chat,
        args=("context_level",),
        help="Indicates the number of historical conversations included in each session, excluding preset content. ",
    )

with tab_func:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button(
            "Clear chat history", use_container_width=True, on_click=clear_button_callback
        )
    with c2:
        btn = st.download_button(
            label="Export chat history",
            data=download_history(st.session_state["history" + current_chat]),
            file_name=f'{current_chat.split("_")[0]}.md',
            mime="text/markdown",
            use_container_width=True,
        )
    with c3:
        st.button(
            "Delete All Windows",
            use_container_width=True,
            on_click=delete_all_chat_button_callback,
        )

def input_callback():
    if st.session_state["user_input_area"] != "":
        # Modify the window name
        user_input_content = st.session_state["user_input_area"]
        df_history = pd.DataFrame(st.session_state["history" + current_chat])
        if df_history.empty or len(df_history.query('role!="system"')) == 0:
            new_name = extract_chars(user_input_content, 18)
            reset_chat_name_fun(new_name)

with tap_input:
    if st.session_state["context_select" + current_chat + "value"]:
        with st.form("input_form", clear_on_submit=True):
            user_input = st.text_area(
                "**enter:**",
                key="user_input_area",
                help="The content will be displayed on the page in Markdown format. It is recommended to follow the relevant language specifications, which is also conducive to GPT reading correctly, for example: "
                "\n- Code blocks are written in three backticks and marked with the language type"
                "\n- Contents or regular expressions starting with a colon are written in single backquotes.",
                value=st.session_state["user_voice_value"],
            )
            submitted = st.form_submit_button(
                "confirm submission", use_container_width=True, on_click=input_callback
            )
        if submitted:
            st.session_state["user_input_content"] = user_input
            st.session_state["user_voice_value"] = ""
            st.rerun()
            
        # Voice input function
        vocie_result = audio_prompt
        # vocie_result will save the last result
        if audio_prompt:
            st.session_state["user_voice_value"] = audio_prompt
            st.session_state["voice_flag"] = "final"
            st.rerun()
    else:
        st.warning("Please set the context before starting the conversation.")

 
def get_model_input():
    # History records to be entered
    context_level = st.session_state["context_level" + current_chat]
    history = get_history_input(
        st.session_state["history" + current_chat], context_level
    ) + [{"role": "user", "content": st.session_state["pre_user_input_content"]}]
    for ctx in [
        st.session_state["context_input" + current_chat],
        set_context_all[st.session_state["context_select" + current_chat]],
    ]:
        if ctx != "":
            history = [{"role": "system", "content": ctx}] + history
    return history


if st.session_state["user_input_content"] != "":
    if "r" in st.session_state:
        st.session_state.pop("r")
        st.session_state[current_chat + "report"] = ""
    st.session_state["pre_user_input_content"] = st.session_state["user_input_content"]
    st.session_state["user_input_content"] = ""
    # Temporary Exhibition
    show_each_message(
        st.session_state["pre_user_input_content"],
        "user",
        "tem",
        [area_user_svg.markdown, area_user_content.markdown],
    )
    # Model Input
    history_need_input = get_model_input()
    
    # Calling interface
    with st.spinner("🤔"):
        chat_data_json = [{"role": message["role"], "content": message["content"]} for message in history_need_input]
        messages = {"messages": chat_data_json}
        res = requests.post(text_conversation_url, data=json.dumps(messages))
        r = res.json().get("response")
        st.session_state["chat_of_r"] = current_chat
        st.session_state["r"] = r
        st.rerun()

if ("r" in st.session_state) and (current_chat == st.session_state["chat_of_r"]):
    if current_chat + "report" not in st.session_state:
        st.session_state[current_chat + "report"] = ""
        
    try:
        response = st.session_state["r"]
        content = response
        st.session_state[current_chat + "report"] += content
        show_each_message(
            st.session_state["pre_user_input_content"],
            "user",
            "tem",
            [area_user_svg.markdown, area_user_content.markdown],
        )
        show_each_message(
            st.session_state[current_chat + "report"],
            "assistant",
            "tem",
            [area_gpt_svg.markdown, area_gpt_content.markdown],
        )
    except Exception as e:
        area_error.error("An error occurred: " + str(e))
    else:
        # Save content
        st.session_state["history" + current_chat].append(
            {"role": "user", "content": st.session_state["pre_user_input_content"]}
        )
        st.session_state["history" + current_chat].append(
            {"role": "assistant", "content": st.session_state[current_chat + "report"]}
        )
        if audio_response:
            with st.spinner("Generating audio response..."):
                    final_data = {"text": f"{response}"}
                    audio_file = requests.post(convert_text_speech_url, data=final_data)
        write_data()
        
    if current_chat + "report" in st.session_state:
        st.session_state.pop(current_chat + "report")
    if "r" in st.session_state:
        st.session_state.pop("r")
        st.rerun()
