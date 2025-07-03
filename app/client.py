import discord
import logging
from app.llm import LLMService
from app.rvc import *
from app.tts import *
from app.database import Database
from app.schema import *
from datetime import timedelta
from discord.ext import commands
import traceback
import uuid
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

        @self.tree.command(description="Make Shiroko join your voice channel")
        async def join(interaction: discord.Interaction):
                # Check if user is in a voice channel

            self.logger.info(f'Voice : {interaction.user.voice}')
            if interaction.user.voice is None or interaction.user.voice.channel is None:
                await interaction.response.send_message(
                    "❌ You must be in a voice channel first!",
                    ephemeral=True
                )
                return
            
                

            channel = interaction.user.voice.channel
            voice_client = interaction.guild.voice_client

            # Case 1: Bot already in user's channel
            if voice_client and voice_client.channel == channel:
                await interaction.response.send_message(
                    "🤖 I'm already in your voice channel!", 
                    ephemeral=True
                )
                return

            # Case 2: Bot in different channel
            if voice_client:
                await voice_client.move_to(channel)
                await interaction.response.send_message(f"🚚 Moved to **{channel.name}**!")
                return

            # Case 3: Bot not connected
            try:
                await channel.connect()
                await interaction.response.send_message(f"🎧 Joined **{channel.name}**!")
            except discord.ClientException as e:
                await interaction.response.send_message(
                    f"⚠️ Failed to join: {e}", 
                    #ephemeral=True
                )

        @self.tree.command(description="Make Shiroko leave the voice channel")
        async def leave(interaction: discord.Interaction):
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect()
                await interaction.response.send_message("Disconnected.")
            else:
                await interaction.response.send_message("I'm not in a voice channel.")



        await self.tree.sync()



    async def on_ready(self):
        await self.register_tree_commands()
        await self.change_presence(status=discord.Status.do_not_disturb,activity=discord.Game('Exercising'))
        try:
            await self.db.init()
            self.logger.info('Conected to the database')
            async with AsyncRVCService(self.logger) as rvc:
                    await rvc.load_model('shiroko')
                    self.logger.info('Loaded RVC model')
        except Exception as e:
            self.logger.critical(e)
            self.logger.critical(f'Failed to conect to the databases : {self.db.URL}')
            exit(1)
        self.logger.info('Shiroko Started')

    async def _talk(self,conversation_channel : ConversationChannel):
        response=self.llm.prompt(conversation_channel.model_dump_json())
        if response=='NULL':
            return False
        tts_audio=self.tts_service.tts(response)
        async with AsyncRVCService(self.logger) as rvc:
                    character_audio, mime_type= await rvc.convert_file(tts_audio)
        return (response, character_audio, mime_type)

    async def _handle_error(self,exception : Exception,message : discord.Message):
        sent_message=await message.reply('```ansi\n\u001b[0;30m\u001b[0;47 An unexpected error occured please contact support```')
        await sent_message.add_reaction('😵')
        self.logger.error(traceback.print_exception(exception))
    
    async def on_message(self,message : discord.Message):
        try:
            if message.author==self.user:
                return
            conversation_channel=await ConversationChannel.find_or_new(message.channel)
            new_user_conversation=Conversation.create(message)
            reference=message.reference
            
            if reference is not None:
                reference_message=reference.resolved
                reference_conversation= Conversation.create(reference_message)
                new_user_conversation.reference=reference_conversation
            await conversation_channel.add_conversation(new_user_conversation)
            audio_file=None
            chatbot_response=''
            chatbot_result= await self._talk(conversation_channel)
            if chatbot_result==False:
                return
            
            chatbot_response,character_audio,mime_type=chatbot_result
            async with message.channel.typing():
                new_conversation=Conversation(content=chatbot_response,author="chatbot")
                await conversation_channel.add_conversation(new_conversation)
                audio_file=discord.File(fp=io.BytesIO(character_audio),filename=f'{uuid.uuid4()}.wav')
                #self.logger.debug(f'New conversation: {new_conversation.model_dump_json()}')
            await message.reply(chatbot_response,file=audio_file)
        except Exception as e:
            await self._handle_error(e,message)
            return