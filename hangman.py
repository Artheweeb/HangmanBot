from random import choice

word_list = list(map(lambda x: x.strip(), open('supporting txts/russian_nouns.txt', 'r', encoding='utf-8').readlines()))
alphabet = open('supporting txts/russian_alphabet.txt', 'r', encoding='utf-8').readline()
allowed_symbols = open('supporting txts/allowed_symbols.txt', 'r').readline()


class HangmanWord:
    def __init__(self, argument, random):
        if random:
            self.clean = choice(tuple(filter(lambda x: len(x) >= argument, word_list)))
        else:
            self.clean = argument
        self.size = len(self.clean)
        self.hidden = ''.join(map(lambda x: '_' if x.isalpha() else x, self.clean))
        self.progress = list(map(lambda x: not x.isalpha(), self.clean))

    def try_symbol(self, symbol):
        to_return = False
        for i in range(self.size):
            if self.clean[i].lower() == symbol.lower():
                self.progress[i] = True
                to_return = True
        return to_return

    def current(self):
        return ''.join([self.clean[i] if self.progress[i] else self.hidden[i] for i in range(self.size)])

    def done(self):
        return all(self.progress)


class HangmanSession:
    def __init__(self):
        self.word = None
        self.mistake_count = 7
        self.mistakes_left = None
        self.wrong = []
        self.right = []

    def start_chosen(self, word):
        self.word = HangmanWord(word, random=False)
        self.mistakes_left = self.mistake_count

    def start_random(self, minimal_length=15):
        self.word = HangmanWord(minimal_length, random=True)
        self.mistakes_left = self.mistake_count

    def result(self):
        if self.word.done():
            return 1
        if not self.mistakes_left:
            return -1
        return 0

    def step(self, symbol):
        if not self.word.try_symbol(symbol):
            self.mistakes_left -= 1
            self.wrong += [symbol.lower()]
            self.wrong.sort()
            return False
        self.right += [symbol.lower()]
        self.right.sort()
        return True


if __name__ == '__main__':
    pass
