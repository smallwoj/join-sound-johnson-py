import mysql.connector
from pytube import Stream
import os
class Database:
    def __init__(self):
        self.db = mysql.connector.connect(
            host='localhost',
            user='joinbot_user',
            password='123456',
            database='joinbot'
        )
        cursor = self.db.cursor()
        cursor.execute('SHOW TABLES')
        rows = cursor.fetchall()
        rows = list(map(lambda x: x[0], rows))
        cursor.close()
        if 'join_sounds' not in rows:
            self.create_table()

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS join_sounds ' + 
            '(' + 
            ', '.join([
                'id INT AUTO_INCREMENT PRIMARY KEY',
                'discord_id VARCHAR(255) UNIQUE',
                'file_path VARCHAR(255)',
            ]) + ')'
        )
        cursor.execute('CREATE INDEX discord_idx ON join_sounds (discord_id)')
        cursor.close()

    def has_sound(self, discord_id: str) -> bool:
        cursor = self.db.cursor()
        cursor.execute(f"SELECT file_path FROM join_sounds WHERE discord_id={discord_id}")
        rows = cursor.fetchall()
        cursor.close()
        found = False
        if rows:
            path = rows[0][0]
            if os.path.exists(path):
                found = True
        return found
    
    def get_sound(self, discord_id: str):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT file_path FROM join_sounds WHERE discord_id={discord_id}")
        rows = cursor.fetchall()
        cursor.close()
        if rows:
            path = rows[0][0]
            return path
        else:
            raise Exception("No join sound found!")

    def upload_sound(self, discord_id: str, sound: Stream):
        path = os.path.join('media', f'{discord_id}')
        file_name = 'joinsound'
        sound.download(path, file_name)
        full_path = sound.get_file_path(output_path=path, filename=file_name)
        cursor = self.db.cursor()
        if self.has_sound(discord_id):
            query = f"UPDATE join_sounds SET file_path='{full_path}' WHERE discord_id='{discord_id}'"
            cursor.execute(query)
        else:
            query = f"INSERT INTO join_sounds (discord_id, file_path) VALUES (%s, %s)"
            val = (discord_id, full_path)
            cursor.execute(query, val)
        cursor.close()
        self.db.commit()
