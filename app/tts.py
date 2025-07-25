import logging
import os
import re
import typing as t
import uuid

import discord
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from math import ceil
from pathlib import Path
from enum import Enum

import httpx
import edge_tts
from dotenv import load_dotenv

import tempfile
import abc
import io
from app.llm import ChatGPT
from logging import Logger
from edge_tts import Communicate
from app.rvc import AsyncRVCService
from pydub import AudioSegment

OpenAITTSModels=t.Literal['tts-1','tts-1-hd']   
OpenAITTSVoices=t.Literal['alloy', 'ash', 'coral', 'echo', 'fable', 'onyx', 'nova', 'sage', 'shimmer']
AudioFormat=t.Literal['mp3', 'opus', 'aac', 'wav']



class TTSWords:
    _CHARACTER_LIMIT=4096
    SPLIT_PATTERN=r'([^\.!\?;]{1,4096}[\.!\?;]{1,10})'

    def __init__(self,content : str):
        self._split_text=re.split(self.SPLIT_PATTERN, content.strip())
        self._text=content.strip()

    def get_split_text(self):
        return list(filter(lambda item : item.strip().__len__()>1,self._split_text))


    def change_character_limit(self,new_character_limit):
        self._CHARACTER_LIMIT=new_character_limit

    def join_phrases(self,first : str,second :str):
        if first.__len__()+second.__len__()<=self._CHARACTER_LIMIT:
            return first+second
        return first


class EdgeTTSService:

    def __init__(self):
        pass


    async def tts(self,content : str):
        result=edge_tts.Communicate(content)
        voice=bytes()
        async for chunk in result.stream():
            if chunk.get('data') is None:
                continue
            voice+=chunk['data']

        return voice    



class OpenAITTSService(ChatGPT):


        
  
    
    
    
    def __init__(self,voice: OpenAITTSVoices='nova', model : OpenAITTSModels='tts-1',STREAM_CHUNK: t.Optional[int]=1024,speed : t.Optional[int]=1,format: t.Optional[AudioFormat]='wav',logger =Logger):
        self.voice=voice
        if not(self._voice_exists()):
            raise RuntimeError(f'The specific voice {self.voice} does not exists')
        
        super().__init__(model=model,logger=logger)
            
        self.STREAM_CHUNK=STREAM_CHUNK
        self.speed=speed
        self.audio_format=format
        self.logger=logger
        
    def get_mime_type(self):
        mime_type_dict={
            "mp3": 'mpeg',
            'opus': 'ogg'
        }
        return f'audio/{self.audio_format}' if self.audio_format not in mime_type_dict.keys() else f'audio/{mime_type_dict.get(self.audio_format)}'
        
    def get_audio_format(self):
        return self.audio_format

    def _voice_exists(self):
        return self.voice in t.get_args(OpenAITTSVoices)

   
    

    
    
 
    
    def tts(self,content : str):
        tts_words=TTSWords(content)
        final_audio=AudioSegment.empty()
        with tempfile.NamedTemporaryFile(suffix=f'.{self.audio_format}') as final_audio_file:
            phrases=tts_words.get_split_text()
            for phrase in phrases:
                with self.client.audio.speech.with_streaming_response.create(model=self.model,voice=self.voice,input=phrase,speed=self.speed,response_format=self.audio_format) as response:
                    response.stream_to_file(final_audio_file.name,chunk_size=self.STREAM_CHUNK)
                final_audio_file.flush()


                final_audio+=AudioSegment.from_file_using_temporary_files(final_audio_file,self.audio_format)
        final_audio.export('static/teste.wav',self.audio_format)
        return final_audio
    








