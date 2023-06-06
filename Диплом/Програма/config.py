import telebot
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

bot = telebot.TeleBot("5654011477:AAHvfdfMjUoJrMmxPGtE-RTlNyXlcLNd_jg")


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, name='pythonbot-9d555-default-rtdb', options={
    'databaseURL': 'https://pythonbot-9d555-default-rtdb.firebaseio.com/'
})
db = firebase_admin.db.reference('/', app=firebase_admin.get_app(name='pythonbot-9d555-default-rtdb'))