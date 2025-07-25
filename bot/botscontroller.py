import telebot
from telebot import types

class BotsController:
    def __init__(self):
        pass
    
    def GenerateButtonArrays(self, textList = [], withOustStart = False):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        for text in textList:
            markup.add(types.KeyboardButton(text))
        
        if (not withOustStart):
            markup.add(types.KeyboardButton("/start"))
            
        return markup