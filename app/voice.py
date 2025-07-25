import asyncio
import logging

from app.rvc import AsyncRVCService
from app.tts import OpenAITTSService, EdgeTTSService


class ShirokoVoiceService:

    def __init__(self,tts_service : EdgeTTSService,rvc_service : AsyncRVCService,logger : logging.Logger):
        self.tts_service=tts_service
        self.rvc_service=rvc_service
        self.logger=logger

    async def talk(self,content : str):
        tts_audio = await self.tts_service.tts(content)

        async with AsyncRVCService(self.logger) as rvc:
            character_audio, mime_type = await rvc.convert_file(tts_audio)
            return character_audio


