from os import name

from telebot import types
from telebot.types import Message

from config import db


class User:
    def __init__(self, id):
        self.id = id
        self.first_name = None
        self.last_name = None
        self.role = None
        self.phone_number = None
        self.is_started = False
        # Load user data from Firebase
        user_ref = db.child("users").child(str(self.id))
        user_data = user_ref.get()
        if user_data is None:
            # Create a new user in the database
            data = {
                "id": self.id,
            }
            user_ref.set(data)
        else:
            self.first_name = user_data.get("first_name")
            self.last_name = user_data.get("last_name")
            self.role = user_data.get("role")
            self.phone_number = user_data.get("phone_number")
            self.is_started = user_data.get("is_started", False)
    def set_name(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.save()

    def set_role(self, role):
        self.role = role
        self.save()

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number
        self.save()

    def has_phone_number(self):
        return self.phone_number is not None

    def save(self):
        # Save user data to Firebase
        data = {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "phone_number": self.phone_number,
            "is_started": self.is_started
        }
        db.child("users").child(str(self.id)).set(data)


def get_user_from_db(id):
    user_ref = db.child("users").child(str(id))
    user_data = user_ref.get()
    if not user_data:
        return None
    user = User(id)
    user.first_name = user_data.get("first_name")
    user.last_name = user_data.get("last_name")
    user.role = user_data.get("role")
    user.phone_number = user_data.get("phone_number")
    return user


def show_menu(bot, chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Вибрати свою роль')
    btn2 = types.KeyboardButton('Кабінет')
    btn3 = types.KeyboardButton('Інше')
    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)
    bot.send_message(chat_id, "Оберіть пункт меню:", reply_markup=keyboard)


def process_contact(bot, message):
    user = get_user_from_db(message.chat.id)
    user.set_name(message.contact.first_name, message.contact.last_name)
    show_menu(bot, message.chat.id)


def create_school(bot, message):
    school_ref = db.child("schools").push({
        "director_id": message.chat.id,
        "country": None,
        "city": None,
        "school_number": None
    })
    school_id = school_ref["name"]
    bot.send_message(message.chat.id, f"Ваша школа створена. ID школи: {school_id}")

def process_role(bot, message):
    user = get_user_from_db(message.chat.id)
    user.set_role(message.text)
    if user.role == "Директор":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_create_school = types.KeyboardButton('Створити школу')
        keyboard.row(btn_create_school)
        bot.send_message(message.chat.id, "Виберіть дію:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, f"Ваша роль: {user.role}")



def contact_handler(bot, message):
    user = get_user_from_db(message.chat.id)
    if user is None:
        # Create a new user object and set the contact information
        user = User(message.chat.id)
        user.set_name(message.contact.first_name, message.contact.last_name)
        user.set_phone_number(message.contact.phone_number)
    else:
        # Update the existing user object with the contact information
        user.set_name(message.contact.first_name, message.contact.last_name)
        user.set_phone_number(message.contact.phone_number)
    show_menu(bot, message.chat.id)


def request_phone_number(bot, chat_id):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton(text="Відправити контакт", request_contact=True)
    keyboard.add(button)

    bot.send_message(chat_id, "Будь ласка, відправте свій контакт:", reply_markup=keyboard)


def text_message_handler(bot, message: Message):
    if message.text == "Вибрати свою роль":
        keyboard = types.InlineKeyboardMarkup()
        button_selected_role_director = types.InlineKeyboardButton(text="Директор", callback_data="role_director")
        button_selected_role_teacher = types.InlineKeyboardButton(text="Вчитель", callback_data="role_teacher")
        button_selected_role_student = types.InlineKeyboardButton(text="Учень", callback_data="role_student")
        keyboard.add(button_selected_role_director, button_selected_role_teacher, button_selected_role_student)
        bot.send_message(chat_id=message.chat.id, text="Зробіть свій вибір ролі", reply_markup=keyboard)

    elif message.text == "Кабінет":
        # Відправляємо повідомлення з іменем, прізвищем та телефоном користувача
        user = get_user_from_db(message.from_user.id)
        bot.send_message(chat_id=message.chat.id, text=f"Ім'я: {user.first_name}\nПрізвище: {user.last_name}\nТелефон: {user.phone_number}")
    elif message.text == "Інше":
        # Обробка інших текстових повідомлень
        bot.send_message(chat_id=message.chat.id, text="Оберіть пункт меню або надішліть свій контактний номер телефону.")
    if name == 'main':
        import telebot

        @bot.message_handler(func=lambda m: m.text == "Запитати номер телефону")
        def ask_for_phone_number(message):
            request_phone_number(bot, message.chat.id)

        @bot.message_handler(content_types=['text'])
        def handle_text_messages(message):
            text_message_handler(bot, message)

        @bot.message_handler(content_types=['contact'])
        def handle_contact_messages(message):
            contact_handler(bot, message)

        bot.polling(none_stop=True)

def update_school_data(bot, message):
    user = get_user_from_db(message.chat.id)
    school_ref = db.child("schools").order_by_child("director_id").equal_to(user.id).get()
    school_id = list(school_ref.val().keys())[0]
    school_data = school_ref.val()[school_id]

    if school_data.get("country") is None:
        school_data["country"] = message.text
        bot.send_message(message.chat.id, "Введіть місто:")
    elif school_data.get("city") is None:
        school_data["city"] = message.text
        bot.send_message(message.chat.id, "Введіть номер школи:")
    elif school_data.get("school_number") is None:
        school_data["school_number"] = message.text
        db.child("schools").child(school_id).update(school_data)
        bot.send_message(message.chat.id, "Дані збережені.")
