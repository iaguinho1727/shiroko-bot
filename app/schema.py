from beanie import Document, Indexed, PydanticObjectId, init_beanie
from discord import DMChannel, GroupChannel, Message, TextChannel,User,Member,VoiceChannel
from pydantic import BaseModel, ConfigDict, Field
import typing as t
from datetime import datetime,timezone
from uuid import *
from beanie.operators import GTE,LTE,And
from enum import Enum
ChannelTypes= t.Union[DMChannel, TextChannel, GroupChannel,VoiceChannel]

class CreatedAt(BaseModel):
    created_at : datetime=Field(default_factory=lambda :datetime.now(tz=timezone.utc))

class UpdateAt(BaseModel):
    updated_at : datetime=Field(default_factory=lambda : datetime.now(tz=timezone.utc))


class OriginType(Enum):
    TEXT_CHANNEL='text_channel'
    GROUP_CHANNEL='group_channel'
    DM_CHANNEL='dm'
    VOICE_CHANNEL='voice_channel'
    OTHER='other'

    @staticmethod
    def get_origin_type_from_channel(channel: Message.channel):
        if isinstance(channel,TextChannel):
            return OriginType.TEXT_CHANNEL
        elif isinstance(channel,GroupChannel):
            return OriginType.GROUP_CHANNEL
        elif isinstance(channel,DMChannel):
            return OriginType.DM_CHANNEL
        elif isinstance(channel,VoiceChannel):
            return OriginType.VOICE_CHANNEL
        return OriginType.OTHER


class Author(BaseModel):
    id: int
    name: str

class Origin(BaseModel):
    id : int
    name: str
    type: OriginType=OriginType.OTHER
    server_name: t.Optional[str]=None

    @staticmethod
    def _get_origin_channel_name(origin: ChannelTypes):
        
        if isinstance(origin,DMChannel):
            return origin.me.name
        else:
            return origin.name
        

    
    @classmethod
    def create(cls,origin : ChannelTypes | str):
        origin_name=origin
        type=OriginType.get_origin_type_from_channel(origin)

        server_name=None
        if isinstance(origin,ChannelTypes):
            origin_name=cls._get_origin_channel_name(origin)
        if type==OriginType.TEXT_CHANNEL:
            server_name=origin.guild.name
        return Origin(id=origin.id,name=origin_name,type=type,server_name=server_name)



class Conversation(Document,CreatedAt):
    id : int
    author  : t.Union[Author,str]
    content: str
    reference: t.Optional["Conversation"]=None
    mentions : t.Optional[t.List[Author]]=[] 
    origin: Origin

    @classmethod
    async def find_or_new(cls,message : Message):
        existing_conversation=await Conversation.find_one(Conversation.origin.id==message.channel.id)
        if existing_conversation is not None:
            return existing_conversation
     
        new_conversation_channel=Conversation(message)
        await new_conversation_channel.insert()
        return new_conversation_channel

    @staticmethod
    async def create(message : Message,save=True):
        mentions=[  ]

        new_author=Author(id=message.author.id,name=message.author.name)
        for mention in message.mentions:
            mentions.append(Author(id=mention.id,name=mention.name))
        new_origin=Origin.create(message.channel)
        new_conversation=Conversation(id=message.id,author=new_author,content=message.content,mentions=mentions,origin=new_origin)
        if message.reference is not None and message.reference.resolved is not None:
            reference=message.reference.resolved
            reference_conversation= await Conversation.create(reference,False)
            new_conversation.reference=reference_conversation
        if save:
            await new_conversation.save()
        return new_conversation
    
    @staticmethod
    async def create_chatbot_conversation(sent_message : Message,content: str):
        new_origin=Origin.create(sent_message.channel)
        new_conversation=Conversation(id=sent_message.id,content=content,author="chatbot",origin=new_origin)
        if sent_message.reference is not None:
            reference=sent_message.reference.resolved
            reference_conversation= await Conversation.create(reference,False)
            new_conversation.reference=reference_conversation
            

        await new_conversation.save()
        return new_conversation

    
    
    
    









