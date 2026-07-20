import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# 1. ТОКЕН БОТА
TOKEN = "8015421149:AAEyptmat5YGt61SruwlkNBRJYhOREhZ2Ok"

# 2. ID ВАШЕЙ ГРУППЫ ДЛЯ КУХНИ / ПЕРСОНАЛА
ORDERS_GROUP_ID = -1004407668447  

# Ссылка на репозиторий GitHub Pages
BASE_WEBAPP_URL = "https://ktoaziza-jpg.github.io/yurt-menu/"

# Ссылка на менеджера поддержки
MANAGER_SUPPORT_URL = "https://t.me/+966500000000"

# Координаты и адрес ресторана для самовывоза
RESTAURANT_MAPS_URL = "https://maps.google.com/?q=24.461623,39.611146"  # FJ76+964 Madinah
RESTAURANT_ADDRESS = "📍 As Safiyyah Museum and Park, 4th floor"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для отображения блюд в Telegram-группе персонала
MENU_NAMES_RU = {
    's1': 'Соленые огурцы', 's2': 'Витаминный салат', 's3': 'Огурцы по-корейски', 's4': 'Салат Бахор', 's5': 'Салат Ачичук',
    'sn1': 'Ассорти самсы', 'sn2': 'Чебурек', 'sn3': 'Долма из говядины',
    'k1': 'Ассорти кебабов (2 шт)', 'k2': 'Сет ассорти кебабов (20 шт)',
    'g1': 'Шаурма с говядиной на гриле', 'g2': 'Шаурма с курицей на гриле',
    'sp1': 'Шурпа', 'sp2': 'Суп Пельмени', 'sp3': 'Мастава', 'sp4': 'Окрошка с говядиной',
    'm1': 'Плов', 'm2': 'Ганфан', 'm3': 'Курица Табака', 'm4': 'Бешбармак', 'm5': 'Манты (4 шт)', 'm6': 'Лагман', 'm7': 'Казан Кебаб с курицей', 'm8': 'Жареные пельмени',
    'sd1': 'Рис Басмати', 'sd2': 'Рис с овощами', 'sd3': 'Картофель Фри',
    'br1': 'Лепешка Кулча', 'br2': 'Баурсак',
    'l1': 'Розовая Матча', 'l2': 'Голубая Матча Анчан', 'l3': 'Матча Манго Кокос', 'l4': 'Свежий Апельсин', 'l5': 'Ягодный лимонад', 'l6': 'Цитрусовый лимонад',
    'ds1': 'Сан-Себастьян Классический', 'ds2': 'Сан-Себастьян с Нутеллой', 'ds3': 'Фисташковый чизкейк', 'ds4': 'Баурсак в шоколаде', 'ds5': 'Баурсак фисташковый', 'ds6': 'Баурсак со сгущенкой', 'ds7': 'Шоколад Kazakhstan', 'ds8': 'Бельгийские вафли', 'ds9': 'Арбузная нарезка',
    'dr1': 'Coca Cola 245 ml', 'dr2': 'Pepsi 245 ml', 'dr3': '7Up 250 ml', 'dr4': 'Mirinda 250 ml', 'dr5': 'Kinza 250ml',
    'j1': 'Айс-ти', 'j2': 'Свежий морковный сок', 'j3': 'Айран', 'j4': 'Апельсиновый сок', 'j5': 'Свежий яблочный сок', 'j6': 'Концентрированное молоко', 'j7': 'Вода',
    'cf1': 'Эспрессо кофе', 'cf2': 'Эспрессо Лонг', 'cf3': 'Американо кофе', 'cf4': 'Капучино кофе', 'cf5': 'Латте кофе', 'cf6': 'Колд Брю', 'cf7': 'Айс Американо',
    't1': 'Чай с мятой', 't2': 'Чай с лимоном', 't3': 'Чай Карак', 't4': 'Ташкентский чай', 't5': 'Марокканский чай', 't6': 'Молочный Оолонго', 't7': 'Имбирный чай', 't8': 'Малиновый чай', 't9': 'Чайник черного чая', 't10': 'Чайник зеленого чая',
    'sc1': 'Соус Нутелла', 'sc2': 'Бельгийский шоколад', 'sc3': 'Сгущенное молоко', 'sc4': 'Чесночный соус', 'sc5': 'Йогурт', 'sc6': 'Томатный соус'
}

