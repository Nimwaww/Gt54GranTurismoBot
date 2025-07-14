import os
from dotenv import load_dotenv
import telebot
from telebot import types
from functools import partial
import json
import shutil
from uuid import uuid4


load_dotenv('token.env')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    print("Ошибка: токен не загружен. Проверьте файл token.env.")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Данные товаров
ducks = {
    1: {'name': 'Утка-пилот ✈️', 'description': 'Стильная утка в лётных очках', 'price': '799 руб', 'photo': 'duck1.jpg'},
    2: {'name': 'Утка-полицейский 👮', 'description': 'Настоящий страж порядка для вашего авто', 'price': '899 руб', 'photo': 'duck2.jpg'}
}

user_states = {}


folders = os.getenv("img").split(",") 

for folder_name in folders:
    try:
        os.mkdir(folder_name)
        print(f"Папка '{folder_name}' создана.")
    except FileExistsError:
        print(f"Папка '{folder_name}' найдена.")
    except Exception as e:
        print(f"Ошибка при создании папки '{folder_name}': {e}")

def start_2(message, model_name=None):
    if message.from_user.id == 1965630668 or message.from_user.id == 1109848616:
        if not model_name:
            bot.send_message(message.chat.id, "Ошибка: не указано название категории")
            return

        filename = f"database/{model_name}.txt"
        
        try:
            with open(filename, "a", encoding="utf-8") as file:
                file.write(f"{message.text}\n")
            
            bot.send_message(message.chat.id, f"✅ Бренд добавлен в категорию {model_name}")
        
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при записи: {str(e)}")
    else:
        bot.send_message(message.chat.id, "⛔ У вас нет прав администратора!")

back = types.InlineKeyboardMarkup()
back.add(types.InlineKeyboardButton("🔙 Назад", callback_data='back1'))

back2 = types.InlineKeyboardMarkup()
back2.add(types.InlineKeyboardButton("🔙 Назад", callback_data='back2'))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Сброс состояния пользователя при старте
    if message.chat.id in user_states:
        del user_states[message.chat.id]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Ассортимент 🛒", callback_data='shop'),
        types.InlineKeyboardButton("Тех Поддержка 🎙", callback_data='support'),
        types.InlineKeyboardButton("WhatsApp 📗", url="https://wa.me/+79250648771")
    )
    
    text = """
*🚗 Добро пожаловать в GRAN TURISMO! 🏁*

*Ваш универсальный магазин премиум-товаров для автомобилей!*

✨ *Почему выбирают нас?*
✔️ *Широкий ассортимент*: У нас вы найдете все, что нужно для вашего автомобиля — от запчастей и масел до премиальных аксессуаров чтобы выделиться из серой массы.  
✔️ *Экспертная поддержка 24/7*: Наша команда профессионалов всегда готова помочь вам с выбором и ответить на любые вопросы.  
✔️ *Честные цены*: Мы предлагаем конкурентоспособные цены и прозрачность без скрытых наценок, чтобы вы могли наслаждаться качеством без лишних затрат.  
✔️ *Гарантия качества*: Мы тщательно отбираем товары, чтобы гарантировать их надежность и долговечность.

*Выберите GRAN TURISMO — и дайте вашему автомобилю лучшее!*
"""
    
    try:
        with open("icon.jpg", 'rb') as photo:
            if message.from_user.id != 1965630668 and message.from_user.id != 1109848616:
                bot.send_photo(message.chat.id, photo, caption=text, reply_markup=markup, parse_mode='Markdown')
            else:
                 markup = types.InlineKeyboardMarkup(row_width=1)
                 markup.add(
                     types.InlineKeyboardButton("Ассортимент 🛒", callback_data='shop'),
                     types.InlineKeyboardButton("Тех Поддержка 🎙", callback_data='support'),
                     types.InlineKeyboardButton("WhatsApp 📗", url="https://wa.me/+79250648771"),
                     types.InlineKeyboardButton("Панель админа", callback_data="admin")
                     )
                 bot.send_photo(message.chat.id, photo, caption=text, reply_markup=markup, parse_mode='Markdown')
    except FileNotFoundError:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# Глобальный словарь для хранения состояний (добавьте в начало скрипта)
