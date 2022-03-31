from schedule import every, repeat, run_pending
from dggbot import DGGBot, Message, PrivateMessage
from threading import Thread, Timer
from time import sleep
from os import getenv
import requests

emotes = [
    e["prefix"]
    for e in requests.get("https://cdn.destiny.gg/emotes/emotes.json").json()
]
cooldown = {"len": 15, "emotes": False}
emotes_bot = DGGBot(getenv("DGG_AUTH"), username="Emotes")
emotes_bot.last_message = ""


def generate_link(data: str):
    link = "tena.dev/emotes"
    if data.count(" ") >= 1:
        requested_link = [i for i in data.split(" ") if i][1]
        if requested_link in emotes:
            link += f"?emote={requested_link}"
        else:
            link += f"?user={requested_link}"
    return link


def end_cooldown(key):
    cooldown[key] = False


def start_cooldown(key):
    cooldown[key] = Timer(15, end_cooldown, [key])
    cooldown[key].start()


def check_emotes():
    while True:
        run_pending()
        sleep(60)


def is_admin(msg: Message):
    return msg.nick in ("RightToBearArmsLOL", "Cake", "tena_")


@repeat(every().day.at("00:00"))
def update_emotes():
    global emotes
    emote_json = requests.get("https://cdn.destiny.gg/emotes/emotes.json").json()
    emotes = [e["prefix"] for e in emote_json]
    print("Updated emotes")


@emotes_bot.command(["emotes"])
def emotes_command(msg: Message):
    if isinstance(msg, PrivateMessage) or not cooldown["emotes"]:
        reply = generate_link(msg.data)
        if not isinstance(msg, PrivateMessage):
            if emotes_bot.last_message == reply:
                reply += " ."
            emotes_bot.last_message = reply
            start_cooldown("emotes")
        msg.reply(reply)


@emotes_bot.command(["emotecd"])
@emotes_bot.check(is_admin)
def emotecd_command(msg: Message):
    if msg.data.count(" ") >= 1:
        length = [i for i in msg.data.split(" ") if i][1]
        try:
            length = abs(int(length))
        except ValueError:
            msg.reply("Amount must be an integer")
            return
        cooldown["len"] = length
        msg.reply(f"Set cooldown to {length}s")


if __name__ == "__main__":
    check_emotes_thread = Thread(target=check_emotes, daemon=True)
    check_emotes_thread.start()
    print("Connecting to DGG")
    while True:
        emotes_bot.run()
        sleep(5)
