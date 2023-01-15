import json
import logging
import asyncio
from threading import Timer

from dggbot import DGGBot, Message, PrivateMessage
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

with open("config.json", "r") as config_json:
    config = json.loads(config_json.read())


cooldown = {"len": 30, "emotes": False}
emotes_bot = DGGBot(config["dgg_auth"], username="Emotes")
emotes_bot.auth = config["dgg_auth"]
emotes_bot.last_message = ""
emotes_bot.blacklist = config["blacklist"]
emotes_bot.admins = config["admins"]


def save_config():
    to_json = {
        "dgg_auth": emotes_bot.auth,
        "admins": emotes_bot.admins,
        "blacklist": emotes_bot.blacklist,
    }
    with open("config.json", "w") as config_json:
        config_json.write(json.dumps(to_json, indent=2))


def generate_link(msg_data: str, msg_author: str):
    def user_response(user):
        response = None
        api_link = f"https://tena.dev/api/users/{user}"
        if user_stats := requests.get(api_link).json():
            link = f"tena.dev/users/{user}"
            if user_stats["emotes"]:
                emotes = list(user_stats["emotes"].keys())[:3]
                response = f"Top 3 emotes: {' '.join(e for e in emotes)} {link}"
            else:
                response = f"Level {user_stats['level']} chatter: {link}"
        return response

    def emote_response(emote):
        response = None
        emotes_api_link = "https://tena.dev/api/emotes"
        emotes = requests.get(emotes_api_link).json().keys()
        if emote in emotes:
            link = f"tena.dev/emotes/{emote}"
            api_link = f"https://tena.dev/api/emotes/{emote}?amount=3"
            top3 = requests.get(api_link).json()
            response = (
                f"Top 3 {emote} posters: {' '.join([n for n in top3.keys()])} {link}"
            )
        return response

    response = None
    if msg_data.count(" ") >= 1:
        requested_link = [i for i in msg_data.split(" ") if i][1]
        if arg_is_emote := emote_response(requested_link):
            response = arg_is_emote
        elif arg_is_user := user_response(requested_link):
            response = arg_is_user
    if not response:
        author_in_db = user_response(msg_author)
        response = author_in_db if author_in_db else "No stats exist for your username"
    return response


def end_cooldown(key):
    cooldown[key] = False


def start_cooldown(key):
    cooldown[key] = Timer(cooldown["len"], end_cooldown, [key])
    cooldown[key].start()


def is_admin(msg: Message):
    return msg.nick in emotes_bot.admins


def not_blacklisted(msg: Message):
    return msg.nick not in emotes_bot.blacklist


@emotes_bot.command(["emotes", "emote"])
@emotes_bot.check(not_blacklisted)
def emotes_command(msg: Message):
    if is_admin(msg) or isinstance(msg, PrivateMessage) or not cooldown["emotes"]:
        reply = generate_link(msg.data, msg.nick)
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
            emotes_bot.last_message = reply = "Amount must be an integer"
            msg.reply(reply)
            return
        cooldown["len"] = length
        reply = f"Set cooldown to {length}s"
    else:
        reply = f"Cooldown is currently {cooldown['len']}s"
    emotes_bot.last_message = reply
    msg.reply(reply)


@emotes_bot.command(["blacklist"])
@emotes_bot.check(is_admin)
def blacklist_command(msg: Message):
    if msg.data.count(" ") >= 2:
        arguments = [i for i in msg.data.split(" ") if i]
        mode, user = arguments[1:3]
        if mode == "add" and user not in emotes_bot.blacklist:
            emotes_bot.blacklist.append(user)
            reply = f"Added {user} to blacklist"
        elif mode == "remove" and user in emotes_bot.blacklist:
            emotes_bot.blacklist.remove(user)
            reply = f"Removed {user} from blacklist"
        else:
            reply = "Invalid user"
    else:
        reply = f"Blacklisted users: {' '.join(emotes_bot.blacklist)}"
    save_config()
    emotes_bot.last_message = reply
    msg.reply(reply)


@emotes_bot.command(["admin"])
@emotes_bot.check(is_admin)
def admin_command(msg: Message):
    if msg.data.count(" ") >= 2:
        arguments = [i for i in msg.data.split(" ") if i]
        mode, user = arguments[1:3]
        if mode == "add" and user not in emotes_bot.admins:
            emotes_bot.admins.append(user)
            reply = f"Added {user} to admins"
        elif mode == "remove" and user in emotes_bot.admins:
            emotes_bot.admins.remove(user)
            reply = f"Removed {user} from admins"
        else:
            reply = "Invalid user"
    else:
        reply = f"Admin users: {' '.join(emotes_bot.blacklist)}"
    save_config()
    emotes_bot.last_message = reply
    msg.reply(reply)


if __name__ == "__main__":
    logger.info("Starting emotes bot")
    while True:
        emotes_bot.run()
