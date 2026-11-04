import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

TOKEN = "vk1.a.gQFcsQKruH5TchxgUWh13DsF_6Gz1ELhYd1NoL6Y4nPX-WsQYskpp4llV6fBNpySgogQp6zlky8j3wXRQLqNufPpLReUV1W_ew0KuQHAcXwuQ_kbPHOS3TfXnxr3mKPw72WrPtnV62LeLWxkQjbWlJMszWUDU_ygov2CN7O-RQLe6sAxEmGNbJ8DlYNysnwLyrsz9xXCUQ5g11Vs0qjCXPUTllPaLfRXmlty3U2ZFvM"

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()

print("===== ТЕСТОВЫЙ БОТ ЗАПУЩЕН =====")

try:
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            peer_id = event.peer_id
            text = event.text.lower().strip()
            print(f"ПОЛУЧЕНО: {text}")
            
            vk.messages.send(
                peer_id=peer_id,
                message="Я живой! Ты написал: " + text,
                random_id=0
            )
except Exception as e:
    print("ОШИБКА:", e)
