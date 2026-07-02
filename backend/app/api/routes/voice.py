from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import openai, io
from config import settings

router = APIRouter()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = file.filename or "audio.webm"
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return {"text": result.text}

@router.post("/speak")
async def speak(payload: dict):
    text = payload.get("text", "")[:4000]
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    return StreamingResponse(io.BytesIO(response.content), media_type="audio/mpeg")
