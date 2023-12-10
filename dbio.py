import sqlite3

database = 'data.db'
table = 'top'
columns = ['user_id', 'nick', 'rating']


class DBInputOutputClass:
    def __init__(self):
        self.connect = None
        self.cursor = None

    def start(self):
        self.connect = sqlite3.connect(database)
        self.cursor = self.connect.cursor()

    def get_everything(self):
        return list(self.cursor.execute(f'''SELECT * FROM {table}'''))

    def update(self, search_column_number, search_value, update_column_number, update_value):
        self.cursor.execute(f'''UPDATE {table}
            SET {columns[update_column_number]} = {repr(update_value)}
            WHERE {columns[search_column_number]} = {repr(search_value)}''')
        self.connect.commit()

    def get(self, search_column_number, search_value, return_column_number):
        try:
            return next(self.cursor.execute(f'''SELECT {columns[return_column_number]}
                FROM {table} WHERE {columns[search_column_number]} = {repr(search_value)}'''))[0]
        except StopIteration:
            return None

    def insert(self, value_1, value_2, value_3):
        self.cursor.execute(f'''INSERT
            INTO {table}({columns[0]}, {columns[1]}, {columns[2]})
            VALUES({repr(value_1)}, {repr(value_2)}, {repr(value_3)})''')
        self.connect.commit()


if __name__ == '__main__':
    pass
