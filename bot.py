from unittest.mock import call
import random
import telebot
import os
from dotenv import load_dotenv
from telebot import types
from flask import Flask, request
load_dotenv()   

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__) 
user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
   
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    markup.add("Menu")
    markup.add("Buyurtmalarim")

    bot.send_message(message.chat.id, "Xush kelibsiz \n Siz bu yeerda fast food buyurtma qilishingiz mumkin", reply_markup=markup)
menu ={
    'Burger': {"name": "Burger", "price": 25000, 'description': "Burgerning ichida go'sht, pishloq, pomidor, marul va boshqa ingredientlardan iborat."},
    'Pizza': {"name": "Pizza", "price": 40000, 'description': "Pizzaning ichida pomidor sousi, pishloq va turli xil qo'shimchalar bilan iborat."},
    'Hot Dog': {"name": "Hot Dog", "price": 15000, 'description': "Hot Dogning ichida kolbasa, ketchup, xantal va boshqa ingredientlardan iborat."},
    'Coca Cola': {"name": "Coca Cola", "price": 10000, 'description': "0,5 litr."},
}

@bot.message_handler(func=lambda message: message.text == "sovg'a")
def show_gift(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Sovg'a olish", callback_data="get_gift")
    markup.add(button) 
    bot.send_message(message.chat.id, "Sizga sovg'a beramiz!", reply_markup=markup)


cart= {}
@bot.message_handler(func=lambda message: message.text == "Menu")
def show_menu(message):

    markup = types.InlineKeyboardMarkup()

    for key, item in menu.items():
        button = types.InlineKeyboardButton(f'{item["name"]} - {item["price"]} sum', callback_data=f'add_{key}')
        markup.add(button)
    bot.send_message(message.chat.id, "Bizning menyuimiz:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart(call):
    user_id = call.from_user.id
    item_key = call.data.split('_')[1]
    
    if item_key in menu:
        if user_id not in cart:
            cart[user_id] = []

        cart[user_id].append(item_key)
        bot.send_message(call.message.chat.id,"Savatga qo'shildi!")

@bot.message_handler(func=lambda message: message.text == "Buyurtmalarim")
def show_cart(message):
    user_id = message.from_user.id
    
    if user_id in cart and cart[user_id]:
        order_summary = "Sizning buyurtmalaringiz:\n"
        total_price = 0

        for item_key in cart[user_id]:
            item = menu[item_key]
            order_summary += f"{item['name']} - {item['price']} sum\n"
            total_price += item['price']

        order_summary += f"\nJami: {total_price} sum"
                
        markup = types.InlineKeyboardMarkup()
        buton=types.InlineKeyboardButton("Buyurtmani tasdiqlash", callback_data="checkout")
        buton1=types.InlineKeyboardButton("Savatni tozalash", callback_data="clear")
        markup.add(buton, buton1)
        bot.send_message(message.chat.id, f"{order_summary}, \n\n buyurtmani tasdiqlash yoki savatni tozalash uchun quyidagi tugmalardan foydalaning:", reply_markup=markup)
            
    else:
        bot.send_message(message.chat.id, "Sizning savatingiz bo'sh.")

@bot.callback_query_handler(func=lambda call: call.data == 'clear')
def clear_cart(call):
    cart[call.from_user.id] = []
    bot.send_message(call.message.chat.id, "Savat tozalandi!")


@bot.callback_query_handler(func=lambda call: call.data == 'checkout')
def checkout(call):
    user_id = call.from_user.id
    user_state[user_id] = "waiting_address"

    bot.send_message(call.message.chat.id, "Iltimos, manzilingizni kiriting:")

@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "waiting_address")
def receive_address(message):
    user_id = message.from_user.id
    address = message.text

    user_state[user_id] = None
    items = cart.get(user_id, [])
    if not items:
        bot.send_message(message.chat.id, "Sizning savatingiz bo'sh.")
        return
    
    for item_key in items:
        item = menu[item_key]
        text = f"{item['name']} - {item['price']} sum\n"
        total = item['price']

    text += f"\nJami: {total} sum\nManzil: {address}\n\nBuyurtmangiz qabul qilindi! Tez orada yetkazib beramiz."

    markup = types.InlineKeyboardMarkup()
    buutton = types.InlineKeyboardButton("Tasdiqlash", callback_data="tasdiqlash")
    buutton1 = types.InlineKeyboardButton("Bekor qilish", callback_data="bekor qilish")
    markup.add(buutton, buutton1)

    bot.send_message(message.chat.id, text, reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data == "tasdiqlash")
def confirm_order(call):
    user_id = call.from_user.id
    cart[user_id] = []
    bot.send_message(call.message.chat.id, "Buyurtmangiz tasdiqlandi! Tez orada yetkazib beramiz.") 

    
@app.route('/webhook', methods=['POST'])
def webhook():  
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://food-shop-bot.onrender.com/webhook')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
