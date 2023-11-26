import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from random import randint

TOKEN = 'vk1.a.qOQPyAdJ_Z5WwjzbNl_WFUq2P05QGpwj-537I7vwLTneH1Fz06BBEslq0_rbUGJFabRakR9V-pL7dzhhx6qCeHA-AP2wNndJTFHYQ7sKmPyiAB05KWIkfmH4G_Gl9luw3qqe8UvwB6tTTaojNW1EcIHjgP8uX5Z89ppE5Mv2cpaWrEmrWtD9b9GC1ulJ_viLiTwOfjTcBd4mqifQqazVZw'
GROUP_ID = 219645807


class VKInputOutputClass:
    def __init__(self):
        self.session = vk_api.VkApi(token=TOKEN)
        self.long_poll = None

    def start(self):
        self.long_poll = VkBotLongPoll(self.session, GROUP_ID)

    def send_message(self, user_id, message):
        self.session.get_api().messages.send(user_id=user_id, message=message, random_id=randint(0, 2 ** 64))

    def get_user(self, user_id):
        user_info = self.session.method('users.get', {'user_ids': user_id})
        return user_info[0]['first_name'], user_info[0]['last_name']


if __name__ == '__main__':
    pass
