import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# 1. ТОКЕН БОТА
TOKEN = "8015421149:AAEyptmat5YGt61SruwlkNBRJYhOREhZ2Ok"

# 2. ID ВАШЕЙ ГРУППЫ ДЛЯ КУХНИ / ПЕРСОНАЛА
ORDERS_GROUP_ID = -1004407668447  

# Ссылка на репозиторий GitHub Pages
BASE_WEBAPP_URL = "https://ktoaziza-jpg.github.io/yurt-menu/"

# Дефолтная ссылка на менеджера поддержки (потом заменишь на реальный юзернейм, например t.me/username)
MANAGER_SUPPORT_URL = "https://t.me/+966500000000"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для отображения блюд в Telegram-группе персонала (всегда на русском для удобства кухни)
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
    'ds1': 'Сан-Себастьян Классический', 'ds2': 'Сан-Себастьян с Нутеллой', 'ds3': 'Фисташковый чизкейк', 'ds4': 'Баурсак в шоколаде', 'ds5': 'Баурсак фисташковый', 'ds6': 'Баурсак со сгущенкой', 'ds7': 'Шоколад Казахстан', 'ds8': 'Бельгийские вафли', 'ds9': 'Арбузная нарезка',
    'dr1': 'Coca Cola 245 ml', 'dr2': 'Pepsi 245 ml', 'dr3': '7Up 250 ml', 'dr4': 'Mirinda 250 ml', 'dr5': 'Kinza 250ml',
    'j1': 'Айс-ти', 'j2': 'Свежий морковный сок', 'j3': 'Айран', 'j4': 'Апельсиновый сок', 'j5': 'Свежий яблочный сок', 'j6': 'Концентрированное молоко', 'j7': 'Вода',
    'cf1': 'Эспрессо кофе', 'cf2': 'Эспрессо Лонг', 'cf3': 'Американо кофе', 'cf4': 'Капучино кофе', 'cf5': 'Латте кофе', 'cf6': 'Колд Брю', 'cf7': 'Айс Американо',
    't1': 'Чай с мятой', 't2': 'Чай с лимоном', 't3': 'Чай Карак', 't4': 'Ташкентский чай', 't5': 'Марокканский чай', 't6': 'Молочный Оолонго', 't7': 'Имбирный чай', 't8': 'Малиновый чай', 't9': 'Чайник черного чая', 't10': 'Чайник зеленого чая',
    'sc1': 'Соус Нутелла', 'sc2': 'Бельгийский шоколад', 'sc3': 'Сгущенное молоко', 'sc4': 'Чесночный соус', 'sc5': 'Йогурт', 'sc6': 'Томатный соус'
}

PAYMENT_LABELS = {
    'cash': '💵 Наличными при получении',
    'terminal': '💳 Картой курьеру (Терминал)',
    'online': '🌐 Онлайн (Apple Pay / Mada)'
}

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
    
    # Поднимаем версию до v=16, чтобы сбросить кэш ссылки
    webapp_url_with_lang = f"{BASE_WEBAPP_URL}?lang={lang_code}&v=20"
    
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
        data = json.loads(message.web_app_data.data)
        
        customer_name = data.get('name', 'Не указано')
        customer_phone = data.get('phone', 'Не указано')
        customer_address = data.get('address', 'Не указано')
        payment_method = data.get('payment', 'cash')
        total_price = data.get('total', '0 SAR')
        cart = data.get('cart', {})
        user_lang = data.get('lang', 'ru') # Получаем выбранный язык
        
        items_text = ""
        for item_id, quantity in cart.items():
            item_name = MENU_NAMES_RU.get(item_id, f"Блюдо {item_id}")
            items_text += f"• {item_name} x {quantity}\n"
            
        pay_label = PAYMENT_LABELS.get(payment_method, payment_method)
        
        order_report = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ (Язык клиента: {user_lang.upper()})</b>\n\n"
            f"👤 <b>Клиент:</b> {customer_name}\n"
            f"📞 <b>Телефон:</b> <code>{customer_phone}</code>\n"
            f"📍 <b>Адрес:</b> {customer_address}\n"
            f"💳 <b>Оплата:</b> {pay_label}\n\n"
            f"📋 <b>Содержимое заказа:</b>\n{items_text}\n"
            f"💰 <b>ИТОГО К ОПЛАТЕ:</b> <b>{total_price}</b>"
        )
        
        # Передаем язык пользователя прямо в callback_data кнопок управления для персонала
        order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🍳 Принять в работу", callback_data=f"status_accept_{message.from_user.id}_{user_lang}")
            ]
        ])
        
        await bot.send_message(
            chat_id=ORDERS_GROUP_ID,
            text=order_report,
            parse_mode="HTML",
            reply_markup=order_keyboard
        )
        
        # Текст подтверждения и инлайн-кнопка поддержки на двух языках
        if user_lang == 'en':
            success_text = (
                f"✨ <b>Thank you for your order, {customer_name}!</b>\n\n"
                f"Your order has been successfully placed and sent to the kitchen of Yurt Medina restaurant.\n"
                f"It is currently being processed. We will notify you as soon as the dishes start cooking!"
            )
            support_btn_text = "💬 Contact Support"
        else:
            success_text = (
                f"✨ <b>Спасибо за ваш заказ, {customer_name}!</b>\n\n"
                f"Заказ успешно оформлен и передан на кухню ресторана Yurt Медина.\n"
                f"В данный момент он находится в обработке. Мы уведомим вас, как только блюда начнут готовиться!"
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
    
    # Достаем язык клиента (если его нет в старых заказах, по умолчанию берем 'ru')
    user_lang = data_parts[3] if len(data_parts) > 3 else 'ru'
    
    manager_name = callback.from_user.first_name
    current_text = callback.message.text
    
    if action == "accept":
        updated_text = f"{current_text}\n\n👨‍🍳 <b>Заказ принят в работу (Менеджер: {manager_name})</b>"
        
        next_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🛵 Передать курьеру", callback_data=f"status_delivery_{client_id}_{user_lang}")
            ]
        ])
        
        await callback.message.edit_text(text=updated_text, parse_mode="HTML", reply_markup=next_keyboard)
        
        # Отправляем статус в зависимости от языка клиента
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
        
        await callback.message.edit_text(text=updated_text, parse_mode="HTML", reply_markup=None)
        
        # Отправляем статус доставки в зависимости от языка клиента
        if user_lang == 'en':
            client_msg = "🛵 <b>Your order is on its way!</b>\nThe courier has picked up the hot dishes from the restaurant and is heading to your address. Please expect delivery soon!"
        else:
            client_msg = "🛵 <b>Ваш заказ уже в пути!</b>\nКурьер забрал горячие блюда из ресторана и направляется по вашему адресу. Пожалуйста, ожидайте доставку!"
            
        try:
            await bot.send_message(chat_id=int(client_id), text=client_msg, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Не удалось отправить статус клиенту: {e}")
            
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            logging.info("Бот запускается...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Сбой: {e}. Рестарт через 5 сек...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())