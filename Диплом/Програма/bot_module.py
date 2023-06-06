# bot_module.py
import tempfile
import os
import telebot
import audio_module
import user_module
from config import bot, db
from telebot import types



# ініціалізація бібліотеки для конвертації тексту в мовлення
engine = audio_module.init_engine()

# задаємо голос
voice = audio_module.get_voice(engine)

# створення клавіатури з однією кнопкою
audio_button = telebot.types.InlineKeyboardButton("Відтворити", callback_data='convert_to_audio')
keyboard = telebot.types.InlineKeyboardMarkup().add(audio_button)

# команда "start"
def start_message_handler(bot, message, keyboard_auth, user=None):
    # check if the user exists in the database
    user_data = user_module.get_user_from_db(message.chat.id)
    print(type(user_data))  # add this line to check the type of user_data
    if user_data.is_started:
        bot.send_message(message.chat.id, "Ви вже авторизувалися.")
        user_module.show_menu(bot, message.chat.id)
        return
    else:
        # handle new user
        db.child("users").child(str(message.chat.id)).update({"is_started": True})

    # текст повідомлення при запуску бота
        start_text = 'Привіт! Я бот для інклюзивного класу. Я допоможу вам з отриманням інформації про заняття та багато чого іншого. Використовуйте доступні команди, щоб отримати більше інформації.'

    # задаємо голос
        voice = audio_module.get_voice(engine)

    # відправка повідомлення та клавіатури
        bot.send_message(message.chat.id, start_text, reply_markup=keyboard_auth)


# обробник натискання кнопки "Відтворити"
@bot.callback_query_handler(func=lambda call: call.data == 'convert_to_audio')
def convert_to_audio_callback_handler(call):
    try:
        # Перевірка, що текст повідомлення не є порожнім
        if call.message.text.strip() == "":
            raise ValueError("Message text is empty")

        # створюємо тимчасовий файл для збереження аудіо
        with tempfile.NamedTemporaryFile(suffix='.mp3') as tf:
            # перетворюємо текст у мовлення
            engine.save_to_file(call.message.text, tf.name)
            engine.runAndWait()

            # перевіряємо, що аудіо файл не є порожнім
            if os.path.getsize(tf.name) == 0:
                raise ValueError("Audio file is empty")

            # пересилаємо аудіо-повідомлення
            tf.seek(0)
            bot.send_voice(call.message.chat.id, voice=tf)

        # видаляємо тимчасовий файл
        os.remove(tf.name)
    except Exception as e:
        print(f"An error occurred while processing the message: {str(e)}")
        bot.send_message(call.message.chat.id, "На жаль, не вдалося обробити ваше повідомлення.")


