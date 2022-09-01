from telebot import TeleBot
import os
from config import TOKEN, VIDEOS_DIR, AUDIOS_DIR
from keyboard import choose_video_or_audio, choose_resolution, language_buttons
from db import PgConn
import json

from yt_downloader import downloader_video, downloader_audio, available_resolutions

bot = TeleBot(TOKEN)

with open("lang.json", "r", encoding="utf-8") as lang_file:
    lang = json.load(lang_file)

if not os.path.isdir(VIDEOS_DIR):
    os.makedirs(VIDEOS_DIR)
if not os.path.isdir(AUDIOS_DIR):
    os.makedirs(AUDIOS_DIR)


@bot.message_handler(commands=['start'])
def start(message):
    try:
        db_conn = PgConn()
        db_conn.create_tables()
        db_conn.add_user(message.chat.id, message.from_user.username)
        choose_lang(message)

    except Exception as e:
        print(e)


@bot.message_handler(content_types=['text'])
def mess(message):
    db_conn = PgConn()
    try:
        get_message_bot = message.text.strip()

        if 'https' in get_message_bot:
            if 'https://www.youtube.com/watch' in get_message_bot:
                db_conn.set_last_link(message.chat.id, get_message_bot)
                bot.send_message(message.chat.id, lang[db_conn.get_user_lang(message.chat.id)]['Please_choose'],
                                 reply_markup=choose_video_or_audio(message))
            else:
                bot.reply_to(message, lang[db_conn.get_user_lang(message.chat.id)]['Not_yt_link'])

        elif get_message_bot in ["🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English"]:
            if get_message_bot == "🇺🇿 O'zbekcha":
                db_conn.set_user_lang("uz", message.from_user.id)

            elif get_message_bot == "🇷🇺 Русский":
                db_conn.set_user_lang("ru", message.from_user.id)

            elif get_message_bot == "🇬🇧 English":
                db_conn.set_user_lang("en", message.from_user.id)

            bot.send_message(message.chat.id, lang[db_conn.get_user_lang(message.chat.id)]['Send_me_link'],
                             reply_markup=None)

    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    try:
        db_conn = PgConn()
        some_data = db_conn.get_user_info(call.message.chat.id)
        resolutions = available_resolutions(some_data[2])

        if call.data == "video":
            bot.edit_message_text(lang[db_conn.get_user_lang(call.message.chat.id)]['Choose_resolution'],
                                  call.message.chat.id, call.message.message_id,
                                  reply_markup=choose_resolution(call.message, some_data[2]))
            db_conn.set_content_type(call.message.chat.id, 'video')

        elif call.data == "audio":
            wait_mess = bot.edit_message_text(f"{lang[db_conn.get_user_lang(call.message.chat.id)]['Wait']}...",
                                              call.message.chat.id, call.message.message_id)
            db_conn.set_content_type(call.message.chat.id, 'audio')
            audio_path, audio_title = downloader_audio(some_data[2])
            bot.send_audio(call.message.chat.id, open(audio_path, 'rb'), caption=audio_title)
            bot.delete_message(call.message.chat.id, wait_mess.message_id)
            os.remove(audio_path)

        elif call.data in resolutions:
            wait_mess = bot.edit_message_text(f"{lang[db_conn.get_user_lang(call.message.chat.id)]['Wait']}...",
                                              call.message.chat.id, call.message.message_id)
            video_path, video_title = downloader_video(some_data[2], quality=call.data)
            bot.send_document(call.message.chat.id, open(video_path, 'rb'), caption=video_title)
            bot.delete_message(call.message.chat.id, wait_mess.message_id)
            os.remove(video_path)

    except Exception as e:
        print(e)


def choose_lang(message):
    try:
        db_conn = PgConn()
        bot.send_message(message.chat.id, f"🇺🇿 Assalomu alaykum, {message.from_user.username}. Tilni tanlang!\n\n"
                                          f"🇷🇺 Здравствуйте, {message.from_user.username}. Выберите язык!\n\n"
                                          f"🇬🇧 Hello, {message.from_user.username}. Choose language!\n\n",
                         reply_markup=language_buttons(message))
        # if get_user_temp(message) == 'no':
        #     bot.send_message(message.from_user.id, f"{emoji.emojize(':Uzbekistan:')} Tilni tanlang!\n\n"
        #                                            f"{emoji.emojize(':Russia:')} Выберите язык!\n\n"
        #                                            f"{emoji.emojize(':United_Kingdom:')} Choose language!\n\n",
        #                      reply_markup=language_buttons(message, get_user_temp(message)))
        # elif get_user_temp(message) == 'some_lang':
        #     bot.register_next_step_handler(message, menu)
        #     bot.send_message(message.from_user.id, f"{lang[get_user_lang(message)]['Choose_lang']}",
        #                      reply_markup=language_buttons(message, get_user_temp(message)))
        # else:
        #     bot.send_message(message.from_user.id, f"{lang[get_user_lang(message)]['Choose_lang']}",
        #                      reply_markup=language_buttons(message, get_user_temp(message)))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    bot.polling(none_stop=True)
