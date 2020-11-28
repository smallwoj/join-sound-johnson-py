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

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS join_sounds ' + 
            '(' + 
            ', '.join([
                'id, INT AUTO_INCREMENT PRIMARY KEY',
                'discord_id, VARCHAR(255) UNIQUE',
                'file_path, VARCHAR(255)',
            ]) + ')'
        )
        cursor.execute('CREATE INDEX discord_id ON join_sounds (discord_id)')
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
        file_name = 'joinsound.mp3'
        sound.download(path, file_name)
        if self.has_sound(discord_id):
            query = f"UPDATE join_sounds SET path='{os.path.join(path, file_name)}' WHERE discord_id='{discord_id}'"
        else:
            query = f"INSERT INTO join_sounds (discord_id, path) VALUES ('{discord_id}', '{os.path.join(path, file_name)}')"
        cursor = self.db.cursor()
        cursor.execute(query)
        cursor.close()
