import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import json, random, sqlite3, time

# ===== НАСТРОЙКИ =====
TOKEN = "vk1.a.gQFcsQKruH5TchxgUWh13DsF_6Gz1ELhYd1NoL6Y4nPX-WsQYskpp4llV6fBNpySgogQp6zlky8j3wXRQLqNufPpLReUV1W_ew0KuQHAcXwuQ_kbPHOS3TfXnxr3mKPw72WrPtnV62LeLWxkQjbWlJMszWUDU_ygov2CN7O-RQLe6sAxEmGNbJ8DlYNysnwLyrsz9xXCUQ5g11Vs0qjCXPUTllPaLfRXmlty3U2ZFvM"
ADMIN_ID = 200005093141
GROUP_ID = 242296265 
GROUP_LINK = "https://vk.com/club242296265"

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()

waiting_mode = {}

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('super_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, warns INTEGER, ban_until INTEGER)''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('super_bot.db')
    c = conn.cursor()
    c.execute("SELECT warns, ban_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id, warns, ban_until) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        row = (0, 0)
    conn.close()
    return row

init_db()

# --- ПРОВЕРКА ПОДПИСКИ ---
def is_subscribed(user_id):
    try:
        res = vk.groups.isMember(group_id=GROUP_ID, user_id=user_id)
        return bool(res)
    except:
        return False

def send(peer_id, text):
    kb = {
        "one_time": False, 
        "buttons": [
            [{"action": {"type": "text", "label": "📸 Создать ссылку"}, "color": "positive"}],
            [{"action": {"type": "text", "label": "📸 Несколько фото"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "🕵️ Мафию"}, "color": "secondary"}]
        ]
    }
    try:
        if len(text) > 4000:
            text = text[:4000] + "\n... (обрезано)"
        vk.messages.send(peer_id=peer_id, message=text, keyboard=json.dumps(kb, ensure_ascii=False), random_id=random.randint(1, 2**31))
    except Exception as e:
        print("Ошибка отправки:", e)

print("БОТ ЗАПУЩЕН!")

try:
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            peer_id = event.peer_id
            user_id = peer_id 
            text = event.text.lower().strip()

            # === СТАТИСТИКА ===
            if text == "стата" and user_id == ADMIN_ID:
                conn = sqlite3.connect('super_bot.db')
                c = conn.cursor()
                c.execute("SELECT user_id, warns, ban_until FROM users")
                all_users = c.fetchall()
                conn.close()
                
                stats_text = "📊 **Статистика:**\n\n"
                for u_id, w, b_until in all_users:
                    if w > 0 or b_until > time.time():
                        ban_status = "Нет" if b_until == 0 or b_until < time.time() else "ДА (ЧС)"
                        stats_text += f"👤 ID: {u_id}\n⚠️ Варны: {w}/3\n⛔ ЧС: {ban_status}\n\n"
                send(peer_id, stats_text)
                continue

            # === ПРОВЕРКА НА ЧС ===
            warns, ban_until = get_user_data(user_id)
            current_time = int(time.time())

            if ban_until > current_time:
                days_left = (ban_until - current_time) // 86400
                hours_left = ((ban_until - current_time) % 86400) // 3600
                send(peer_id, f"⛔ **Вы заблокированы в боте!**\nОсталось: {days_left} дн. {hours_left} ч.")
                continue

            # === ПРОВЕРКА ПОДПИСКИ ===
            if not is_subscribed(user_id):
                sub_text = (
                    f"🔒 **Доступ ограничен!**\n\n"
                    f"Чтобы пользоваться ботом, вы должны быть подписаны на наше сообщество.\n\n"
                    f"👉 Подпишитесь: {GROUP_LINK}\n\n"
                    f"После подписки напишите любое сообщение боту."
                )
                send(peer_id, sub_text)
                continue

            # === ОБРАБОТКА ФОТО ===
            if peer_id in waiting_mode:
                try:
                    msg_info = vk.messages.getById(message_ids=event.message_id)
                    items = msg_info.get('items', [])
                    
                    if items:
                        attachments = items[0].get('attachments', [])
                        photo_links = []
                        
                        for attach in attachments:
                            if attach.get('type') == 'photo':
                                sizes = attach['photo'].get('sizes', [])
                                if sizes:
                                    photo_links.append(sizes[-1]['url'])
                        
                        if photo_links:
                            mode = waiting_mode[peer_id]
                            if mode == 'one':
                                final_text = f"🌿 **Ваша фотография загружена!**\n\n🔗 Ссылка: {photo_links[0]}\n\n👇 Скопируйте ссылку."
                                send(peer_id, final_text)
                            else:
                                final_text = "🌿 **Ваши фотографии загружены!**\n\n"
                                for i, link in enumerate(photo_links, 1):
                                    final_text += f"🔗 Фото {i}: {link}\n\n"
                                send(peer_id, final_text)
                except Exception as e:
                    print("Ошибка при обработке фото:", e)
                
                if peer_id in waiting_mode:
                    del waiting_mode[peer_id]
                continue

            # === ЛОГИКА КНОПОК ===
            if "мафию" in text:
                send(peer_id, "🕵️ **МАФИЯ**\nНапиши в беседе 'Создать мафия', чтобы начать!")
            elif "несколько фото" in text:
                waiting_mode[peer_id] = 'multi'
                send(peer_id, "📸 Отправь мне сразу несколько фото.")
            elif "создать ссылку" in text:
                waiting_mode[peer_id] = 'one'
                send(peer_id, "📸 Отправь мне одно фото.")
            elif text == "начать" or text == "start":
                send(peer_id, "Привет! Выбирай действие на кнопках внизу 👇")
            else:
                send(peer_id, "Жми кнопки внизу 👇")

except Exception as e:
    print("КРИТИЧЕСКАЯ ОШИБКА:", e)