# обробник натискання кнопки "Авторизація"
@bot.callback_query_handler(func=lambda call: call.data == 'auth')
def auth_callback_handler(call):
    if user_module.get_user_from_db(call.message.chat.id).phone_number is not None:
        bot.send_message(call.message.chat.id, "Ви вже авторизувалися.")
        user_module.show_menu(bot, call.message.chat.id)
        return
    else:
        bot.send_message(call.message.chat.id, "Для авторизації надішліть свій номер телефону.",
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        user_module.request_phone_number(bot, call.message.chat.id)

        # заборонити вводити текст, поки не буде надісланий контакт
        @bot.message_handler(content_types=['text'])
        def handle_text(message):
            bot.send_message(message.chat.id, "Будь ласка, надішліть свій контакт.")
            bot.register_next_step_handler(message, process_contact)
            if keyboard_auth:
                bot.remove_keyboard(message.chat.id)


# обробник натискання кнопки "Розклад занять"
@bot.callback_query_handler(func=lambda call: call.data == 'schedule')
def schedule_callback_handler(call):
    try:
        # отримання розкладу з бази даних Firebase
        schedule = db.child("schedule").get().val()
        # перевірка, що розклад не є порожнім
        if not schedule:
            raise ValueError("Schedule is empty")

        # формування тексту повідомлення з розкладом
        schedule_text = "Розклад занять:\n"
        for day, lessons in schedule.items():
            schedule_text += f"\n{day.capitalize()}:\n"
            for lesson, time in lessons.items():
                schedule_text += f"{lesson.capitalize()} - {time}\n"

        # відправка повідомлення з розкладом та клавіатурою
        bot.send_message(call.message.chat.id, schedule_text, reply_markup=keyboard)
    except Exception as e:
        print(f"An error occurred while processing the message: {str(e)}")
        bot.send_message(call.message.chat.id, "На жаль, не вдалося отримати розклад занять.")


# обробник натискання кнопки "Контакти"
@bot.callback_query_handler(func=lambda call: call.data == 'contacts')
def contacts_callback_handler(call):
    try:
        # отримання контактів з бази даних Firebase
        contacts = db.child("contacts").get().val()
        # перевірка, що контакти не є порожніми
        if not contacts:
            raise ValueError("Contacts are empty")

        # формування тексту повідомлення з контактами
        contacts_text = "Контакти:\n"
        for contact, phone in contacts.items():
            contacts_text += f"\n{contact.capitalize()}: {phone}"

        # відправка повідомлення з контактами та клавіатурою
        bot.send_message(call.message.chat.id, contacts_text, reply_markup=keyboard)
    except Exception as e:
        print(f"An error occurred while processing the message: {str(e)}")
        bot.send_message(call.message.chat.id, "На жаль, не вдалося отримати контакти.")

@bot.callback_query_handler(func=lambda call: call.data == 'role_director')
def callback_query_handler(call):
    if call.data == "role_director":
        user = user_module.get_user_from_db(call.from_user.id)
        user.set_role("Директор")

        # Відправляємо inline-клавіатуру з кнопкою "Створити школу"
        keyboard = types.InlineKeyboardMarkup()
        button_create_school = types.InlineKeyboardButton(text="Створити школу", callback_data="create_school")
        keyboard.add(button_create_school)
        bot.send_message(chat_id=call.from_user.id, text="Оберіть дію:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'create_school')
def callback_query_handler(call):
    if call.data == "create_school":
        # Check if there are any schools in the database
        check_school(call.message)
        # Add the new school to the user's list of schools in the database
        user_id = str(call.from_user.id)  # Convert user_id to string
        school_id = user_id  # Use the user's ID as the school ID

        schools = db.child("schools").child(school_id).get()
        last_school_id = list(schools.keys())[-1] if schools else None

        if last_school_id is not None:
            last_school = schools[last_school_id]
            new_school_id = last_school["school_id"] + 1  # This line is causing the error
        else:
            new_school_id = 1

        db.child("schools").push({
            "school_id": new_school_id,
            "country": None,
            "city": None,
            "number": None
        })

        db.child("users").child(user_id).child("schools").push(new_school_id)

        # Надсилаємо повідомлення з проханням заповнити поля
        bot.send_message(chat_id=call.from_user.id, text="Будь ласка, введіть країну, місто та номер школи:")

        # Встановлюємо хендлер на отримання повідомлення з назвою країни
        bot.register_next_step_handler(call.message, get_country)

def get_country(message):
    # Отримуємо id останньої створеної школи
    school_id = list(db.child("schools").get().keys())[-1]

    # Оновлюємо запис з введеними даними про країну
    db.child("schools").child(school_id).update({"country": message.text})

    # Надсилаємо повідомлення з проханням заповнити поле з містом
    bot.send_message(chat_id=message.chat.id, text="Введіть місто школи:")

    # Встановлюємо хендлер на отримання повідомлення з назвою міста
    bot.register_next_step_handler(message, get_city)

def get_number(message):
    # Get the school_id
    school_id = list(db.child("schools").get().keys())[-1]

    # Update the record with the entered number
    db.child("schools").child(school_id).update({"number": message.text})

    # Retrieve the school data
    school_data = db.child("schools").child(school_id).get()

    # Check if school_data exists and 'number' is not None
    if school_data and school_data.get('number') is not None:
        response = f"Нова школа:\nКраїна: {school_data['country']}\nМісто: {school_data['city']}\nНомер: {school_data['number']}"
        bot.send_message(chat_id=message.chat.id, text=response)
    else:
        bot.send_message(chat_id=message.chat.id, text="Сталася помилка. Будь ласка, спробуйте ще раз.")

def get_city(message):
    # Отримуємо id останньої створеної школи
    school_id = list(db.child("schools").get().keys())[-1]

    # Оновлюємо запис з введеними даними про місто
    db.child("schools").child(school_id).update({"city": message.text})

    # Надсилаємо повідомлення з проханням заповнити поле з номером школи
    bot.send_message(chat_id=message.chat.id, text="Введіть номер школи:")

    # Встановлюємо хендлер на отримання повідомлення з номером школи
    bot.register_next_step_handler(message, get_number)

def check_school(message):
    user_id = str(message.from_user.id)  # Convert user_id to string
    # Retrieve the user's data
    user_data = db.child("users").child(user_id).get()

    user_schools = user_data.get('schools', None)
    if user_schools:
        # If the user has one or more schools
        for school_id, school_data in user_schools.items():
            response = f"Школа:\nКраїна: {school_data['country']}\nМісто: {school_data['city']}\nНомер: {school_data['number']}"
            bot.send_message(chat_id=message.chat.id, text=response)

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Так", callback_data='create_school')
        btn2 = types.InlineKeyboardButton("Ні", callback_data='no_create_school')
        markup.add(btn1, btn2)
        bot.send_message(chat_id=message.chat.id, text="Ви хочете створити ще одну школу?", reply_markup=markup)
    else:
        # If the user does not have any school
        bot.send_message(chat_id=message.chat.id, text="Ви ще не маєте жодної школи.")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "create_school":
        # Handle school creation
        pass
    elif call.data == "no_create_school":
        # Handle user's decision to not create another school
        pass