user_stats = {}

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global user_stats
    try:
        if call.data == 'shop':
            show_categories(call)
        elif call.data == 'duck':
            send_duck(call, 1)
        elif call.data == 'next_duck':
            current = get_current_duck_id(call)
            send_duck(call, current + 1)
        elif call.data == 'prev_duck':
            current = get_current_duck_id(call)
            send_duck(call, current - 1)
        elif call.data == 'back1':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
        elif call.data == 'back2':
            show_categories(call)
        elif call.data.startswith('buy-'):
            buy(call)
        elif call.data == 'cancel_order':
            cancel_order(call)
        elif call.data == 'admin':
            if call.from_user.id == 1965630668 or call.from_user.id == 1109848616:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("Добавить Бренд 💼", callback_data='brend'),
                    types.InlineKeyboardButton("Добавить Товар 📦", callback_data='product'),
                    types.InlineKeyboardButton("Назад 🔙", callback_data='back1')
                )
                bot.send_message(call.message.chat.id, "Что нужно сделать", reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, "Вы не администратор!!")
        elif call.data == 'brend':
            if call.from_user.id == 1965630668 or call.from_user.id == 1109848616:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("Масла", callback_data='set-Масла'),
                    types.InlineKeyboardButton("Анти Фриз", callback_data='set-АнтиФриз'),
                    types.InlineKeyboardButton("Ароматизаторы", callback_data='set-Ароматизаторы'),
                    types.InlineKeyboardButton("Свет", callback_data='set-Свет'),
                    types.InlineKeyboardButton("Косметика", callback_data='set-Косметика'),
                    types.InlineKeyboardButton("Эмаль", callback_data='set-Эмаль'),
                    types.InlineKeyboardButton("Автохимия", callback_data='set-Автохимия'),
                    types.InlineKeyboardButton("Фильтра", callback_data='set-Фильтра'),
                    types.InlineKeyboardButton("Отмена ❌", callback_data='cancel')
                )
                bot.send_message(call.message.chat.id, "Выберите категорию", reply_markup=markup)
        elif call.data.startswith('var-'):
            category_name = call.data.split('-')[1]
            filename = f"database/{category_name}.txt"
            
            brands = []
            
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    brands = [line.strip() for line in file.readlines() if line.strip()]
            
            if not brands:
                bot.send_message(call.message.chat.id, "⛔ Бренды для этой категории не найдены")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            for brand in brands:
                markup.add(types.InlineKeyboardButton(
                    brand, 
                    callback_data=f'brand-{category_name}-{brand}'
                ))
            
            markup.add(types.InlineKeyboardButton(
                "Назад 🔙", 
                callback_data='back2'
            ))
            
            bot.send_message(
                call.message.chat.id,
                f"Доступные Бренды Из Категории: *{category_name}*:",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        elif call.data.startswith('set-'):
            model_name = call.data.split('-')
            tax = model_name[1]
            user_stats[call.from_user.id] = {'state': 'awaiting_brand', 'category': tax}
            markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Отмена ❌", callback_data='cancel')
            markup.add(cancel_button)
            if call.from_user.id == 1965630668 or call.from_user.id == 1109848616:
                msg = bot.send_message(call.message.chat.id, f"Введите название бренда для категории {tax}:", reply_markup=markup)
                bot.register_next_step_handler(msg, partial(start_2, model_name=tax))
            else:
                bot.send_message(call.message.chat.id, "Вы не администратор ❗")
        elif call.data == "cancel":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if call.from_user.id in user_stats:
                del user_stats[call.from_user.id]
                bot.clear_step_handler_by_chat_id(call.message.chat.id)
                bot.send_message(call.message.chat.id, "Ввод отменен.")
        elif call.data == 'product':
            if call.from_user.id == 1965630668 or call.from_user.id == 1109848616:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("Масла", callback_data='addprod-Масла'),
                    types.InlineKeyboardButton("Анти Фриз", callback_data='addprod-АнтиФриз'),
                    types.InlineKeyboardButton("Ароматизаторы", callback_data='addprod-Ароматизаторы'),
                    types.InlineKeyboardButton("Свет", callback_data='addprod-Свет'),
                    types.InlineKeyboardButton("Косметика", callback_data='addprod-Косметика'),
                    types.InlineKeyboardButton("Эмаль", callback_data='addprod-Эмаль'),
                    types.InlineKeyboardButton("Автохимия", callback_data='addprod-Автохимия'),
                    types.InlineKeyboardButton("Фильтра", callback_data='addprod-Фильтра'),
                    types.InlineKeyboardButton("Отмена ❌", callback_data='cancel')
                )
                bot.send_message(call.message.chat.id, "Выберите категорию для товара:", reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, "⛔ У вас нет прав администратора!")
        elif call.data.startswith('addprod-'):
            category = call.data.split('-')[1]
            user_stats[call.from_user.id] = {
                'state': 'adding_product',
                'step': 'select_brand',
                'category': category
            }
            filename = f"database/{category}.txt"
            brands = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    brands = [line.strip() for line in file.readlines() if line.strip()]
            
            if not brands:
                bot.send_message(call.message.chat.id, "⛔ В этой категории нет брендов. Сначала добавьте бренды.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            for brand in brands:
                markup.add(types.InlineKeyboardButton(brand, callback_data=f'selectbrand-{brand}'))
            markup.add(types.InlineKeyboardButton("Отмена ❌", callback_data='cancel'))
            bot.send_message(call.message.chat.id, f"Выберите бренд для товара в категории {category}:", reply_markup=markup)
        elif call.data.startswith('selectbrand-'):
            brand = call.data.split('-')[1]
            user_data = user_stats[call.from_user.id]
            user_data['brand'] = brand
            user_data['step'] = 'enter_name'
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Отмена ❌", callback_data='cancel'))
            msg = bot.send_message(call.message.chat.id, f"Введите название товара для бренда {brand}:", reply_markup=markup)
            bot.register_next_step_handler(msg, process_product_name)
        elif call.data.startswith('brand-'):
            parts = call.data.split('-')
            if len(parts) == 3:
                category, brand = parts[1], parts[2]
                show_products(call, category, brand)
        elif call.data.startswith('prevprod-'):
            parts = call.data.split('-')
            if len(parts) == 4:
                category, brand, index = parts[1], parts[2], int(parts[3])
                show_products(call, category, brand, index-1)
        elif call.data.startswith('nextprod-'):
            parts = call.data.split('-')
            if len(parts) == 4:
                category, brand, index = parts[1], parts[2], int(parts[3])
                show_products(call, category, brand, index+1)
        elif call.data.startswith('buyprod-'):
            product_id = call.data[8:]
            buy_product(call, product_id)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        bot.answer_callback_query(call.id, "Произошла ошибка, попробуйте позже")
    

def get_current_duck_id(call):
    if call.message.content_type == 'photo':
        text = call.message.caption or ""
    else:
        text = call.message.text or ""
    
    if not text:
        return 1
    
    try:
        return int(text.split('\n')[0].split('/')[0])
    except:
        return 1

def show_categories(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Масла", callback_data='var-Масла'),
        types.InlineKeyboardButton("Анти Фриз", callback_data='var-АнтиФриз'),
        types.InlineKeyboardButton("Ароматизаторы", callback_data='var-Ароматизаторы'),
        types.InlineKeyboardButton("Свет", callback_data='var-Свет'),
        types.InlineKeyboardButton("Косметика", callback_data='var-Косметика'),
        types.InlineKeyboardButton("Эмаль", callback_data='var-Эмаль'),
        types.InlineKeyboardButton("Автохимия", callback_data='var-Автохимия'),
        types.InlineKeyboardButton("Фильтра", callback_data='var-Фильтра'),
        types.InlineKeyboardButton("Отмена ❌", callback_data='cancel')
    )
    
    caption = "👣 Шаг 1 Из 3 👣\n\nВыберите категорию товаров:"
    
    try:
        with open("icon.jpg", 'rb') as photo:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=photo,
                caption=caption,
                reply_markup=markup
            )
    except Exception as e:
        print(f"Ошибка при отправке фото: {e}")
        try:
            if call.message.content_type == 'photo':
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=caption,
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=caption,
                    reply_markup=markup
                )
        except:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=caption,
                reply_markup=markup
            )

