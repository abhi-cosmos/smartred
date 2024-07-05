import whisper
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import wave
import queue
import threading
import sounddevice as sd
from scipy.io.wavfile import write
import wavio as wv
import threading
import time


from speechttext import get_text_from_speech
from texttspeech import text_to_speech
from west_intel import chat_with_assistant


app = FastAPI()

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Check for GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load a smaller model for faster inference
model = whisper.load_model("tiny", device=device)

@app.post("/speech-to-text/")
async def speech_to_text(audio: UploadFile = File(...)):
    audio_path = f"temp_{audio.filename}"
    with open(audio_path, "wb") as audio_file:
        audio_file.write(await audio.read())

    audio_data = whisper.load_audio(audio_path)
    audio_data = whisper.pad_or_trim(audio_data)

    mel = whisper.log_mel_spectrogram(audio_data).to(model.device)
    options = whisper.DecodingOptions(fp16=True, language="en", without_timestamps=True)

    result = whisper.decode(model, mel, options)
    os.remove(audio_path)

    return {"text": result.text}


@app.post("/chat/")
async def chat(text: str):
    pass


@app.post("/call")
@app.post("/call/{thread_id}/{assistant_id}")
async def call(thread_id: str = None, assistant_id: str = None):
    file = "recording1.wav"
    # Convert speech to text
    text = get_text_from_speech("recording1.wav")
    print(f"Recognized text: {text}")

    # Chat with the assistant
    response, thread_id, assistant_id = chat_with_assistant(text, thread_id=thread_id or None, assistant_id=assistant_id or None)
    print(f"Assistant response: {response}")
    print(f"Thread ID: {thread_id}")
    print(f"Assistant ID: {assistant_id}")

    # Convert text to speech
    audio_path = await text_to_speech(response)
    print(f"Generated audio file: {audio_path}")



    return FileResponse(path=audio_path, media_type="audio/mpeg")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(Path(__file__).parent / "templates" / "index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, media_type="text/html")

@app.get("/phone", response_class=HTMLResponse)
async def read_phone():
    with open(Path(__file__).parent / "templates" / "phone.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, media_type="text/html")


# Global variables to control recording
is_recording = False
recording_thread = None

# Function to handle the recording process
def record_audio(channels):
    global is_recording
    freq = 48000  # Sample rate
    duration = 10  # Record for 5 seconds (you can adjust this as needed)

    while is_recording:
        print("Recording started")
        recording = sd.rec(int(duration * freq), samplerate=freq, channels=channels)
        sd.wait()  # Wait until the recording is finished
        write("recording0.wav", freq, recording)
        wv.write("recording1.wav", recording, freq, sampwidth=2)
        print("Recording saved")
        time.sleep(1)  # Add a small delay to prevent overwhelming the system

@app.post("/start_recording")
def start_recording(background_tasks: BackgroundTasks):
    global is_recording, recording_thread
    if not is_recording:
        try:
            # Check the default input device's supported channels
            device_info = sd.query_devices(kind='input')
            max_channels = device_info['max_input_channels']
            channels = 2 if max_channels >= 2 else 1
            
            is_recording = True
            recording_thread = threading.Thread(target=record_audio, args=(channels,))
            recording_thread.start()
            return {"message": "Recording started"}
        except Exception as e:
            return {"message": f"Failed to start recording: {e}"}
    else:
        return {"message": "Recording is already in progress"}

@app.post("/stop_recording")
def stop_recording():
    global is_recording, recording_thread
    if is_recording:
        is_recording = False
        recording_thread.join()
        return {"message": "Recording stopped"}
    else:
        return {"message": "No recording in progress"}