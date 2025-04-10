from beanie import Document, Indexed, init_beanie
from pydantic import Field
import typing as t
from datetime import datetime,timezone
from uuid import *
from beanie.operators import GTE,LTE,And

Roles=t.Literal['developer','user','assistant']

class Conversation(Document):
    role: Roles='developer'
    content: str
    user_id : int
    created_at : datetime=Field(default_factory=lambda :datetime.now(tz=timezone.utc))

    @staticmethod
    async def get_all_from_today():
        today_midnight=datetime.now(tz=timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
        end_of_day=datetime.now(tz=timezone.utc).replace(hour=23,minute=59,second=59,microsecond=0)
        condition=And(GTE(Conversation.created_at,today_midnight),
                      LTE(Conversation.created_at,end_of_day))
        previous_messages=await Conversation.find(condition).sort('-created_at').to_list()
        
        if previous_messages.__len__()>0:
            return list(map(lambda item: item.model_dump(include=['role','content']),previous_messages))
        return None
  

class UpdateConversation(Conversation):
    updated_at : datetime=Field(default_factory=lambda : datetime.now(tz=timezone.utc))



