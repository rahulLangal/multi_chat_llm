#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
import streamlit as st
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, OpenAIError

# --- Page Config ---
st.set_page_config(
    page_title="Your Own AI Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stChatMessage {
        background-color: transparent;
    }
    .stChatInput {
        bottom: 20px;
    }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.expander("Configuration", expanded=True):
    st.header("Configuration")

    api_key = st.text_input("OpenRouter API Key", type="password",
                            help="Get your api key from https://openrouter.ai")

    st.divider()

    selected_model = st.selectbox("Choose Model",
        options=[
            "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            "x-ai/grok-4.1-fast:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "alibaba/tongyi-deepresearch-30b-a3b:free",
            "openai/gpt-3.5-turbo", # Swapped gpt-oss for a known working standard
        ], index=0)

    st.divider()

    system_context = st.text_area("System Context (Persona)",
        value="You are a helpful assistant.",
        height=100,
        help="Give some background information about yourself")

    st.divider()

    # FIX: Everything below is now indented to stay INSIDE the sidebar
    col1, col2 = st.columns(2)
    with col1:
        max_tokens = st.slider(
            "Max Tokens",
            min_value=1,
            max_value=8192,
            value=1024,
            step=256
        )
    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Main App Logic ---
st.title("Your Own AI Assistant")
st.caption(f"Current model: `{selected_model}`")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Input
if prompt := st.chat_input("What's on your mind?"):

    if not api_key:
        st.error("Please enter your OpenRouter API Key in the sidebar to continue.")
        st.stop()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://streamlit.io/",
                    "X-Title": "Streamlit App",
                }
            )

            messages_payload = [{"role": "system", "content": system_context}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            stream = client.chat.completions.create(
                model=selected_model,
                messages=messages_payload,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        # FIX: Specific Exceptions MUST come before the general Exception
        except AuthenticationError:
            st.error("🔒 **Authentication Failed:** Your API Key is invalid.")
        
        except RateLimitError:
            st.error("⏳ **Rate Limit Reached:** You are sending requests too fast.")
        
        except APIConnectionError:
            st.error("📡 **Connection Error:** Check your internet.")
        
        except OpenAIError as e:
            st.error(f"🤖 **API Error:** {e}")
            
        except Exception as e:
            st.error(f"⚠️ **Unexpected Error:** {e}")
