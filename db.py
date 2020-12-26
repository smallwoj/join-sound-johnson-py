import mysql.connector
from pytube import Stream
import os
class Database:
    def __init__(self):
        """
        Initializes the database.
        """
        self.db = None
        cursor = self.cursor()

        # Create the join_sounds database table if not present
        cursor.execute('SHOW TABLES')
        rows = cursor.fetchall()
        rows = list(map(lambda x: x[0], rows))
        cursor.close()
        if 'join_sounds' not in rows:
            self.create_table()

    def cursor(self) -> mysql.connector.connection.MySQLCursor:
        """
        Retrieves a cursor for the database, reconnecting if it is disconnected

        :return: A database cursor to the current database
        """
        while not self.db or not self.db.is_connected():
            self.db = mysql.connector.connect(
                host='localhost',
                user='joinbot_user',
                password='123456',
                database='joinbot'
            )
        return self.db.cursor()

    def create_table(self):
        """
        Creates a join sound table and sets indexes for the discord id.
        """
        cursor = self.cursor()
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
        """
        Checks if the user with the given discord id has a sound in the database.

        :param discord_id: The discord user id to check
        :return: True if it has a sound in the database, false otherwise.
        """
        cursor = self.cursor()
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
        """
        Retrieves the join sound from the database

        :param discord_id: Discord id of the sound to retrieve
        :raises Exception: If the join sound was not found
        :return: The file path to the sound.
        """
        cursor = self.cursor()
        cursor.execute(f"SELECT file_path FROM join_sounds WHERE discord_id={discord_id}")
        rows = cursor.fetchall()
        cursor.close()
        if rows:
            path = rows[0][0]
            return path
        else:
            raise Exception("No join sound found!")

    def upload_sound(self, discord_id: str, sound: Stream):
        """
        Saves the sound to file and creates/updates a record in the database

        :param discord_id: The id of the user that uploaded this sound.
        :param sound: The stream of the sound to upload.
        """
        # Get the file path & name
        path = os.path.join('media', f'{discord_id}')
        file_name = 'joinsound'
        # Save the sound to file
        sound.download(path, file_name)
        full_path = sound.get_file_path(output_path=path, filename=file_name)
        cursor = self.cursor()
        # If the user has a sound already
        if self.has_sound(discord_id):
            query = f"UPDATE join_sounds SET file_path='{full_path}' WHERE discord_id='{discord_id}'"
            cursor.execute(query)
        else:
            query = f"INSERT INTO join_sounds (discord_id, file_path) VALUES (%s, %s)"
            val = (discord_id, full_path)
            cursor.execute(query, val)
        cursor.close()
        self.db.commit()
    
    def remove_sound(self, discord_id: str):
        """
        Removes the user's join sound from the database

        :param discord_id: The discord id to remove.
        """
        # Remove file
        path = self.get_sound(discord_id)
        os.remove(path)
        # Remove database entry
        cursor = self.cursor()
        query = f"DELETE FROM join_sounds WHERE discord_id='{discord_id}'"
        cursor.execute(query)
        cursor.close()
