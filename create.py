from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import token

storage = MemoryStorage()
bot = Bot(token=token, parse_mode='html')
disp = Dispatcher(bot, storage=storage)