def send_duck(call, duck_id):
    duck_id = max(1, min(duck_id, len(ducks)))
    duck = ducks[duck_id]
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⬅️", callback_data='prev_duck'),
        types.InlineKeyboardButton(f"{duck_id}/{len(ducks)}", callback_data='none'),
        types.InlineKeyboardButton("➡️", callback_data='next_duck')
    )
    markup.row(types.InlineKeyboardButton("🛒 Заказать", callback_data=f'buy-{duck_id}'))
    markup.add(types.InlineKeyboardButton("Назад к категориям", callback_data='back2'))
    
    text = f"{duck_id}/{len(ducks)}\n{duck['name']}\n\n{duck['description']}\n\nЦена: {duck['price']}"
    
    try:
        with open(duck['photo'], 'rb') as photo:
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    types.InputMediaPhoto(photo, caption=text),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
            else:
                bot.send_photo(call.message.chat.id, photo, caption=text, reply_markup=markup)
    except:
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup
            )
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)

def buy(call):
    if call.data.startswith('buy-'):
        duck_id = int(call.data.split('-')[1])
        duck = ducks[duck_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # Сохраняем информацию о заказе
        user_states[call.message.chat.id] = {
            'product': duck['name'],
            'price': duck['price'],
            'step': 'waiting_data'
        }
        
        opra = (
            "\n\n1. ФИО Получателя -"
            "\n2. Адресные Данные:"
            "\n• Индекс -"
            "\n• Регион -"
            "\n• Город или населённый пункт -"
            "\n3. Телефонный номер -"
            "\n4. Электронная почта (по желанию) -"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить заказ", callback_data='cancel_order'))
        
        msg = bot.send_message(
            call.message.chat.id, 
            f"Отлично❗️, вижу вам пригляделся/ась {duck['name']} за {duck['price']}.\n\nОтличный выбор ❗️ но для отправки посылки нужно заполнить бланк снизу 👇🏻 {opra}", 
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_order_data)

def process_order_data(message):
    chat_id = message.chat.id
    
    # Проверяем, есть ли активный заказ
    if chat_id not in user_states or user_states[chat_id]['step'] != 'waiting_data':
        bot.send_message(chat_id, "Ваш заказ был отменен или завершен. Начните заново с /start")
        return
    
    # Сохраняем данные пользователя
    user_states[chat_id]['user_data'] = message.text
    user_states[chat_id]['step'] = 'waiting_payment'
    
    # Отправляем реквизиты для оплаты
    payment_markup = types.InlineKeyboardMarkup()
    payment_markup.add(types.InlineKeyboardButton("❌ Отменить заказ", callback_data='cancel_order'))
    
    payment_text = f"""
*Мы Почти У Цели ❗*

Для завершения заказа {user_states[chat_id]['product']} за {user_states[chat_id]['price']}:

1. Переведите сумму {user_states[chat_id]['price']} на карту:
`8888 8888 8888 8888`

2. После оплаты отправьте фото чека или скриншот перевода.

*Внимание!* Заказ будет обработан только после подтверждения оплаты.
"""
    
    bot.send_message(
        chat_id,
        payment_text,
        reply_markup=payment_markup,
        parse_mode='Markdown'
    )
    
    # Ждем фото оплаты
    bot.register_next_step_handler(message, process_payment)

def buy_product(call, product_id):
    print(f"Ищем товар с ID: {product_id}")
    
    if not os.path.exists('database'):
        bot.send_message(call.message.chat.id, "⛔ Ошибка системы", reply_markup=back2)
        return
    
    found = False
    for filename in os.listdir('database'):
        if filename.startswith('products_') and filename.endswith('.json'):
            try:
                with open(f'database/{filename}', 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    for product in products:
                        if product.get('id') == product_id:
                            print(f"Найден товар: {product['name']}")
                            found = True
                            
                            user_states[call.message.chat.id] = {
                                'product': product['name'],
                                'price': product['price'],
                                'step': 'waiting_data',
                                'product_data': product
                            }
                            
                            opra = "\n\n1. ФИО Получателя -\n2. Адресные Данные:\n• Индекс -\n• Регион -\n• Город -\n3. Телефон -\n4. Email -"
                            
                            markup = types.InlineKeyboardMarkup()
                            markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data='cancel_order'))
                            
                            # Удаляем предыдущее сообщение (если есть)
                            try:
                                bot.delete_message(call.message.chat.id, call.message.message_id)
                            except:
                                pass
                            
                            # Отправляем запрос данных
                            msg = bot.send_message(
                                call.message.chat.id,
                                f"Вижу Вы выбрали: {product['name']} стоимость {product['price']}\n\nПожалуйста, заполните данные для отправки:{opra}",
                                reply_markup=markup
                            )
                            
                            # Регистрируем обработчик
                            bot.register_next_step_handler(msg, process_order_data)
                            break
                    if found:
                        break
            except Exception as e:
                print(f"Ошибка чтения {filename}: {e}")
    
    if not found:
        print(f"Товар с ID {product_id} не найден")
        bot.send_message(
            call.message.chat.id,
            "⛔ Ошибка: товар не найден. Попробуйте снова",
            reply_markup=back2
        )

def process_order_data(message):
    chat_id = message.chat.id
    print(f"Обработка данных для chat_id: {chat_id}")  # Логирование
    
    if chat_id not in user_states or user_states[chat_id]['step'] != 'waiting_data':
        print(f"Некорректное состояние: {user_states.get(chat_id)}")  # Логирование
        bot.send_message(chat_id, "Ваш заказ был отменен или завершен. Начните заново с /start")
        return
    
    # Сохраняем данные
    user_states[chat_id]['user_data'] = message.text
    user_states[chat_id]['step'] = 'waiting_payment'
    
    print(f"Данные сохранены: {message.text}")  # Логирование
    
    # Отправляем реквизиты
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data='cancel_order'))
    
    bot.send_message(
        chat_id,
        f"""*Мы Почти У Цели ❗* 
Отправьте {user_states[chat_id]['price']} по номеру карты 
`1234 5678 9012 3456` (Т-Банк) и пришлите скриншот оплаты.""",
        reply_markup=markup,
        parse_mode='MarkDown'
    )
    
    # Регистрируем обработчик для фото
    bot.register_next_step_handler(message, process_payment)

