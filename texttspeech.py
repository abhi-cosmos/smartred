import os
from pathlib import Path
from openai import OpenAI
from fastapi import HTTPException

api_key = None

if api_key is None:
  raise HTTPException(status_code=403, detail="API key not found")

os.environ["OPENAI_API_KEY"] = api_key 


async def text_to_speech(text):
  client = OpenAI()
  
  speech_file_path = Path(__file__).parent / "speech.mp3"
  response = client.audio.speech.create(
    model="tts-1-hd",
    voice="alloy",
    input=text
  )

  response.stream_to_file(speech_file_path)

  return speech_file_path