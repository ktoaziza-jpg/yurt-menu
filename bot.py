import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────
TOKEN           = "8015421149:AAEyptmat5YGt61SruwlkNBRJYhOREhZ2Ok"
ORDERS_GROUP_ID = -1004407668447
BASE_WEBAPP_URL = "[https://ktoaziza-jpg.github.io/yurt-menu/](https://ktoaziza-jpg.github.io/yurt-menu/)"
MANAGER_SUPPORT_URL   = "[https://t.me/+966500000000](https://t.me/+966500000000)"
RESTAURANT_MAPS_URL   = "[https://maps.google.com/?q=24.461623,39.611146](https://maps.google.com/?q=24.461623,39.611146)"
RESTAURANT_ADDRESS    = "📍 As Safiyyah Museum and Park, 4th floor"
API_PORT        = 8080          # порт API-сервера
CASHBACK_PCT    = 0.05          # 5% кэшбэк с каждого заказа
# ──────────────────────────────────────────────────────────────────────────────

bot = Bot(token=TOKEN)
dp  = Dispatcher()

MENU_NAMES_RU = {
    's1':'Соленые огурцы','s2':'Витаминный салат','s3':'Огурцы по-корейски',
    's4':'Салат Бахор','s5':'Салат Ачичук',
    'sn1':'Ассорти самсы','sn2':'Чебурек','sn3':'Долма из говядины',
    'k1':'Ассорти кебабов (2 шт)','k2':'Сет ассорти кебабов (20 шт)',
    'g1':'Шаурма с говядиной на гриле','g2':'Шаурма с курицей на гриле',
    'sp1':'Шурпа','sp2':'Суп Пельмени','sp3':'Мастава','sp4':'Окрошка с говядиной',
    'm1':'Плов','m2':'Ганфан','m3':'Курица Табака','m4':'Бешбармак',
    'm5':'Манты (4 шт)','m6':'Лагман','m7':'Казан Кебаб с курицей','m8':'Жареные пельмени',
    'sd1':'Рис Басмати','sd2':'Рис с овощами','sd3':'Картофель Фри',
    'br1':'Лепешка Кулча','br2':'Баурсак',
    'l1':'Розовая Матча','l2':'Голубая Матча Анчан','l3':'Матча Манго Кокос',
    'l4':'Свежий Апельсин','l5':'Ягодный лимонад','l6':'Цитрусовый лимонад',
    'ds1':'Сан-Себастьян Классический','ds2':'Сан-Себастьян с Нутеллой',
    'ds3':'Фисташковый чизкейк','ds4':'Баурсак в шоколаде','ds5':'Баурсак фисташковый',
    'ds6':'Баурсак со сгущенкой','ds7':'Шоколад Kazakhstan','ds8':'Бельгийские вафли',
    'ds9':'Арбузная нарезка',
    'dr1':'Coca Cola 245 ml','dr2':'Pepsi 245 ml','dr3':'7Up 250 ml',
    'dr4':'Mirinda 250 ml','dr5':'Kinza 250ml',
    'j1':'Айс-ти','j2':'Свежий морковный сок','j3':'Айран',
    'j4':'Апельсиновый сок','j5':'Свежий яблочный сок',
    'j6':'Концентрированное молоко','j7':'Вода',
    'cf1':'Эспрессо кофе','cf2':'Эспрессо Лонг','cf3':'Американо кофе',
    'cf4':'Капучино кофе','cf5':'Латте кофе','cf6':'Колд Брю','cf7':'Айс Американо',
    't1':'Чай с мятой','t2':'Чай с лимоном','t3':'Чай Карак',
    't4':'Ташкентский чай','t5':'Марокканский чай','t6':'Молочный Оолонго',
    't7':'Имбирный чай','t8':'Малиновый чай',
    't9':'Чайник черного чая','t10':'Чайник зеленого чая',
    'sc1':'Соус Нутелла','sc2':'Бельгийский шоколад','sc3':'Сгущенное молоко',
    'sc4':'Чесночный соус','sc5':'Йогурт','sc6':'Томатный соус',
}

