import discord
import logging
from app.llm import LLMService
from app.rvc import *
from app.tts import *
from app.database import Database
from app.schema import *
from datetime import timedelta
from discord.ext import commands

from app.debug import bk,start_debug_session
class ShirokoClient(commands.Bot):
    
    def __init__(self, *, intents,logger : logging.Logger,llm : LLMService,db : Database,tts : OpenAITTSService, **options):
        super().__init__(intents=intents,command_prefix='$', **options)
        self.logger=logger
        self.llm=llm
        self.tts_service=tts
        self.db=db



    async def register_tree_commands(self):

        @self.tree.command(description='PING bot')
        async def ping(interaction : discord.Interaction):
            await interaction.response.send_message('PONG!')
        self.logger.info('Registered all commands')

        @self.tree.command(description='Clear all bot conversations you had with it ( ⚠️ DANGEROUS! ⚠️ )')
        async def clear(interaction : discord.Interaction):
            async with interaction.user.typing():
                Conversation.find(Conversation.user_id==interaction.user.id).delete_many()
                interaction.response.send_message('Conversations deleted')

        await self.tree.sync()



    async def on_ready(self):
        await self.register_tree_commands()
        await self.change_presence(status=discord.Status.do_not_disturb,activity=discord.Game('Exercising'))
        try:
            await self.db.init()
            self.logger.info('Conected to the database')
        except Exception as e:
            self.logger.critical(e)
            self.logger.critical(f'Failed to conect to the databases : {self.db.URL}')
            exit(1)
        self.logger.info('Shiroko Started')
        
    async def on_message(self,message : discord.Message):
        try:
            if message.author==self.user:
                new_conversation=Conversation(role='assistant',content=message.content,user_id=message.author.id)
                await new_conversation.create()
                return
            
            audio_file=None
            response=''
            async with message.channel.typing():
                previous_messages=await Conversation.get_all_from_today()
                self.logger.info(previous_messages)
                response=self.llm.prompt(message.content,previous_messages)
                tts_audio=self.tts_service.tts(response)
                async with AsyncRVCService(self.logger) as rvc:
                    await rvc.load_model()
                    character_audio, mime_type= await rvc.convert_file(tts_audio)
                    new_message=Conversation(role='user',content=message.content,user_id=message.author.id)
                    new_conversation=await new_message.create()
                    
                    audio_file=discord.File(fp=io.BytesIO(character_audio),filename=f'{new_conversation.id}.wav')
                    self.logger.debug(f'New conversation: {new_conversation.model_dump_json()}')
            await message.channel.send(response,file=audio_file,tts=True)
        except Exception as e:
            sent_message=await message.channel.send('```ansi\n\u001b[0;30m\u001b[0;47 An unexpected error occored please contact support```')
            await sent_message.add_reaction('😵')
            self.logger.error(e)
            return