def init_db():
    conn = sqlite3.connect("yurt_orders.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            total_price REAL,
            fulfillment_type TEXT,
            items_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_order_to_db(user_id, total_price_str, fulfillment_type, cart_dict):
    try:
        clean_price_str = "".join(c for c in str(total_price_str) if c.isdigit() or c == '.')
        clean_price = float(clean_price_str) if clean_price_str else 0.0
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect("yurt_orders.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, timestamp, total_price, fulfillment_type, items_json) VALUES (?, ?, ?, ?, ?)",
            (user_id, now_str, clean_price, fulfillment_type, json.dumps(cart_dict))
        )
        conn.commit()
        conn.close()
        logging.info("Заказ сохранен в БД.")
    except Exception as e:
        logging.error(f"Ошибка сохранения заказа в БД: {e}")

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    await message.answer(
        "Welcome to Yurt! Please choose your language:\n"
        "Добро пожаловать в Yurt! Пожалуйста, выберите язык:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("lang_"))
async def process_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1] 
    webapp_url_with_lang = f"{BASE_WEBAPP_URL}?lang={lang_code}&v=71"
    
    btn_text = "🍽 Open Menu" if lang_code == 'en' else "🍽 Открыть меню"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn_text, web_app=WebAppInfo(url=webapp_url_with_lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    if lang_code == 'en':
        text = "Great! Tap the big button below to explore our menu:"
    else:
        text = "Отлично! Нажмите на большую кнопку «Открыть меню» внизу экрана:"
        
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        raw_data = message.web_app_data.data
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')
        elif hasattr(raw_data, 'encode') == False:
            raw_data = str(raw_data)
            
        data = json.loads(raw_data)
        
        customer_name = data.get('customer_name') or data.get('name', 'Не указано')
        customer_phone = data.get('phone_number') or data.get('phone', 'Не указано')
        customer_address = data.get('location') or data.get('address', 'Самовывоз / Не указано')
        customer_comment = data.get('comment', '').strip()
        fulfillment_type = data.get('order_type') or data.get('fulfillment', 'delivery')
        target_time = data.get('pickup_time') or data.get('time', 'Как можно скорее')
        payment_method = data.get('payment', 'cash')
        
        subtotal_price = f"{data.get('subtotal', 0)} SAR"
        delivery_cost = f"{data.get('delivery_cost', 0)} SAR"
        total_price = f"{data.get('total_pay') or data.get('total', 0)} SAR"
        
        cart_raw = data.get('items') or data.get('cart', {})
        cart_dict = {}
        if isinstance(cart_raw, list):
            for item in cart_raw:
                cart_dict[item.get('name', 'Блюдо')] = item.get('qty', 1)
        else:
            cart_dict = cart_raw

        user_lang = data.get('lang', 'ru')
        
        tg_user = message.from_user
        username_str = f"@{tg_user.username}" if tg_user.username else "Нет юзернейма"
        tg_profile_link = f"<a href='tg://user?id={tg_user.id}'>{tg_user.full_name}</a>"
        
        # СОХРАНЯЕМ ЗАКАЗ В БАЗУ ДАННЫХ
        save_order_to_db(tg_user.id, total_price, fulfillment_type, cart_dict)

        total_qty = 0
        has_heavy_dish = False
        items_text = ""
        
        for item_key, quantity in cart_dict.items():
            item_name = MENU_NAMES_RU.get(item_key, item_key)
            items_text += f"• {item_name} x {quantity}\n"
            total_qty += quantity
            if item_key in ['k2', 'sn3', 'm4']:
                has_heavy_dish = True
        
        if total_qty <= 2:
            prep_time = "15-20"
        elif total_qty <= 5:
            prep_time = "25-30"
        else:
            prep_time = "40-45"
            
        if has_heavy_dish and total_qty <= 5:
            prep_time = "35-40"
            
        load_warning = ""
        if total_qty > 5 or has_heavy_dish:
            load_warning = "⚠️ <b>ВЫСОКАЯ НАГРУЗКА КУХНИ!</b>\n"

        if fulfillment_type == 'pickup':
            pay_label = "💵 Наличными на кассе" if payment_method == "cash" else "💳 Картой на кассе (Терминал)"
            fulf_label = "🛍️ САМОВЫВОЗ"
        else:
            pay_label = "💵 Наличными курьеру" if payment_method == "cash" else "💳 Картой курьеру (Терминал)"
            fulf_label = "🛵 ДОСТАВКА"
        
        comment_section = f"💬 <b>Комментарий:</b> <u>{customer_comment}</u>\n\n" if customer_comment else ""
        
        order_report = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ — {fulf_label} ({user_lang.upper()})</b>\n\n"
            f"👤 <b>Клиент:</b> {customer_name}\n"
            f"📱 <b>Telegram:</b> {tg_profile_link} ({username_str})\n"
            f"📞 <b>Телефон:</b> <code>{customer_phone}</code>\n"
            f"📍 <b>Получение:</b> {customer_address}\n"
            f"⏱ <b>Время прибытия/выдачи:</b> <b>{target_time}</b>\n"
            f"💳 <b>Оплата:</b> {pay_label}\n\n"
            f"{comment_section}"
            f"📋 <b>Содержимое заказа:</b>\n{items_text}\n"
            f"👨‍🍳 <b>Рекомендуемое время готовки:</b> <b>{prep_time} минут</b>\n"
            f"{load_warning}\n"
            f"───────────────\n"
            f"💰 Блюда: {subtotal_price}\n"
            f"🚗 Доставка: {delivery_cost}\n"
            f"💰 <b>ИТОГО К ОПЛАТЕ: {total_price}</b>"
        )
        
        inline_buttons = [
            [InlineKeyboardButton(text="👨‍🍳 Принять в работу", callback_data=f"status_accept_{message.from_user.id}_{user_lang}_{fulfillment_type}")]
        ]
        
        if fulfillment_type == 'delivery' and customer_address and "http" in customer_address:
            inline_buttons.insert(0, [InlineKeyboardButton(text="📍 Открыть маршрут в картах", url=customer_address)])
            
        order_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
        
        await bot.send_message(
            chat_id=ORDERS_GROUP_ID,
            text=order_report,
            parse_mode="HTML",
            reply_markup=order_keyboard
        )
        
        if user_lang == 'en':
            success_text = (
                f"✨ <b>Thank you for your order, {customer_name}!</b>\n\n"
                f"Your order has been successfully placed and sent to the kitchen. Type: <b>{fulfillment_type.upper()}</b>.\n"
                f"Time request: <b>{target_time}</b>.\n"
                f"We will notify you when preparation starts!"
            )
            support_btn_text = "💬 Contact Support"
        else:
            success_text = (
                f"✨ <b>Спасибо за ваш заказ, {customer_name}!</b>\n\n"
                f"Заказ успешно оформлен и передан на кухню. Тип: <b>{fulfillment_type.upper()}</b>.\n"
                f"Время выдачи/доставки: <b>{target_time}</b>.\n"
                f"Мы уведомим вас, как только блюда начнут готовиться!"
            )
            support_btn_text = "💬 Связаться с поддержкой"

        support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=support_btn_text, url=MANAGER_SUPPORT_URL)]
        ])
        
        await message.answer(
            text=success_text,
            parse_mode="HTML",
            reply_markup=support_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}")
        await message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте снова.")

