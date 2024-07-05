import whisper
import ssl
import torch


def get_text_from_speech(file):
    # Create an unverified context to avoid SSL issues
    # Check for GPU availability
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load a smaller model for faster inference
    model = whisper.load_model("base", device=device)

    # Load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(file)

    audio = whisper.pad_or_trim(audio)

    # Make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # Set decoding options for faster inference
    options = whisper.DecodingOptions(fp16=True, language="en", without_timestamps=True)

    # Decode the audio
    result = whisper.decode(model, mel, options)

    # Print the recognized text
    return result.text

