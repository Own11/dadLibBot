import re
import edge_tts
from config import TTS_VOICE, TTS_RATE, TTS_VOLUME

def chunks(text, size=850):
    parts=[]
    while text:
        cut=min(size,len(text)); match=list(re.finditer(r"[.!?…](?:\s|$)",text[:cut]))
        if match: cut=match[-1].end()
        parts.append(text[:cut].strip()); text=text[cut:].strip()
    return [p for p in parts if p]

async def synthesize(text, path):
    await edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME).save(path)

