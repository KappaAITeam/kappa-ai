from openai import OpenAI
from dotenv import load_dotenv
from base64 import b64decode, b64encode
from pathlib import Path
import os

load_dotenv('.env')

openai = OpenAI()
chat_history = []
def get_audio_from_user(audio_file):
    """This get audio file from user"""
    with open(audio_file, 'rb') as audio:
        transcription = openai.audio.transcriptions.create(
            file=audio,
            model='whisper-1',
        )
    ai_output_audio, output_text = speak_back(transcription.text)
    chat_history.append({"role": "user", "content": ai_output_audio})
    return ai_output_audio, output_text

def speak_back(message):
    """This returns the audio generated from the model and the equivalent transcription
    """
    messages = [
        {"role": "user", "content": message}
    ]
    audio_path = Path("audio_output")
    response = openai.chat.completions.create(
        model='gpt-4o-audio-preview',
        modalities=["text", "audio"],
        audio={"voice": "onyx", "format": "wav"},
        messages=messages
    )
    audio_path = Path("./audio_output")
    audio_filename = "audio_response.wav"
    audio_stream = b64decode(response.choices[0].message.audio.data)
    with open(f"{audio_path}/{audio_filename}", "wb") as audio_file:
        audio_file.write(audio_stream)
    audio_transcription = response.choices[0].message.audio.transcript
    chat_history.append({"role": "assistant", "content": audio_transcription})
    return (os.path.join(audio_path, audio_filename), audio_transcription)
    

print(get_audio_from_user("testing_audo.m4a"))
    