# ─── БАЗА ДАННЫХ ──────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect("yurt_orders.db")

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER,
            username         TEXT,
            full_name        TEXT,
            timestamp        TEXT,
            total_price      REAL,
            fulfillment_type TEXT,
            items_json       TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id   INTEGER PRIMARY KEY,
            username      TEXT,
            full_name     TEXT,
            points        REAL    DEFAULT 0,
            orders_count  INTEGER DEFAULT 0,
            first_seen    TEXT,
            last_seen     TEXT
        )
    """)
    conn.commit()
    conn.close()
    logging.info("БД инициализирована.")

def upsert_user(telegram_id: int, username: str, full_name: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (telegram_id, username, full_name, points, orders_count, first_seen, last_seen)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username  = excluded.username,
            full_name = excluded.full_name,
            last_seen = excluded.last_seen
    """, (telegram_id, username, full_name, now, now))
    conn.commit()
    conn.close()

def add_points_and_order(telegram_id: int, total_price: float, fulfillment_type: str, items_json: str,
                          username: str, full_name: str):
    earned = round(total_price * CASHBACK_PCT, 2)
    now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn   = get_conn()
    c      = conn.cursor()
    c.execute("""
        INSERT INTO orders (user_id, username, full_name, timestamp, total_price, fulfillment_type, items_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (telegram_id, username, full_name, now, total_price, fulfillment_type, items_json))
    c.execute("""
        INSERT INTO users (telegram_id, username, full_name, points, orders_count, first_seen, last_seen)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username     = excluded.username,
            full_name    = excluded.full_name,
            points       = points + ?,
            orders_count = orders_count + 1,
            last_seen    = excluded.last_seen
    """, (telegram_id, username, full_name, earned, now, now, earned))
    conn.commit()
    conn.close()
    return earned

def get_user_data(telegram_id: int):
    conn = get_conn()
    c    = conn.cursor()
    c.execute("SELECT points, orders_count, full_name, username FROM users WHERE telegram_id = ?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"points": round(row[0], 2), "orders_count": row[1],
                "full_name": row[2], "username": row[3]}
    return {"points": 0, "orders_count": 0, "full_name": "", "username": ""}

# ─── REST API (aiohttp) ────────────────────────────────────────────────────────
async def api_get_user(request: web.Request):
    try:
        tg_id = int(request.match_info['telegram_id'])
    except (KeyError, ValueError):
        return web.json_response({"error": "bad id"}, status=400)

    data = get_user_data(tg_id)
    return web.json_response(data)

async def api_health(request: web.Request):
    return web.json_response({"status": "ok", "time": datetime.now().isoformat()})

def make_api_app():
    app = web.Application()
    async def cors_middleware(app, handler):
        async def middleware(request):
            if request.method == 'OPTIONS':
                resp = web.Response()
            else:
                resp = await handler(request)
            resp.headers['Access-Control-Allow-Origin']  = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return resp
        return middleware
    app.middlewares.append(cors_middleware)
    app.router.add_get('/api/health',            api_health)
    app.router.add_get('/api/user/{telegram_id}', api_get_user)
    return app

# ─── TELEGRAM HANDLERS ────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    u = message.from_user
    upsert_user(u.id, u.username or "", u.full_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
    ]])
    await message.answer(
        "Welcome to Yurt! Please choose your language:\n"
        "Добро пожаловать в Yurt! Пожалуйста, выберите язык:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("lang_"))
async def process_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    url = f"{BASE_WEBAPP_URL}?lang={lang_code}&v=81"

    btn_text = "🍽 Open Menu" if lang_code == 'en' else "🍽 Открыть меню"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    text = ("Great! Tap the button below to explore our menu:"
            if lang_code == 'en' else
            "Отлично! Нажмите кнопку «Открыть меню» внизу экрана:")
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        raw = message.web_app_data.data
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        data = json.loads(raw)

        # ── Клиент ──────────────────────────────────────────────────────────
        tg_user      = message.from_user
        tg_id        = tg_user.id
        full_name    = tg_user.full_name
        username_str = f"@{tg_user.username}" if tg_user.username else "—"
        tg_link      = f"<a href='tg://user?id={tg_id}'>{full_name}</a>"

        # ── Данные заказа ───────────────────────────────────────────────────
        customer_name  = data.get('customer_name') or data.get('name', full_name)
        customer_phone = data.get('phone_number')  or data.get('phone', '—')
        customer_addr  = data.get('location')      or data.get('address', '—')
        customer_time  = data.get('pickup_time')   or data.get('time',   'Как можно скорее')
        customer_comment = (data.get('comment') or '').strip()
        fulfillment    = data.get('order_type') or data.get('fulfillment', 'delivery')
        payment_method = data.get('payment_method', 'cash')
        user_lang      = data.get('lang', 'ru')

        subtotal_raw   = data.get('subtotal', 0)
        bonus_spent    = data.get('bonus_spent', 0)
        total_raw      = data.get('total_pay') or data.get('total', 0)

        try:    subtotal_val = float(str(subtotal_raw).replace(' SAR',''))
        except: subtotal_val = 0.0
        try:    total_val    = float(str(total_raw).replace(' SAR',''))
        except: total_val    = 0.0

        # ── Корзина ─────────────────────────────────────────────────────────
        cart_by_id  = data.get('cart', {})
        items_list  = data.get('items', [])
        display_cart = {}

        if cart_by_id and isinstance(cart_by_id, dict):
            for iid, qty in cart_by_id.items():
                name_ru = MENU_NAMES_RU.get(iid, iid)
                display_cart[name_ru] = qty
        elif items_list:
            for item in items_list:
                display_cart[item.get('name','Блюдо')] = item.get('qty', 1)

        # ── БД и Баллы ──────────────────────────────────────────────────────
        items_for_db = cart_by_id if cart_by_id else {i.get('name',''): i.get('qty',1) for i in items_list}
        earned_points = add_points_and_order(
            tg_id, total_val, fulfillment,
            json.dumps(items_for_db, ensure_ascii=False),
            tg_user.username or "", full_name
        )

        # ── Сообщение менеджерам ───────────────────────────────────────────
        total_qty = sum(display_cart.values())
        items_text = "".join(f"• {nm} × {qty}\n" for nm, qty in display_cart.items())

        prep_time = "15-20" if total_qty <= 2 else ("25-30" if total_qty <= 5 else "40-45")
        heavy = any(k in cart_by_id for k in ['k2','sn3','m4']) if cart_by_id else False
        if heavy and total_qty <= 5: prep_time = "35-40"
        load_warn = "⚠️ <b>ВЫСОКАЯ НАГРУЗКА КУХНИ!</b>\n" if (total_qty > 5 or heavy) else ""

        if fulfillment == 'pickup':
            pay_label  = "💵 Наличными на кассе" if payment_method == "cash" else "💳 Картой (Терминал)"
            fulf_label = "🛍️ САМОВЫВОЗ"
        else:
            pay_label  = "💵 Наличными курьеру" if payment_method == "cash" else "💳 Картой курьеру"
            fulf_label = "🛵 ДОСТАВКА"

        comment_block = f"💬 <b>Комментарий:</b> <u>{customer_comment}</u>\n\n" if customer_comment else ""
        bonus_block   = f"🎁 <b>Списано бонусов:</b> {bonus_spent} SAR\n" if bonus_spent else ""

        report = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ — {fulf_label} ({user_lang.upper()})</b>\n\n"
            f"👤 <b>Клиент:</b> {customer_name}\n"
            f"📱 <b>Telegram:</b> {tg_link} ({username_str})\n"
            f"📞 <b>Телефон:</b> <code>{customer_phone}</code>\n"
            f"📍 <b>Адрес/Получение:</b> {customer_addr}\n"
            f"⏱ <b>Время:</b> <b>{customer_time}</b>\n"
            f"💳 <b>Оплата:</b> {pay_label}\n\n"
            f"{comment_block}"
            f"📋 <b>Состав заказа:</b>\n{items_text}\n"
            f"👨‍🍳 <b>Время готовки:</b> <b>{prep_time} мин</b>\n"
            f"{load_warn}\n"
            f"───────────────\n"
            f"💰 Блюда: {subtotal_val:.0f} SAR\n"
            f"{bonus_block}"
            f"💰 <b>ИТОГО К ОПЛАТЕ: {total_val:.0f} SAR</b>\n"
            f"⭐ Начислено бонусов клиенту: <b>+{earned_points} SAR</b>"
        )

        btns = [[InlineKeyboardButton(
            text="👨‍🍳 Принять в работу",
            callback_data=f"status_accept_{tg_id}_{user_lang}_{fulfillment}"
        )]]
        if fulfillment == 'delivery' and customer_addr and "http" in customer_addr:
            btns.insert(0, [InlineKeyboardButton(text="📍 Маршрут в картах", url=customer_addr)])

        await bot.send_message(
            chat_id=ORDERS_GROUP_ID, text=report,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
        )

        # ── Ответ клиенту ───────────────────────────────────────────────────
        if user_lang == 'en':
            ok_text = (
                f"✨ <b>Thank you, {customer_name}!</b>\n\n"
                f"Your order has been placed and sent to the kitchen.\n"
                f"Type: <b>{fulfillment.upper()}</b> · Time: <b>{customer_time}</b>\n\n"
                f"⭐ You earned <b>{earned_points} SAR</b> in bonus points!"
            )
            sup_btn = "💬 Contact Support"
        else:
            ok_text = (
                f"✨ <b>Спасибо, {customer_name}!</b>\n\n"
                f"Заказ оформлен и передан на кухню.\n"
                f"Тип: <b>{fulf_label}</b> · Время: <b>{customer_time}</b>\n\n"
                f"⭐ Вам начислено <b>{earned_points} SAR</b> бонусных баллов!"
            )
            sup_btn = "💬 Связаться с поддержкой"

        await message.answer(
            ok_text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=sup_btn, url=MANAGER_SUPPORT_URL)
            ]])
        )

    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@dp.callback_query(F.data.startswith("status_"))
async def handle_status(callback: types.CallbackQuery):
    parts       = callback.data.split("_")
    action      = parts[1]
    client_id   = parts[2]
    user_lang   = parts[3] if len(parts) > 3 else 'ru'
    fulfillment = parts[4] if len(parts) > 4 else 'delivery'
    manager     = callback.from_user.first_name
    cur_text    = callback.message.text or ""

    maps_btn = None
    if callback.message.reply_markup:
        for row in callback.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.url and "maps" in btn.url:
                    maps_btn = btn; break

    if action == "accept":
        new_text = f"{cur_text}\n\n👨‍🍳 <b>Принял в работу: {manager}</b>"
        if fulfillment == 'pickup':
            nxt_txt  = "🛍️ Готов к выдаче"
            nxt_cb   = f"status_ready_{client_id}_{user_lang}_{fulfillment}"
        else:
            nxt_txt  = "🛵 Передать курьеру"
            nxt_cb   = f"status_delivery_{client_id}_{user_lang}_{fulfillment}"

        btns = [[InlineKeyboardButton(text=nxt_txt, callback_data=nxt_cb)]]
        if maps_btn: btns.insert(0, [maps_btn])
        await callback.message.edit_text(new_text, parse_mode="HTML",
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
        client_msg = (
            "👨‍🍳 <b>Status Update:</b>\nYour order has been accepted and is being prepared!"
            if user_lang == 'en' else
            "👨‍🍳 <b>Обновление статуса:</b>\nВаш заказ принят шефом и уже готовится на кухне!"
        )

    elif action == "delivery":
        new_text = f"{cur_text}\n\n🛵 <b>Передан курьеру!</b>"
        btns     = [[maps_btn]] if maps_btn else []
        await callback.message.edit_text(new_text, parse_mode="HTML",
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=btns) if btns else None)
        client_msg = (
            "🛵 <b>Your order is on its way!</b>\nThe courier is heading to your address!"
            if user_lang == 'en' else
            "🛵 <b>Ваш заказ уже в пути!</b>\nКурьер направляется по вашему адресу!"
        )

    elif action == "ready":
        new_text = f"{cur_text}\n\n✅ <b>Готов к выдаче в ресторане!</b>"
        await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
        map_btn_txt = "📍 Open route" if user_lang == 'en' else "📍 Открыть маршрут"
        client_msg = (
            f"🛍️ <b>Your order is ready for pickup!</b>\n\n{RESTAURANT_ADDRESS}"
            if user_lang == 'en' else
            f"🛍️ <b>Ваш заказ готов к выдаче!</b>\n\n{RESTAURANT_ADDRESS}"
        )
        try:
            await bot.send_message(int(client_id), client_msg, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text=map_btn_txt, url=RESTAURANT_MAPS_URL)
                ]]))
        except Exception as e:
            logging.error(f"Не удалось уведомить клиента: {e}")
        await callback.answer()
        return
    else:
        await callback.answer()
        return

    try:
        await bot.send_message(int(client_id), client_msg, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось уведомить клиента: {e}")
    await callback.answer()

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.chat.id != ORDERS_GROUP_ID:
        return

    args   = message.text.split()
    period = "week" if len(args) > 1 and args[1].lower() in ["week","неделя"] else "day"

    try:
        conn = get_conn(); c = conn.cursor(); now = datetime.now()
        if period == "day":
            filt   = f"{now.strftime('%Y-%m-%d')}%"
            title  = "за сегодня"
            c.execute("SELECT COUNT(*), SUM(total_price), MAX(timestamp) FROM orders WHERE timestamp LIKE ?", (filt,))
        else:
            since  = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            title  = "за последние 7 дней"
            c.execute("SELECT COUNT(*), SUM(total_price), MAX(timestamp) FROM orders WHERE timestamp >= ?", (since,))

        count, total_sum, last_ts = c.fetchone()
        if not count:
            await message.reply(f"📊 <b>Статистика {title}</b>\n\nЗаказов пока нет.", parse_mode="HTML")
            conn.close(); return

        total_sum = total_sum or 0
        avg       = total_sum / count

        last_str = "—"
        if last_ts:
            diff = now - datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
            m    = int(diff.total_seconds() // 60)
            last_str = f"{m} мин назад" if m < 60 else f"{m//60} ч {m%60} мин назад"

        if period == "day":
            c.execute("SELECT items_json FROM orders WHERE timestamp LIKE ?", (filt,))
        else:
            c.execute("SELECT items_json FROM orders WHERE timestamp >= ?", (since,))

        dish_counts = {}
        for (ij,) in c.fetchall():
            try:
                for iid, qty in json.loads(ij).items():
                    nm = MENU_NAMES_RU.get(iid, iid)
                    dish_counts[nm] = dish_counts.get(nm, 0) + qty
            except: pass

        top = sorted(dish_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_text = "".join(f"{i+1}. {nm} — {qty} шт\n" for i,(nm,qty) in enumerate(top)) or "Нет данных\n"

        c.execute("""
            SELECT full_name, COUNT(*) as cnt, SUM(total_price) as rev
            FROM orders WHERE """ + ("timestamp LIKE ?" if period=="day" else "timestamp >= ?") + """
            GROUP BY user_id ORDER BY cnt DESC LIMIT 3
        """, (filt if period=="day" else since,))
        top_clients = c.fetchall()
        clients_text = "".join(f"• {fn or '—'}: {cnt} заказ(ов) / {rev:.0f} SAR\n"
                               for fn,cnt,rev in top_clients) or "Нет данных\n"
        conn.close()

        report = (
            f"📊 <b>Статистика {title}</b>\n\n"
            f"🛒 <b>Заказов:</b> {count}\n"
            f"💰 <b>Выручка:</b> {total_sum:.0f} SAR\n"
            f"🧾 <b>Средний чек:</b> {avg:.0f} SAR\n"
            f"⏳ <b>Последний заказ:</b> {last_str}\n\n"
            f"🏆 <b>Топ блюд:</b>\n{top_text}\n"
            f"👥 <b>Активные клиенты:</b>\n{clients_text}"
        )
        await message.reply(report, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка статистики: {e}", exc_info=True)
        await message.reply("Не удалось загрузить статистику.")

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────
async def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    init_db()

    api_app    = make_api_app()
    runner     = web.AppRunner(api_app)
    await runner.setup()
    site       = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()
    logging.info(f"API-сервер запущен на порту {API_PORT}")

    while True:
        try:
            logging.info("Бот запускается...")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            logging.error(f"Сбой: {e}. Рестарт через 5 сек...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())