from aiogram import executor

from create import disp

from handlers import start, registration, profile, weather

start.reg_start(disp)
registration.reg_registration(disp)
profile.reg_profile(disp)
weather.reg_weather(disp)
executor.start_polling(disp, skip_updates=True) 
