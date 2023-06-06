import bot_module
import user_module
from config import bot, db
from telebot import types


# keyboard for the /start command
keyboard_auth = types.InlineKeyboardMarkup(row_width=1)
button_auth = types.InlineKeyboardButton(text="Авторизація", callback_data="auth")
keyboard_auth.add(button_auth)

@bot.message_handler(commands=['start'])
def start_message(message):
    user = user_module.get_user_from_db(message.from_user.id)

    if user is None:
        user_module.User(message.from_user.id).set_name(None, None)
        bot_module.start_message_handler(bot, message, keyboard_auth)
    else:
        bot_module.start_message_handler(bot, message, keyboard_auth)
        return


@bot.message_handler(func=lambda m: m.text == "Запитати номер телефону")
def ask_for_phone_number(message):
    user_module.request_phone_number(bot, message.chat.id)


@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_module.text_message_handler(bot, message)


@bot.message_handler(content_types=['contact'])
def handle_contact_messages(message):
    user_module.contact_handler(bot, message)


# Запуск бота
bot.polling(none_stop=True)