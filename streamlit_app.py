"""
FunctionWin - Streamlit Web App
Provides a web interface to interact with all Windows functions locally using natural language
Took idea from FunctionMac and created for Windows by Dhyey
"""

import streamlit as st
import json
import inspect
import typing
from datetime import datetime
from windows_functions import AVAILABLE_FUNCTIONS
from windows_ai_assistant import WindowsAIAssistant


def is_list_type(tp) -> bool:
    """Return True if tp is list or a generic alias of list (e.g. List[float])."""
    return tp is list or (hasattr(tp, '__origin__') and tp.__origin__ is list)

# Configure page
st.set_page_config(
    page_title="FunctionWin",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #0078d4;
        padding: 20px 0;
    }
    .function-card {
        background-color: #f3f2f1;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d2d0ce;
        margin: 10px 0;
    }
    .success-box {
        background-color: #dff6dd;
        border: 1px solid #107c10;
        color: #107c10;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #fde7e9;
        border: 1px solid #a80000;
        color: #a80000;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🪟 FunctionWin</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #605e5c;">Natural language control for Windows — runs 100% locally</p>', unsafe_allow_html=True)

# Function categories
FUNCTION_CATEGORIES = {
    "📋 Basic System": [
        "take_screenshot", "copy_to_clipboard", "get_clipboard_content", "paste_from_clipboard"
    ],
    "🎨 Theme & Appearance": [
        "change_theme", "get_current_theme", "set_wallpaper"
    ],
    "🔊 Audio Control": [
        "set_volume", "get_volume", "mute_volume", "unmute_volume"
    ],
    "💡 Display Control": [
        "set_brightness", "get_brightness"
    ],
    "🔕 Focus Assist": [
        "enable_do_not_disturb", "disable_do_not_disturb"
    ],
    "📂 File Operations": [
        "find_files", "open_file", "open_folder", "process_text_file"
    ],
    "📱 Applications": [
        "open_application", "quit_application", "list_running_applications", "get_installed_apps"
    ],
    "📊 System Information": [
        "get_battery_info", "get_system_info", "get_cpu_usage", "get_memory_usage", "get_disk_usage"
    ],
    "🖱️ GUI Automation": [
        "click_at_coordinates", "drag_mouse", "type_text", "send_keyboard_shortcut",
        "scroll_screen", "get_mouse_position", "get_screen_info"
    ],
    "📅 Productivity": [
        "create_reminder", "show_notification", "get_current_datetime"
    ],
    "🎵 Media Control": [
        "control_music"
    ],
    "🧮 Data & Analysis": [
        "calculate_expression", "analyze_data", "generate_qr_code"
    ],
    "🌐 Network": [
        "get_wifi_networks", "get_network_info"
    ],
    "🔧 Windows Extras": [
        "lock_screen", "empty_recycle_bin"
    ],
    "⚙️ Utilities": [
        "run_powershell", "run_shell_command", "execute_function"
    ]
}


def run_function(func_name: str, params: dict) -> dict:
    """Execute a function with given parameters and return result."""
    try:
        if func_name not in AVAILABLE_FUNCTIONS:
            return {"success": False, "error": f"Function '{func_name}' not found"}
        func = AVAILABLE_FUNCTIONS[func_name]
        result = func(**params)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                result = {"success": True, "message": result}
        return result
    except Exception as e:
        return {"success": False, "error": f"Error executing {func_name}: {str(e)}"}


def display_result(result: dict):
    """Display function execution result."""
    if result.get("success"):
        st.markdown('<div class="success-box">✅ Success!</div>', unsafe_allow_html=True)
        if "message" in result:
            st.info(f"**Message:** {result['message']}")
        result_data = {k: v for k, v in result.items() if k not in ['success', 'message']}
        if result_data:
            st.json(result_data)
    else:
        st.markdown('<div class="error-box">❌ Error occurred!</div>', unsafe_allow_html=True)
        st.error(f"**Error:** {result.get('error', 'Unknown error')}")


# Sidebar
st.sidebar.title("🚀 Interface Mode")
app_mode = st.sidebar.radio(
    "Choose how to interact:",
    ["🤖 AI Assistant", "🔧 Direct Functions"],
    help="AI Assistant uses natural language with Ollama. Direct Functions gives you immediate access to each function."
)

# Initialize AI Assistant
if app_mode == "🤖 AI Assistant":
    if 'ai_assistant' not in st.session_state:
        try:
            st.session_state.ai_assistant = WindowsAIAssistant()
            st.session_state.ai_ready = True
        except Exception as e:
            st.session_state.ai_ready = False
            st.session_state.ai_error = str(e)

# ─── AI ASSISTANT MODE ────────────────────────────────────────────────────────
if app_mode == "🤖 AI Assistant":
    st.header("🤖 AI Assistant Mode")

    if not st.session_state.get('ai_ready', False):
        st.error("❌ AI Assistant not available")
        st.error(f"Error: {st.session_state.get('ai_error', 'Unknown error')}")
        st.info("Make sure Ollama is running and FunctionGemma model is installed:")
        st.code("ollama pull functiongemma:270m")
    else:
        st.success("✅ AI Assistant ready!")
        st.markdown("Type your requests in natural language and I'll help you control your Windows PC.")

        with st.expander("💡 Example Queries"):
            st.markdown("""
            - "Take a screenshot and save it to desktop"
            - "Set volume to 50 percent"
            - "Switch to dark mode"
            - "Show me battery information"
            - "Find all PDF files in my Documents folder"
            - "Get my current system information"
            - "Set brightness to 70%"
            - "What's my CPU usage?"
            - "Lock the screen"
            - "Show me running applications"
            - "Play next track"
            """)

        st.markdown("---")

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        for chat_entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(chat_entry['query'])
            with st.chat_message("assistant"):
                if chat_entry['success']:
                    st.write(chat_entry['final_response'])
                    if chat_entry.get('function_calls'):
                        with st.expander(f"🔧 Function Details ({len(chat_entry['function_calls'])} called)"):
                            for fc in chat_entry['function_calls']:
                                if fc['success']:
                                    st.success(f"✅ {fc['function']}")
                                    if fc.get('arguments'):
                                        st.json(fc['arguments'])
                                else:
                                    st.error(f"❌ {fc['function']}: {fc.get('error', 'Unknown error')}")
                else:
                    st.error(f"❌ {chat_entry.get('error', 'Unknown error')}")

        user_query = st.chat_input("Ask me anything about your Windows PC...")

        if user_query:
            st.session_state.chat_history.append({
                'query': user_query,
                'success': False,
                'processing': True
            })
            with st.spinner("🤖 Processing your request..."):
                try:
                    result = st.session_state.ai_assistant.process_query(user_query)
                    st.session_state.chat_history[-1] = result
                except Exception as e:
                    st.session_state.chat_history[-1] = {
                        'query': user_query,
                        'error': str(e),
                        'success': False
                    }
            st.rerun()

# ─── DIRECT FUNCTIONS MODE ────────────────────────────────────────────────────
else:
    st.header("🔧 Direct Functions Mode")
    st.sidebar.title("🛠️ Function Categories")
    selected_category = st.sidebar.selectbox("Choose a category:", list(FUNCTION_CATEGORIES.keys()))

    category_functions = FUNCTION_CATEGORIES[selected_category]

    for func_name in category_functions:
        if func_name not in AVAILABLE_FUNCTIONS:
            continue
        with st.expander(f"🔧 {func_name.replace('_', ' ').title()}"):
            func = AVAILABLE_FUNCTIONS[func_name]

            if func.__doc__:
                st.markdown(f"**Description:** {func.__doc__.strip().splitlines()[0]}")

            sig = inspect.signature(func)
            params = {}

            for param_name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                default_value = param.default if param.default != inspect.Parameter.empty else None

                if param_type == int:
                    val = default_value if default_value is not None else 0
                    params[param_name] = st.number_input(f"{param_name}:", value=int(val), key=f"{func_name}_{param_name}")
                elif param_type == float:
                    val = default_value if default_value is not None else 0.0
                    params[param_name] = st.number_input(f"{param_name}:", value=float(val), key=f"{func_name}_{param_name}")
                elif param_type == bool:
                    val = default_value if default_value is not None else False
                    params[param_name] = st.checkbox(f"{param_name}:", value=bool(val), key=f"{func_name}_{param_name}")
                elif is_list_type(param_type) or "List" in str(param_type):
                    list_input = st.text_area(f"{param_name} (comma-separated):", key=f"{func_name}_{param_name}")
                    if list_input.strip():
                        try:
                            params[param_name] = [float(x.strip()) for x in list_input.split(',')]
                        except ValueError:
                            params[param_name] = [x.strip() for x in list_input.split(',')]
                    else:
                        params[param_name] = []
                else:
                    val = str(default_value) if default_value is not None else ""
                    params[param_name] = st.text_input(f"{param_name}:", value=val, key=f"{func_name}_{param_name}")

                # Remove params equal to their defaults (so optional args stay optional)
                if default_value is not None:
                    if params.get(param_name) in [0, 0.0, "", [], False] and str(default_value) in ["0", "0.0", "", "[]", "False"]:
                        params.pop(param_name, None)
                elif default_value is None:
                    # For params with a None default (e.g. Optional[int] = None),
                    # remove the param when the widget is at its zero-state so the
                    # function receives no argument (and uses its own None default)
                    # instead of an unintended 0 / "" value.
                    current_val = params.get(param_name)
                    if current_val in [0, 0.0, "", [], False, None]:
                        params.pop(param_name, None)

            if st.button(f"Execute {func_name}", key=f"execute_{func_name}"):
                with st.spinner("Executing..."):
                    result = run_function(func_name, params)
                    display_result(result)

# Footer
st.markdown("---")
st.markdown("**ℹ️ About:** FunctionWin — Windows port of [FunctionMac](https://github.com/krupagaliya/FunctionMac). Natural language + local AI to control your PC.")
st.markdown("**⚠️ Note:** Some functions require administrator privileges. Run as Administrator if a function fails.")

# Quick actions in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Quick Actions")

if st.sidebar.button("📸 Take Screenshot"):
    result = run_function("take_screenshot", {})
    if result.get("success"):
        st.sidebar.success("✅ Screenshot taken!")
    else:
        st.sidebar.error(f"❌ {result.get('error', 'Failed')}")

if st.sidebar.button("📊 System Info"):
    result = run_function("get_system_info", {})
    if result.get("success"):
        st.sidebar.success("✅ Done")
        st.sidebar.json({k: v for k, v in result.items() if k not in ['success']})
    else:
        st.sidebar.error(f"❌ {result.get('error')}")

if st.sidebar.button("🔋 Battery Info"):
    result = run_function("get_battery_info", {})
    if result.get("success"):
        st.sidebar.success(f"🔋 {result.get('percentage')}% — {result.get('status')}")
    else:
        st.sidebar.info(result.get('error', 'No battery found'))

if st.sidebar.button("🔊 Get Volume"):
    result = run_function("get_volume", {})
    if result.get("success"):
        st.sidebar.success(f"🔊 Volume: {result.get('volume')}%")
    else:
        st.sidebar.error(f"❌ {result.get('error')}")

if st.sidebar.button("🔒 Lock Screen"):
    result = run_function("lock_screen", {})
    if result.get("success"):
        st.sidebar.success("🔒 Screen locked")
    else:
        st.sidebar.error(f"❌ {result.get('error')}")
