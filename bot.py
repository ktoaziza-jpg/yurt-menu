import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# 1. ВСТАВЬТЕ СЮДА ВАШ ТОКЕН
TOKEN = "8015421149:AAEyptmat5YGt61SruwlkNBRJYhOREhZ2Ok"

# 2. ВСТАВЬТЕ СЮДА ID ВАШЕЙ СОЗДАННОЙ ГРУППЫ (вместе с минусом!)
ORDERS_GROUP_ID = -1004407668447  # Замените это число на ваш ID из Шага 1

# Ваша ссылка с GitHub (БЕЗ index.html на конце!)
BASE_WEBAPP_URL = "https://ktoaziza-jpg.github.io/yurt-menu/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для красивого отображения названий блюд менеджерам
MENU_NAMES_RU = {
    's1': 'Весенний Бахор', 's2': 'Ачичук', 's3': 'Огурцы по-корейски', 's4': 'Коул Слоу', 's5': 'Маринованный Редис',
    'm1': 'Плов', 'm2': 'Бешбармак', 'm3': 'Лагман', 'm4': 'Ганфан', 'm5': 'Курица Табака с Рисом', 'm6': 'Манты по-уйгурски', 'm7': 'Вареники с картофелем',
    'sp1': 'Шурпа', 'sp2': 'Мастава', 'sp3': 'Пельмени',
    'sn1': 'Самса с курицей', 'sn2': 'Самса с говядиной', 'sn3': 'Чебуреки', 'sn4': 'Долма',
    'k1': 'Люля Кебаб', 'k2': 'Говяжий Кебаб', 'k3': 'Куриный Кебаб', 'k4': 'Казан Кебаб Куриный', 'k5': 'Казан Кебаб Баранина', 'k6': 'Куриный + Люля Комбо', 'k7': 'Говяжий + Куриный Комбо', 'k8': 'Люля + Говяжий Комбо',
    'sd1': 'Рис с овощами', 'sd2': 'Рис', 'sd3': 'Картофель Фри', 'br1': 'Баурсаки', 'br2': 'Лепешка Кулча Нон',
    'ds1': 'Сан-Себастьян Классический', 'ds2': 'Сан-Себастьян Фисташковый', 'ds3': 'Сан-Себастьян Лотус', 'ds4': 'Шоколад Казахстан',
    'dr1': 'Kinza Вода с газом', 'dr2': 'Kinza Cola', 'dr3': 'Kinza Lemon', 'dr4': 'Kinza Orange', 'dr5': 'Coca Cola', 'dr6': 'Fanta', 'dr7': 'Sprite', 'dr8': 'Pepsi', 'dr9': 'Mirinda', 'dr10': '7UP', 'dr11': 'Фреш Апельсин', 'dr12': 'Фреш Яблоко', 'dr13': 'Фреш Морковь', 'dr14': 'Айс-ти', 'dr15': 'Айран',
    'cf1': 'Эспрессо', 'cf2': 'Лонг Эспрессо', 'cf3': 'Американо', 'cf4': 'Айс-Американо', 'cf5': 'Капучино', 'cf6': 'Латте',
    'hd1': 'Черный чай', 'hd2': 'Зеленый чай', 'sc1': 'Томатный соус', 'sc2': 'Йогуртовый соус', 'sc3': 'Сгущенка', 'sc4': 'Nutella', 'sc5': 'Lotus'
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
    
    # Меняем версию на v=4, чтобы намертво пробить кэш во время тестов
    webapp_url_with_lang = f"{BASE_WEBAPP_URL}?lang={lang_code}&v=4"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🍽 Open Menu" if lang_code == 'en' else "🍽 Открыть меню", 
            web_app=WebAppInfo(url=webapp_url_with_lang)
        )]
    ])
    
    text = "Great! Tap the button below:" if lang_code == 'en' else "Отлично! Нажмите кнопку ниже:"
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ХЕНДЛЕР ПРИЕМА ЗАКАЗА ИЗ WEB APP
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
        
        # Формируем список блюд для кухни
        items_text = ""
        for item_id, quantity in cart.items():
            item_name = MENU_NAMES_RU.get(item_id, f"Блюдо {item_id}")
            items_text += f"• {item_name} x {quantity}\n"
            
        pay_label = PAYMENT_LABELS.get(payment_method, payment_method)
        
        # Красивый шаблон заказа для персонала в группу
        order_report = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
            f"👤 <b>Клиент:</b> {customer_name}\n"
            f"📞 <b>WhatsApp:</b> <code>{customer_phone}</code>\n"
            f"📍 <b>Адрес:</b> {customer_address}\n"
            f"💳 <b>Оплата:</b> {pay_label}\n\n"
            f"📋 <b>Содержимое заказа:</b>\n{items_text}\n"
            f"💰 <b>ИТОГО К ОПЛАТЕ:</b> <b>{total_price}</b>"
        )
        
        # Инлайн-кнопки для управления статусом внутри группы
        order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🍳 Принять", callback_data=f"status_accept_{message.from_user.id}"),
                InlineKeyboardButton(text="🛵 В доставке", callback_data=f"status_delivery_{message.from_user.id}")
            ]
        ])
        
        # Отправляем заказ в группу менеджеров
        await bot.send_message(
            chat_id=ORDERS_GROUP_ID,
            text=order_report,
            parse_mode="HTML",
            reply_markup=order_keyboard
        )
        
        # Отвечаем клиенту в личку
        await message.answer(
            f"🎉 Спасибо за заказ, {customer_name}!\n"
            f"Мы уже передали его в ресторан. Способ оплаты: {pay_label}.\n"
            f"Менеджер свяжется с вами по WhatsApp в ближайшее время!"
        )
        
    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}")
        await message.answer("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.")

# Обработка нажатия кнопок управления в группе
@dp.callback_query(F.data.startswith("status_"))
async def handle_status_buttons(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    action = data_parts[1]
    client_id = data_parts[2]
    
    manager_name = callback.from_user.first_name
    current_text = callback.message.text
    
    if action == "accept":
        updated_text = f"{current_text}\n\n✅ <b>Заказ принят менеджером {manager_name} и отправлен на кухню!</b>"
        await callback.message.edit_text(text=updated_text, parse_mode="HTML")
        try:
            await bot.send_message(chat_id=client_id, text="👨‍🍳 Ваш заказ принят рестораном и уже готовится!")
        except:
            pass
            
    elif action == "delivery":
        updated_text = f"{current_text}\n\n🛵 <b>Заказ передан курьеру (Изменил: {manager_name})!</b>"
        await callback.message.edit_text(text=updated_text, parse_mode="HTML")
        try:
            await bot.send_message(chat_id=client_id, text="🛵 Курьер забрал ваш заказ и выехал по адресу доставки!")
        except:
            pass
            
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