def cancel_order(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Удаляем состояние пользователя
    if chat_id in user_states:
        del user_states[chat_id]

    # Удаляем сообщение с кнопкой "Отмена"
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    # Отправляем подтверждение отмены
    bot.send_message(
        chat_id,
        "❌ Заказ отменен. Если передумаете — начните заново через /start",
        reply_markup=back2
    )

def process_payment(message):
    chat_id = message.chat.id
    
    if chat_id not in user_states or user_states[chat_id]['step'] != 'waiting_payment':
        bot.send_message(chat_id, "Ваш заказ был отменен или завершен. Начните заново с /start")
        return
    
    if message.content_type == 'photo':
        admin_chat_id = 1965630668
        file_id = message.photo[-1].file_id
        product_data = user_states[chat_id].get('product_data', {})
        
        order_text = f"""
📦 *Новый заказ!*
——————————————
Товар: {user_states[chat_id]['product']}
Категория: {product_data.get('category', 'не указано')}
Бренд: {product_data.get('brand', 'не указано')}
Цена: {user_states[chat_id]['price']}
——————————————
Данные покупателя:
{user_states[chat_id]['user_data']}
——————————————
Чат: @{message.from_user.username or message.from_user.first_name}
ID: {chat_id}
        """
        
        bot.send_photo(admin_chat_id, file_id, order_text, parse_mode='Markdown')
        bot.send_message(chat_id, "✅ Отлично! Ваш заказ и оплата отправлены администрации, ожидайте ответа.", reply_markup=back2)
        del user_states[chat_id]
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Отменить заказ", callback_data='cancel_order'))
        bot.send_message(chat_id, "❌ Это не похоже на фото. Пожалуйста, отправьте скриншот перевода.", reply_markup=markup)
        bot.register_next_step_handler(message, process_payment)


def process_product_name(message):
    user_data = user_stats[message.from_user.id]
    user_data['name'] = message.text
    user_data['step'] = 'enter_price'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Отмена ❌", callback_data='cancel'))
    msg = bot.send_message(message.chat.id, "Введите цену товара (например: 1500 руб):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_product_price)

def process_product_price(message):
    user_data = user_stats[message.from_user.id]
    user_data['price'] = message.text
    user_data['step'] = 'enter_description'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Отмена ❌", callback_data='cancel'))
    msg = bot.send_message(message.chat.id, "Введите описание товара:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_product_description)

def process_product_description(message):
    user_data = user_stats[message.from_user.id]
    user_data['description'] = message.text
    user_data['step'] = 'upload_photo'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Отмена ❌", callback_data='cancel'))
    msg = bot.send_message(message.chat.id, "Отправьте фото товара:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_product_photo)

def process_product_photo(message):
    if message.content_type != 'photo':
        msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте фото товара.")
        bot.register_next_step_handler(msg, process_product_photo)
        return
    
    user_data = user_stats[message.from_user.id]
    
    # Генерируем ID и сохраняем фото
    product_id = str(uuid4())  # Это уже генерирует полный UUID
    print(f"Создаем товар с ID: {product_id}")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        photo_path = f"images/{product_id}.jpg"
        
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
    except Exception as e:
        print(f"Ошибка сохранения фото: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")
        return
    
    # Создаем запись о товаре
    product_data = {
        'id': product_id,
        'name': user_data['name'],
        'brand': user_data['brand'],
        'category': user_data['category'],
        'price': user_data['price'],
        'description': user_data['description'],
        'photo': photo_path
    }
    
    # Сохраняем в JSON
    products_file = f"database/products_{user_data['category']}_{user_data['brand']}.json"
    products = []
    
    if os.path.exists(products_file):
        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
        except Exception as e:
            print(f"Ошибка чтения файла товаров: {e}")
    
    products.append(product_data)
    
    try:
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        print(f"Товар сохранен в {products_file}")  # Логирование
    except Exception as e:
        print(f"Ошибка сохранения товара: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении товара")
        return
    
    bot.send_message(
        message.chat.id,
        f"✅ Товар добавлен!\nID: {product_id}\nКатегория: {user_data['category']}\nБренд: {user_data['brand']}",
        reply_markup=back2
    )
    del user_stats[message.from_user.id]

def show_products(call, category, brand, product_index=0):
    products_file = f"database/products_{category}_{brand}.json"
    print(f"Ищем файл товаров: {products_file}")  # Логирование
    
    if not os.path.exists(products_file):
        print("Файл товаров не найден!")  # Логирование
        bot.send_message(call.message.chat.id, "⛔ Товары этого бренда не найдены")
        return
    
    with open(products_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    if not products:
        print("Файл товаров пуст!")  # Логирование
        bot.send_message(call.message.chat.id, "⛔ Товары этого бренда не найдены")
        return
    
    product_index = max(0, min(product_index, len(products)-1))
    product = products[product_index]
    print(f"Товар найден: {product}")  
    markup = types.InlineKeyboardMarkup()
    row_buttons = []
    if product_index > 0:
        row_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f'prevprod-{category}-{brand}-{product_index}'))
    row_buttons.append(types.InlineKeyboardButton(f"{product_index+1}/{len(products)}", callback_data='none'))
    if product_index < len(products)-1:
        row_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f'nextprod-{category}-{brand}-{product_index}'))
    
    markup.row(*row_buttons)
    markup.row(types.InlineKeyboardButton("🛒 Заказать", callback_data=f'buyprod-{product["id"]}'))
    markup.row(types.InlineKeyboardButton("Назад к брендам", callback_data=f'var-{category}'))
    
    text = f"{product['name']}\n\n{product['description']}\n\nЦена: {product['price']}"
    
    try:
        with open(product['photo'], 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=text, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


def start_5(message):
    verify = 1965630668
    number = message.text
    gay = message.from_user.id
    admin = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton("💬 Написать", callback_data=f'chat-{gay}')
    button2 = types.InlineKeyboardButton("🚫 Блокировка", callback_data=f'ban-{gay}')
    admin.add(button1, button2)

    try:
        bot.reply_to(message, f"Успешно ✅\n\nВаш вопрос был доставлен администрации, ожидайте.", reply_markup=back)
        bot.send_message(verify, f"Запрос в поддержку ❗️❗️❗\n\n{number}",reply_markup=admin)
    except Exception as e:
        # Логируем ошибку или отправляем сообщение об ошибке
        print(f"Произошла ошибка: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже.")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)