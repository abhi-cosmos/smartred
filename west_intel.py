from openai import OpenAI
import os
from typing_extensions import override
from openai import AssistantEventHandler
from fastapi import HTTPException

# First, we create an EventHandler class to define how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler):    
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
      
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
      
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

client = OpenAI()
api_key = None

if api_key is None:
    raise HTTPException(status_code=403, detail="API key not found")

os.environ["OPENAI_API_KEY"] = api_key

def chat_with_assistant(prompt, thread_id=None, assistant_id=None):
    try:
        if thread_id:
            thread = client.beta.threads.retrieve(thread_id)
            print('x')
        else:
            my_assistant = client.beta.assistants.create(
                name="west_intel",
                instructions="""You are a customer service representative as Westpac Bank of Australia.""",
                model="gpt-4o"
            )
            # Create a new thread
            thread = client.beta.threads.create()

        # Create a new message in the thread
        thread_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )

        if assistant_id:
            my_assistant = client.beta.assistants.retrieve(assistant_id)

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=my_assistant.id,
            instructions="""
                You are being called on a phone so tailor your responses to a phone call. 

                Guide the user step by step by helping them with each step of the problem. Take a break with each step.
                Take it slow and ensure a clear communication with the customer.

                Help the Westpac bank customer with their problem or point them to the right solution.
                
                Guide Westpac bank customers on how to use online banking features.

                Do not assume you know what they want and clarify with the user in a step-by-step manner.
            
                Tailor response so it is short, sweet, and helpful. Only one step at a time and confirming with user that they are ok to proceed.

                For fraudulent activity, redirect customer to the fraud department.
                For complex issues, redirect customer to the technical department.
                For general inquiries, please provide the information to the customer.
                """
        )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            formatted_messages = []
            for message in messages.data:
                for content_block in message.content:
                    if content_block.type == 'text':
                        text = content_block.text.value.replace("\n", " ").strip()
                        text = text.replace("*", "")
                        formatted_messages.append(text)
            return formatted_messages[0], thread.id, my_assistant.id
        else:
            print(run.status)
    except Exception as e:
        print(f"Error: {e}")


