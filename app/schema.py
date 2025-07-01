from beanie import Document, Indexed, init_beanie
from discord import DMChannel, GroupChannel, TextChannel,User,Member
from pydantic import BaseModel, ConfigDict, Field
import typing as t
from datetime import datetime,timezone
from uuid import *
from beanie.operators import GTE,LTE,And

from app.dto import ConversationChannelDTO, ConversationDTO
OriginType= t.Union[DMChannel, TextChannel, GroupChannel]

class CreatedAt(BaseModel):
    created_at : datetime=Field(default_factory=lambda :datetime.now(tz=timezone.utc))

class UpdateAt(BaseModel):
    updated_at : datetime=Field(default_factory=lambda : datetime.now(tz=timezone.utc))

class Origin(BaseModel):
    id: str | int
    name: str

    @staticmethod
    def _get_origin_channel_name(origin: OriginType):
        
        if isinstance(origin,DMChannel):
            return origin.me.name
        else:
            return origin.name
    
    @classmethod
    def create(cls,origin : OriginType):
        return Origin(id=origin.id,name=cls._get_origin_channel_name(origin))



class Conversation(CreatedAt):
    author  : t.Union[Origin,str]
    content: str





class ConversationChannel(Document,CreatedAt):
    #model_config = ConfigDict(arbitrary_types_allowed=True)

    conversations: t.List[Conversation]=[]
    origin : Origin

    # @staticmethod
    # async def get_all_from_today():
    #     today_midnight=datetime.now(tz=timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    #     end_of_day=datetime.now(tz=timezone.utc).replace(hour=23,minute=59,second=59,microsecond=0)
    #     condition=And(GTE(Conversation.conversations.created_at,today_midnight),
    #                   LTE(ChatMessage.created_at,end_of_day))
    #     previous_messages=await ChatMessage.find(condition).sort('-created_at').to_list()
        
    #     if previous_messages.__len__()>0:
    #         return list(map(lambda item: item.model_dump(include=['role','content']),previous_messages))
    #     return None

   


    @classmethod
    async def find_or_new(cls,origin_type : OriginType):
        existing_conversation=await ConversationChannel.find_one(ConversationChannel.origin.id==origin_type.id)
        if existing_conversation is not None:
            return existing_conversation
     
        new_conversation_channel=ConversationChannel(origin=Origin.create(origin_type),conversations=[])
        await new_conversation_channel.insert()
        return new_conversation_channel
    
    async def add_conversation(self,conversation: Conversation):
        self.conversations.append(conversation)
        await self.save()
        return self
    
    def serialize_object(self):
        new_conversation=ConversationChannelDTO(dm=False,conversations=[])
        if isinstance(self.origin,DMChannel):
            new_conversation.dm=True
            new_conversation.origin=self.origin.me.name
        else:
            new_conversation.origin=self.origin.name

        for conversation in self.conversations:
            author_name=conversation.author.name

            new_conversation.conversations.append(ConversationDTO(sender=author_name,content=conversation.content,timestamp=conversation.created_at.__str__()))
        return new_conversation.model_dump_json()


    

        


    







class UpdateConversation(ConversationChannel,UpdateAt):
    pass



