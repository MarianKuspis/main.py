import os

folder = "./temp"
if not os.path.exists(folder):
    os.makedirs(folder)

import tempfile
tempfile.tempdir = './temp'
from gtts import gTTS

from config import bot


def init_engine():
    # ініціалізація бібліотеки для конвертації тексту в мовлення
    engine = gTTS(text="В рот шатав")
    return engine


def get_voice(engine):
    # задаємо голос
    return engine

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
            tts = gTTS(text=call.message.text, lang='uk')
            tts.save(tf.name)

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
