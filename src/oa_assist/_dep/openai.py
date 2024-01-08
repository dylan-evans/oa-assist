
import asyncio
import aiohttp
from typing import Literal

# This is mostly for when the "beta" is removed. And not because they are a chore to find.
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads import ThreadMessage
from openai.types.beta.thread import Thread

from openai.types.beta import assistant
from openai.types.beta import threads
from openai.types.beta.threads.thread_message import Content
from openai.types.beta.threads.message_content_text import MessageContentText, Text

