import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from random import randint


class VKInputOutputClass:
    def __init__(self):
        with open('vk_community_data.txt', 'r') as data:
            self.community_data = (data.readline().strip(), int(data.readline()))
        self.session = vk_api.VkApi(token=self.community_data[0])
        self.long_poll = None

    def start(self):
        self.long_poll = VkBotLongPoll(self.session, self.community_data[1])

    def send_message(self, user_id, message):
        self.session.get_api().messages.send(user_id=user_id, message=message, random_id=randint(0, 2 ** 64))

    def get_user(self, user_id):
        user_info = self.session.method('users.get', {'user_ids': user_id})
        return user_info[0]['first_name'], user_info[0]['last_name']


if __name__ == '__main__':
    pass
