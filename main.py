import json
import logging
from typing import Union

from dggbot import DGGBot, Message
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

with open("config.json", "r") as config_json:
    cfg: dict[str, Union[str, list]] = json.loads(config_json.read())

emotes_bot = DGGBot(cfg["dgg_auth"])
emotes_bot._avoid_dupe = True


def save_cfg():
    with open("config.json", "w") as config_json:
        config_json.write(json.dumps(cfg, indent=2))


def generate_link(msg_data: str, msg_author: str):
    def user_response(user):
        response = None
        api_link = f"https://tena.dev/api/users/{user}"
        if user_stats := requests.get(api_link).json():
            link = f"tena.dev/users/{user}"
            if user_stats["emotes"]:
                emotes = sorted(
                    list(user_stats["emotes"].keys()),
                    key=lambda e: user_stats["emotes"][e],
                    reverse=True,
                )[:3]
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


def is_admin(msg: Message):
    return msg.nick in cfg["admins"]


def not_blacklisted(msg: Message):
    return msg.nick not in cfg["blacklist"]


@emotes_bot.command(["emotes", "emote"], cooldown=20)
@emotes_bot.check(not_blacklisted)
def emotes_command(msg: Message):
    reply = generate_link(msg.data, msg.nick)
    msg.reply(reply)


@emotes_bot.check(is_admin)
@emotes_bot.command()
def blacklist(msg: Message, mode: str, user: str, *_):
    if mode == "add" and user not in cfg["blacklist"]:
        cfg["blacklist"].append(user)
        reply = f"Added {user} to blacklist"
    elif mode == "remove" and user in cfg["blacklist"]:
        cfg["blacklist"].remove(user)
        reply = f"Removed {user} from blacklist"
    else:
        reply = "Invalid user"
    save_cfg()
    msg.reply(reply)


@emotes_bot.check(is_admin)
@emotes_bot.command()
def admin(msg: Message, mode: str, user: str, *_):
    if mode == "add" and user not in cfg["admins"]:
        cfg["admins"].append(user)
        reply = f"Added {user} to admins"
    elif mode == "remove" and user in cfg["admins"]:
        cfg["admins"].remove(user)
        reply = f"Removed {user} from admins"
    else:
        reply = "Invalid user"
    save_cfg()
    msg.reply(reply)


if __name__ == "__main__":
    logger.info("Starting emotes bot")
    while True:
        emotes_bot.run()
