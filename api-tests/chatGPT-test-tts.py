from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="gpt-4o-mini-tts",
  voice="alloy",
  input=" بەڵێ، دەتوانم زانیاریت پێ بدەم لەسەر سووریا. سووریا وڵاتێکە لە ڕۆژهەڵاتی ناوەڕاستدا، کە سنووری لەگەڵ تورکیا، عێراق، ئوردن، ئیسرائیل و لوبنان هەیە. گەورەترین شارەکانی دیمەشق (پایتەخت) و حەلەبە. وڵاتێکی فرە نەتەوە و ئایینە، بەڵام زۆرینەی دانیشتوانەکەی عەرەبن. لە ساڵی ٢٠١١ـەوە تووشی شەڕی ناوخۆ بووە.    ",
)
response.stream_to_file(speech_file_path)