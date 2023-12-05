from hangman import HangmanSession, allowed_symbols
from vkio import VKInputOutputClass, VkBotEventType
from dbio import DBInputOutputClass

NO_ENEMY, AWAITING, FIGHTING = 'no_enemy', 'awaiting', 'fighting'
max_nick_size = 20
command_list = [
    'help', 'register', 'challenge',
    'try', 'rating', 'surrender', 'nick'
]


def text(address):
    return ''.join(open(f'messages/{address}.txt', 'r', encoding='utf-8').readlines())


class User:
    def __init__(self):
        self.condition = NO_ENEMY
        self.enemy = None
        self.bet = 0
        self.game_session = None
        self.awaiting = set()

    def set(self, condition, enemy, bet, game_session):
        self.condition = condition
        self.enemy = enemy
        self.bet = bet
        self.game_session = game_session


class Interface:
    def __init__(self):
        self.vk_tool = VKInputOutputClass()
        self.game = HangmanSession()
        self.db_tool = DBInputOutputClass()
        self.users = dict()

    def main_cycle(self):
        self.vk_tool.start()
        self.db_tool.start()
        for event in self.vk_tool.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_ALLOW:
                self.vk_tool.send_message(event.object['from_id'], text('welcome message'))
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.process_command(event.object.message['from_id'], event.object.message['text'])

    def process_command(self, user, message):
        command = message.split()
        if not self.db_tool.get(0, user, 1) and command[0] != '/register':
            self.vk_tool.send_message(user, text('for_unregistered'))
            return
        if user not in self.users:
            self.users[user] = User()
        match command[0]:
            case '/challenge':
                self.process_challenge(user, command)
            case '/register':
                self.process_register(user, command)
            case '/help':
                self.process_help(user, command)
            case '/nick':
                self.process_nick(user, command)
            case '/surrender':
                self.process_surrender(user, command)
            case '/try':
                self.process_try(user, command)
            case '/rating':
                self.process_rating(user, command)
            case _:
                self.wrong_input(user)

    def verify_nick(self, user, nick):
        if len(nick) > max_nick_size:
            return -1
        for symbol in nick:
            if symbol.lower() not in allowed_symbols:
                return -1
        if self.user_exist_check(nick):
            return 1
        self.db_tool.insert(user, nick, 10)
        return 0

    def end_game(self, user, result):  # 1 - победил решающий, 0 - победил задавший
        winner = user
        loser = self.users[user].enemy
        bet = self.users[user].bet
        if not result:
            winner, loser = loser, winner
        win_res = self.db_tool.get(0, winner, 2)
        los_res = self.db_tool.get(0, loser, 2)
        self.db_tool.update(0, winner, 2, win_res + bet)
        self.db_tool.update(0, loser, 2, min(los_res - bet, 10))
        self.users[user].condition = NO_ENEMY
        self.users[user].enemy = None
        self.users[user].bet = 0
        self.users[user].game_session = None
        self.vk_tool.send_message(winner, f'Вы выиграли, ваш рейтинг теперь: {win_res + bet}')
        self.vk_tool.send_message(loser, f'Вы проиграли, ваш рейтинг теперь: {min(los_res - bet, 10)}')

    def wrong_input(self, user):
        self.vk_tool.send_message(user, text('wrong_input'))

    def user_exist_check(self, nick):
        return bool(self.db_tool.get(1, nick, 0))

    def get_game_condition(self, user):
        message = ''
        message += f'Слово: {self.users[user].game_session.word.current()}\n'
        message += f'Угадано: {" ".join(self.users[user].game_session.right)}\n'
        message += f'Ошибки: {" ".join(self.users[user].game_session.wrong)}\n'
        message += f'Осталось прав на ошибку: {self.users[user].game_session.mistakes_left}'
        return message

    def correct_user_check(self, user, command):
        if user == self.db_tool.get(1, command[2], 0):
            self.vk_tool.send_message(user, text('no_selfcest'))
            return True
        if not self.user_exist_check(command[2]):
            self.vk_tool.send_message(user, 'Такой пользователь в системе не существует')
            return True

    def process_help(self, user, command):
        match len(command):
            case 1:
                self.vk_tool.send_message(user, text('global_help'))
            case 2:
                if command[1] in command_list:
                    self.vk_tool.send_message(user, text(f'commands/{command[1]}'))
                else:
                    self.wrong_input(user)
            case _:
                self.wrong_input(user)

    def process_register(self, user, command):
        if self.db_tool.get(0, user, 0):
            self.vk_tool.send_message(user, f'Вы уже зарегистрированы, ваш ник: {self.db_tool.get(0, user, 1)}')
            return
        if len(command) != 2:
            self.wrong_input(user)
            return
        match self.verify_nick(user, command[1]):
            case -1:
                self.vk_tool.send_message(user, text('unusable_nick'))
            case 0:
                self.vk_tool.send_message(user, text('correct_nick'))
            case 1:
                self.vk_tool.send_message(user, 'Данный ник уже используется, предложите новый')

    def process_challenge(self, user, command):
        if len(command) < 3:
            self.wrong_input(user)
            return
        match command[1]:
            case 'offer':
                self.process_challenge_offer(user, command)
            case 'accept':
                self.process_challenge_accept(user, command)
            case 'reject':
                self.process_challenge_reject(user, command)
            case 'cancel':
                self.process_challenge_cancel(user, command)
            case _:
                self.wrong_input(user)

    def process_challenge_offer(self, user, command):
        if len(command) < 4:
            self.wrong_input(user)
            return
        if self.correct_user_check(user, command):
            return
        if self.users[user].condition != NO_ENEMY:
            self.vk_tool.send_message(user, text('busy_no_offer'))
            return
        prey = self.db_tool.get(1, command[2], 0)
        try:
            bet = int(command[3])
        except ValueError:
            self.wrong_input(user)
            return
        if bet < 0 or bet > self.db_tool.get(0, user, 2):
            self.vk_tool.send_message(user, 'Такая ставка не может быть сделана')
            return
        game_session = HangmanSession()
        if len(command) == 4:
            game_session.start_random()
        else:
            game_session.start_chosen(' '.join(command[4:]))
        if prey not in self.users:
            self.users[prey] = User()
        if self.users[prey].condition != NO_ENEMY:
            self.vk_tool.send_message(user, 'Пользователь недоступен, вызовите его позже')
            return
        for awaiting in self.users[prey].awaiting:
            if user == awaiting[2]:
                self.vk_tool.send_message(user, 'Вы уже бросили вызов этому пользователю')
                return
        self.users[prey].awaiting.add((game_session, bet, user))
        self.users[user].condition = AWAITING
        self.vk_tool.send_message(prey, f'Пользователь {self.db_tool.get(0, user, 1)} бросил вам вызов\nСтавка: {bet}\nСлово: {game_session.word.hidden}')
        self.vk_tool.send_message(user, f'Вы успешно бросили вызов пользователю {self.db_tool.get(0, prey, 1)}, ожидайте ответа')

    def process_challenge_accept(self, user, command):
        if len(command) != 3:
            self.wrong_input(user)
            return
        if self.correct_user_check(user, command):
            return
        if self.users[user].condition != NO_ENEMY:
            self.vk_tool.send_message(user, text('busy_no_accept'))
            return
        hunter = self.db_tool.get(1, command[2], 0)
        for awaiting in self.users[user].awaiting:
            if hunter == awaiting[2]:
                self.users[user].awaiting.remove(awaiting)
                self.vk_tool.send_message(user, f'Вы успешно приняли вызов пользователя {self.db_tool.get(0, hunter, 1)}')
                self.vk_tool.send_message(hunter, f'{self.db_tool.get(0, user, 1)} принял ваш вызов')
                self.users[user].set(FIGHTING, hunter, awaiting[1], awaiting[0])
                self.users[hunter].condition = NO_ENEMY
                return
        self.vk_tool.send_message(user, f'{self.db_tool.get(0, hunter, 1)} не бросал вам вызов')

    def process_challenge_reject(self, user, command):
        if len(command) != 3:
            self.wrong_input(user)
            return
        if self.correct_user_check(user, command):
            return
        hunter = self.db_tool.get(1, command[2], 0)
        for awaiting in self.users[user].awaiting:
            if hunter == awaiting[2]:
                self.users[user].awaiting.remove(awaiting)
                self.users[hunter].condition = NO_ENEMY
                self.vk_tool.send_message(user, f'Вы успешно отклонили вызов пользователя {self.db_tool.get(0, hunter, 1)}')
                self.vk_tool.send_message(hunter, f'{self.db_tool.get(0, user, 1)} отклонил ваш вызов')
                return
        self.vk_tool.send_message(user, f'{self.db_tool.get(0, hunter, 1)} не бросал вам вызов')

    def process_challenge_cancel(self, user, command):
        if len(command) != 3:
            self.wrong_input(user)
            return
        if self.correct_user_check(user, command):
            return
        prey = self.db_tool.get(1, command[2], 0)
        for awaiting in self.users[prey].awaiting:
            if user == awaiting[2]:
                self.vk_tool.send_message(user, f'Вы отменили вызов игроку {command[2]}')
                self.vk_tool.send_message(prey, f'Пользователь {self.db_tool.get(0, user,  1)} отменил свой вызов')
                self.users[prey].awaiting.remove(awaiting)
                self.users[user].condition = NO_ENEMY
                return
        self.vk_tool.send_message(user, f'Вы не бросали вызов игроку {command[2]}')

    def process_nick(self, user, command):
        match len(command):
            case 1:
                self.vk_tool.send_message(user, f'Ваш ник: {self.db_tool.get(0, user, 1)}')
            case 2:
                if self.db_tool.get(0, command[1], 1):
                    self.vk_tool.send_message(user, f"{text('found_by_id')} {self.db_tool.get(0, command[1], 1)}")
                else:
                    self.vk_tool.send_message(user, text('not_found_by_id'))
            case 3:
                for member in self.db_tool.get_everything():
                    name, surname = command[1:]
                    if self.vk_tool.get_user(member[0]) == (name, surname):
                        self.vk_tool.send_message(user, f"{text('found_by_name')} {member[1]}")
                        return
                self.vk_tool.send_message(user, text('not_found_by_name'))

    def process_surrender(self, user, command):
        if len(command) != 1:
            self.wrong_input(user)
            return
        if self.users[user].condition != FIGHTING:
            self.vk_tool.send_message(user, 'Вам некому сдаваться')
            return
        hunter = self.users[user].enemy
        self.vk_tool.send_message(user, 'Вы сдались')
        self.vk_tool.send_message(hunter, f'{self.db_tool.get(0, user, 1)} сдался')
        self.end_game(user, False)

    def process_rating(self, user, command):
        match len(command):
            case 1:
                message = ''
                rating = sorted(self.db_tool.get_everything(), key=lambda row: row[2], reverse=True)
                for number, row in enumerate(rating, start=1):
                    message += f'{number}) {row[1]} : {row[2]}\n'
                self.vk_tool.send_message(user, message)
            case 2:
                message = ''
                try:
                    limit = int(command[2])
                except ValueError:
                    self.wrong_input(user)
                    return
                rating = sorted(self.db_tool.get_everything(), key=lambda row: row[2], reverse=True)
                for number, row in enumerate(rating, start=1):
                    if number <= limit or row[0] == user:
                        message += f'{number}) {row[1]} : {row[2]}\n'
                self.vk_tool.send_message(user, message)
            case _:
                self.wrong_input(user)

    def process_try(self, user, command):
        if len(command) != 2:
            self.wrong_input(user)
            return
        if self.users[user].condition != FIGHTING:
            self.vk_tool.send_message(user, 'Вы не участвуете в игре, чтобы пробовать буквы')
            return
        if len(command[1]) != 1:
            self.wrong_input(user)
            return
        if self.users[user].game_session.step(command[1]):
            self.vk_tool.send_message(user, f'Вы угадали букву\n{self.get_game_condition(user)}')
        else:
            self.vk_tool.send_message(user, f'Вы не угадали букву\n{self.get_game_condition(user)}')
        match self.users[user].game_session.result():
            case 1:
                self.vk_tool.send_message(user, 'Вы угадали слово')
                self.vk_tool.send_message(self.users[user].enemy, f'{self.db_tool.get(0, user, 1)} угадал слово')
                self.end_game(user, True)
            case -1:
                self.vk_tool.send_message(user, 'Вы не угадали слово, права на ошибку закончились')
                self.vk_tool.send_message(self.users[user].enemy, f'{self.db_tool.get(0, user, 1)} не угадал слово')
                self.end_game(user, False)


if __name__ == '__main__':
    server = Interface()
    server.main_cycle()
