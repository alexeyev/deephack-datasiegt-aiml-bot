"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
    Please note that this bot would not store sessions correctly;
    the state of the dialog is shared between ALL USERS (which is ugly)!

    You know, at hackathon you sometimes have to do stuf in a quick-and-dirty
    fashion.
"""

import atexit
import json
import os
import random
import shelve
from lru import LRU

import requests
from nltk.tokenize import TweetTokenizer

from PyAIML2.aiml import Kernel
from log_config import *

tt = TweetTokenizer()

db = shelve.open("session.db", "c", writeback=True)
atexit.register(lambda: k.saveBrain('brain.sav'))

k = Kernel(sessionStore=db)
k.learn("startup.xml")
k.respond("load aiml b")

lg.info(k.respond("Hello"))

lg.info("ALICE INITED!")

stoplist = open("stoplist.txt").read().strip().split("\n")


class ConvAISampleBot:
    def __init__(self):
        self.chat_id = None
        self.observation = None

    def observe(self, m):

        lg.info("Observe:")
        self.chat_id = m['message']['chat']['id']
        self.observation = m['message']['text']
        lg.info("\tStart new chat #%s" % self.chat_id)

        return self.observation

    def act(self):
        lg.info("Act:")
        if self.chat_id is None:
            lg.info("\tChat not started yet. Do not act.")
            return

        if self.observation is None:
            lg.info("\tNo new messages for chat #%s. Do not act." % self.chat_id)
            return

        message = {
            'chat_id': self.chat_id
        }

        # govnokod!
        should_finish = random.randint(0, 8) == 0 and not "/start" in self.observation

        data = {}

        if not should_finish:
            if len(self.observation) < 52:

                lg.info("Responding short " + self.observation)
                resp = k.respond(self.observation).replace("  ", " ")

                data = None

                for sw in stoplist:
                    if sw in resp:
                        data = {}
                        data["text"] = "/end"
                        data['evaluation'] = {
                            'quality': 0,
                            'breadth': 0,
                            'engagement': 0
                        }
                        break

                if not data:
                    data = {
                        'text': resp,
                        'evaluation': 0
                    }
            else:
                lg.info("Responding long " + self.observation)

                should_say_hello = random.randint(0, 2) == 1

                if should_say_hello:
                    data = {
                        'text': "hi",
                        'evaluation': 0
                    }
                else:
                    lg.debug(tt.tokenize(self.observation))
                    longest_word = sorted([(len(w), w) for w in tt.tokenize(self.observation)], key=lambda x: -x[0])[0][
                        1]
                    intro = ["Any idea what {0} is?", "whats {0}", "Do you know what {0} means?", "What is {0}",
                             "what is {0}", "I don't understand what's {0}", "I don't understand what {0} means", ]

                    # "Impressive", "'{0}' is something i dont know",
                    # "So what? skipped parts", "So what lol", "Whoa", "http://bit.ly/2uU6Mig",
                    # "Screw this, lets just chat."]
                    choose_intro = random.randint(0, len(intro) - 1)
                    data = {
                        'text': intro[choose_intro].format(longest_word) if "{" in intro[choose_intro] else intro[
                            choose_intro],
                        'evaluation': 0
                    }
            lg.info("Responding with " + str(data['text']))
        else:
            lg.info("\tDecide to finish chat %s" % self.chat_id)
            self.chat_id = None

            data['text'] = '/end'

            data['evaluation'] = {
                'quality': 0,
                'breadth': 0,
                'engagement': 0
            }

        message['text'] = json.dumps(data)
        return message


def main():
    BOT_ID = open("bot_id.conf").read().strip()

    if BOT_ID is None:
        raise Exception('You should enter your bot token/id!')

    BOT_URL = os.path.join('https://ipavlov.mipt.ru/nipsrouter/', BOT_ID)

    bot_map = LRU(100)

    while True:
        try:
            # lg.info("Get updates from server")
            res = requests.get(os.path.join(BOT_URL, 'getUpdates'))

            if res.status_code != 200:
                lg.info(res.text)
                res.raise_for_status()

            # lg.info("Got %s new messages" % len(res.json()))

            for m in res.json():

                lg.info("Process message %s" % m)

                if not m['message']['chat']['id'] in bot_map:
                    lg.info("chat id is Not in bot map")
                    bot = ConvAISampleBot()
                    bot_map[m['message']['chat']['id']] = bot
                else:
                    lg.info("chat id is found in bot map")
                    bot = bot_map[m['message']['chat']['id']]

                bot.observe(m)
                new_message = bot.act()

                if new_message is not None:

                    lg.info("Send response to server.")
                    res = requests.post(os.path.join(BOT_URL, 'sendMessage'),
                                        json=new_message,
                                        headers={'Content-Type': 'application/json'})
                    if res.status_code != 200:
                        lg.info(res.text)
                        res.raise_for_status()
                        # lg.info("Sleep for 1 sec. before new try")
        except Exception as e:
            lg.info("Exception: {}".format(e))


if __name__ == '__main__':
    main()
