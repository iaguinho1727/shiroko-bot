from PyPDF2 import PdfReader
from discord import Attachment, Message

from app.tts import OpenAITTSService
from app.voice import ShirokoVoiceService


class ShirokoPDFReader:


    def __init__(self, shiroko_voice : ShirokoVoiceService):
        self.shiroko_voice_service=shiroko_voice

    @staticmethod
    def is_pdf(attachment : Attachment):
        return attachment.content_type=='application/pdf'

    @classmethod
    def filter_pdf_attachments(cls,attachments : list[Attachment]):
        return list(filter(lambda  item: cls.is_pdf(item),attachments ))

    @classmethod
    def filter_messages_with_attachments(cls,messages : list[Message]):
        return list(filter(lambda  item: item.attachments.__len__()>0,messages))

    @classmethod
    def get_attachments_from_messages(cls,messages : list[Message]):
        attachments=[]
        for message in messages:
            for attachment in message.attachments:
                attachments.append(attachment)

        return attachments


    async def single_pdf_to_audio(self, attachment : Attachment):
        if not(self.is_pdf(attachment)):
            raise RuntimeError('Attachment must be a pdf file')
        file = await attachment.to_file()
        reader = PdfReader(file.fp)
        final_text=""
        for page in reader.pages:
            text=page.extract_text()
            if text.__len__()==0:
                continue
            final_text+=text
        final_audio= await self.shiroko_voice_service.talk(final_text)
        return (file.filename,final_audio)

    async def pdfs_to_audio(self, attachments : list[Attachment]):
        audios=[]
        for attachment in attachments:
            if not(self.is_pdf(attachment)):
                continue
            result=await self.single_pdf_to_audio(attachment)
            audios.append(result)

        return audios