@dp.callback_query(F.data.startswith("status_"))
async def handle_status_buttons(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    action = data_parts[1]
    client_id = data_parts[2]
    user_lang = data_parts[3] if len(data_parts) > 3 else 'ru'
    fulfillment_type = data_parts[4] if len(data_parts) > 4 else 'delivery'
    
    manager_name = callback.from_user.first_name
    current_text = callback.message.text
    
    existing_reply_markup = callback.message.reply_markup
    maps_button = None
    if existing_reply_markup and existing_reply_markup.inline_keyboard:
        for row in existing_reply_markup.inline_keyboard:
            for btn in row:
                if btn.url and ("maps" in btn.url or "google" in btn.url):
                    maps_button = btn
                    break

    if action == "accept":
        updated_text = f"{current_text}\n\n👨‍🍳 <b>Заказ принят в работу (Менеджер: {manager_name})</b>"
        
        if fulfillment_type == 'pickup':
            next_btn_text = "🛍️ Готов к выдаче"
            next_callback = f"status_ready_{client_id}_{user_lang}_{fulfillment_type}"
        else:
            next_btn_text = "🛵 Передать курьеру"
            next_callback = f"status_delivery_{client_id}_{user_lang}_{fulfillment_type}"
            
        next_buttons = [
            [InlineKeyboardButton(text=next_btn_text, callback_data=next_callback)]
        ]
        if maps_button:
            next_buttons.insert(0, [maps_button])
            
        next_keyboard = InlineKeyboardMarkup(inline_keyboard=next_buttons)
        await callback.message.edit_text(text=updated_text, parse_mode="HTML", reply_markup=next_keyboard)
        
        if user_lang == 'en':
            client_msg = "👨‍🍳 <b>Status Update:</b>\nYour order has been accepted by the chef of Yurt restaurant and is now being freshly cooked in the kitchen!"
        else:
            client_msg = "👨‍🍳 <b>Обновление статуса:</b>\nВаш заказ принят шеф-поваром ресторана Yurt и уже вовсю готовится на кухне!"
            
        try:
            await bot.send_message(chat_id=int(client_id), text=client_msg, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не удалось отправить статус клиенту: {e}")
            
    elif action == "delivery":
        updated_text = f"{current_text}\n\n✅ <b>Заказ приготовлен и передан курьеру!</b>"
        
        final_buttons = [[maps_button]] if maps_button else None
        final_keyboard = InlineKeyboardMarkup(inline_keyboard=final_buttons) if final_buttons else None
        
        await callback.message.edit_text(text=updated_text, parse_mode="HTML", reply_markup=final_keyboard)
        
        if user_lang == 'en':
            client_msg = "🛵 <b>Your order is on its way!</b>\nThe courier has picked up the hot dishes from the restaurant and is heading to your address. Please expect delivery soon!"
        else:
            client_msg = "🛵 <b>Ваш заказ уже в пути!</b>\nКурьер забрал горячие блюда из ресторана и направляется по вашему адресу. Пожалуйста, ожидайте доставку!"
            
        try:
            await bot.send_message(chat_id=int(client_id), text=client_msg, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не удалось отправить статус клиенту: {e}")

    elif action == "ready":
        updated_text = f"{current_text}\n\n✅ <b>Заказ приготовлен и ожидает клиента в ресторане!</b>"
        
        await callback.message.edit_text(text=updated_text, parse_mode="HTML", reply_markup=None)
        
        if user_lang == 'en':
            client_msg = (
                f"🛍️ <b>Your order is ready for pickup!</b>\n\n"
                f"We are waiting for you at the restaurant Yurt:\n"
                f"🏢 <b>Address:</b> {RESTAURANT_ADDRESS}\n\n"
                f"You can open the map below to find the best route. See you soon!"
            )
            map_btn_text = "📍 Open route in Google Maps"
        else:
            client_msg = (
                f"🛍️ <b>Ваш заказ готов к выдаче!</b>\n\n"
                f"Ждем вас в ресторане Yurt по адресу:\n"
                f"🏢 <b>Адрес:</b> {RESTAURANT_ADDRESS}\n\n"
                f"Нажмите на кнопку ниже, чтобы открыть маршрут в Google Картах. До встречи!"
            )
            map_btn_text = "📍 Открыть маршрут в Google Картах"

        client_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=map_btn_text, url=RESTAURANT_MAPS_URL)]
        ])
            
        try:
            await bot.send_message(chat_id=int(client_id), text=client_msg, parse_mode="HTML", reply_markup=client_keyboard)
        except Exception as e:
            logging.error(f"Не удалось отправить статус самовывоза клиенту: {e}")
            
    await callback.answer()


