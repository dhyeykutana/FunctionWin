"""
FunctionWin - Streamlit Web App
Provides a web interface to interact with all Windows functions locally using natural language
Took idea from FunctionMac and created for Windows by Dhyey
"""

import json
from typing import Dict, Any, List
from ollama import chat, ChatResponse
from windows_functions import AVAILABLE_FUNCTIONS


BLOCKED_AI_TOOLS = {'run_powershell', 'run_shell_command', 'execute_function'}


class WindowsAIAssistant:
    def __init__(self, model: str = 'functiongemma:270m'):
        """
        Initialize the AI Assistant

        Args:
            model: The Ollama model to use (default: functiongemma:270m)
        """
        self.model = model
        self.available_functions = AVAILABLE_FUNCTIONS
        print(f"Initialized Windows AI Assistant with model: {model}")
        print(f"Available functions: {len(self.available_functions)} functions loaded")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a natural language query and execute the appropriate Windows function

        Args:
            user_query: Natural language query from user

        Returns:
            Dictionary containing the result and execution details
        """
        try:
            print(f"\n🔍 Processing query: '{user_query}'")

            messages = [{'role': 'user', 'content': user_query}]
            available_tools = [
                func for name, func in self.available_functions.items()
                if name not in BLOCKED_AI_TOOLS
            ]

            print(f"📡 Sending query to {self.model}...")

            response: ChatResponse = chat(
                model=self.model,
                messages=messages,
                tools=available_tools
            )

            print(f"🤖 Model response: {response.message.content}")

            if response.message.tool_calls:
                results = []

                for tool_call in response.message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments

                    print(f"🔧 Calling function: {function_name} with args: {function_args}")

                    if function_name in self.available_functions:
                        try:
                            function_result = self.available_functions[function_name](**function_args)
                            result_data = json.loads(function_result) if isinstance(function_result, str) else function_result
                            results.append({
                                'function': function_name,
                                'arguments': function_args,
                                'result': result_data,
                                'success': True
                            })
                            print(f"✅ Function executed successfully")
                            print(f"📋 Result: {result_data}")
                        except Exception as e:
                            results.append({
                                'function': function_name,
                                'arguments': function_args,
                                'error': str(e),
                                'success': False
                            })
                            print(f"❌ Function execution failed: {str(e)}")
                    else:
                        results.append({
                            'function': function_name,
                            'arguments': function_args,
                            'error': f'Function {function_name} not found',
                            'success': False
                        })
                        print(f"❌ Function {function_name} not found")

                messages.append(response.message)
                for result in results:
                    content = json.dumps(result['result']) if result['success'] else f"Error: {result['error']}"
                    messages.append({'role': 'tool', 'content': content})

                final_response = chat(model=self.model, messages=messages)

                return {
                    'query': user_query,
                    'model_response': response.message.content,
                    'function_calls': results,
                    'final_response': final_response.message.content,
                    'success': True
                }
            else:
                return {
                    'query': user_query,
                    'model_response': response.message.content,
                    'function_calls': [],
                    'final_response': response.message.content,
                    'success': True
                }

        except Exception as e:
            error_msg = f"Failed to process query: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'query': user_query,
                'error': error_msg,
                'success': False
            }

    def interactive_mode(self):
        """Start interactive mode where user can continuously input queries."""
        print("\n🎉 Welcome to FunctionWin - Windows AI Assistant!")
        print("Type your requests in natural language and I'll help you control your PC.")
        print("\nExamples:")
        print("  - 'Take a screenshot and save it to desktop'")
        print("  - 'Set volume to 50 percent'")
        print("  - 'Switch to dark mode'")
        print("  - 'Show me CPU usage'")
        print("  - 'Lock the screen'")
        print("  - 'Find all PDF files in my Documents folder'")
        print("  - 'Show my battery status'")
        print("  - 'Play next track'")
        print("Type 'quit' or 'exit' to stop.\n")

        while True:
            try:
                user_input = input("🗣️  You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                result = self.process_query(user_input)

                if result['success']:
                    print(f"🤖 Assistant: {result['final_response']}\n")
                else:
                    print(f"❌ Error: {result['error']}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}\n")


def main():
    try:
        assistant = WindowsAIAssistant()
        assistant.interactive_mode()
    except Exception as e:
        print(f"❌ Failed to start assistant: {str(e)}")
        print("Make sure Ollama is running and the model is installed.")
        print("Run: ollama pull functiongemma:270m")


if __name__ == "__main__":
    main()
