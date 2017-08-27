import asyncio
import atexit

import telepot
from nltk.tokenize import TweetTokenizer
from telepot.aio.delegate import per_chat_id, create_open, pave_event_space
from telepot.aio.loop import MessageLoop

from PyAIML2.aiml import Kernel

# sys.path.insert(0, "../")

tt = TweetTokenizer()

# db = shelve.open("session.db", "c", writeback=True)
atexit.register(lambda: k.saveBrain('brain.sav'))
k = Kernel()  # sessionStore=db)
k.learn("startup.xml")
k.respond("load aiml b")


class MessageKiller(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageKiller, self).__init__(*args, **kwargs)

    async def on_chat_message(self, msg):
        print("Message text ", msg["text"])
        res = k.respond(msg["text"]).replace("  ", " ").replace("  ", " ")
        print("Response ", res)
        await self.sender.sendMessage(res)


TOKEN = "here_goes_bot_token"

bot = telepot.aio.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, MessageKiller, timeout=30),
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()