@dp.message(Command("stats"))
async def show_statistics(message: types.Message):
    if message.chat.id != ORDERS_GROUP_ID:
        return

    args = message.text.split()
    period = "day"
    if len(args) > 1 and args[1].lower() in ["week", "неделя"]:
        period = "week"

    try:
        conn = sqlite3.connect("yurt_orders.db")
        cursor = conn.cursor()
        
        now = datetime.now()
        
        if period == "day":
            date_filter = now.strftime("%Y-%m-%d")
            query_filter = f"{date_filter}%"
            title_text = "за сегодня"
            
            cursor.execute("""
                SELECT COUNT(*), SUM(total_price), MAX(timestamp) 
                FROM orders 
                WHERE timestamp LIKE ?
            """, (query_filter,))
        else:
            seven_days_ago = now - timedelta(days=7)
            date_filter = seven_days_ago.strftime("%Y-%m-%d %H:%M:%S")
            title_text = "за последние 7 дней"
            
            cursor.execute("""
                SELECT COUNT(*), SUM(total_price), MAX(timestamp) 
                FROM orders 
                WHERE timestamp >= ?
            """, (date_filter,))
        
        count, total_sum, last_timestamp = cursor.fetchone()
        
        if not count or count == 0:
            await message.reply(f"📊 <b>Статистика {title_text}</b>\n\nЗаказов за этот период пока не найдено.")
            conn.close()
            return

        total_sum = total_sum or 0.0
        avg_check = total_sum / count if count > 0 else 0

        last_order_text = "нет данных"
        if last_timestamp:
            try:
                last_order_dt = datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S")
                diff = now - last_order_dt
                minutes = int(diff.total_seconds() // 60)
                if minutes < 60:
                    last_order_text = f"{max(0, minutes)} мин назад"
                else:
                    hours = minutes // 60
                    last_order_text = f"{hours} ч {minutes % 60} мин назад"
            except Exception as dt_err:
                logging.error(f"Ошибка парсинга даты заказа: {dt_err}")

        if period == "day":
            cursor.execute("SELECT items_json FROM orders WHERE timestamp LIKE ?", (query_filter,))
        else:
            cursor.execute("SELECT items_json FROM orders WHERE timestamp >= ?", (date_filter,))
            
        orders_jsons = cursor.fetchall()
        
        dish_counts = {}
        for (item_json,) in orders_jsons:
            try:
                cart = json.loads(item_json)
                for item_id, qty in cart.items():
                    dish_name = MENU_NAMES_RU.get(item_id, f"Блюдо {item_id}")
                    dish_counts[dish_name] = dish_counts.get(dish_name, 0) + qty
            except:
                continue

        sorted_dishes = sorted(dish_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_dishes_text = ""
        if sorted_dishes:
            for idx, (name, qty) in enumerate(sorted_dishes, 1):
                top_dishes_text += f"{idx}. {name} — {qty} шт\n"
        else:
            top_dishes_text = "Нет данных о блюдах\n"

        report = (
            f"📊 <b>Статистика {title_text}</b>\n\n"
            f"🛒 <b>Заказов:</b> {count}\n"
            f"💰 <b>Выручка:</b> {int(total_sum)} SAR\n"
            f"🧾 <b>Средний чек:</b> {int(avg_check)} SAR\n\n"
            f"🏆 <b>Топ блюд:</b>\n{top_dishes_text}\n"
            f"⏳ <b>Последний заказ:</b> {last_order_text}"
        )
        
        await message.reply(report, parse_mode="HTML")
        conn.close()
        
    except Exception as e:
        logging.error(f"Ошибка вывода статистики: {e}")
        await message.reply("Не удалось загрузить статистику. Попробуйте позже.")


async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    while True:
        try:
            logging.info("Бот запускается...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Сбой: {e}. Рестарт через 5 сек...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())