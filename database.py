import sqlite3
import config

# Create table of users if it does not exist
def create_if_not_exists() -> None:
    
    connection = sqlite3.connect(config.USER_DB_NAME)
    
    with connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                rank_and_name TEXT NOT NULL,
                company TEXT NOT NULL,
                username TEXT NOT NULL,
                UNIQUE (rank_and_name, company)
            ) WITHOUT ROWID;"""
        )
    
    connection.close()
    return


# Create a new user or replace an existing one  
def add_user(user_id: int, user_data: dict):
    
    connection = sqlite3.connect(config.USER_DB_NAME)
    
    with connection:    
        connection.execute(
            """INSERT OR REPLACE INTO users (user_id, rank_and_name, company, username)
            VALUES (:user_id, :rank_and_name, :company, :username);""",
            (user_id, user_data['rank_and_name'], user_data['company'], user_data['username'])
        )
    
    connection.close()
    return


# Retrieve an existing user profile
def retrieve_user(user_id: int) -> dict:
    
    connection = sqlite3.connect(config.USER_DB_NAME)
    cursor = connection.cursor()
    
    cursor.execute(
        """SELECT rank_and_name, company, username
        FROM users
        WHERE user_id = :user_id""",
        (user_id,) # (user_id) is an int while (user_id,) is a tuple containing an int
    )
    
    if (user_data := cursor.fetchone()):
        connection.close()
        return {
            'rank_and_name': user_data[0],
            'company': user_data[1],
            'username': user_data[2]
        }
    
    connection.close()
    return {}


# Retrieve users by rank and name and company
def retrieve_user_by_rank_name_company(rank_and_name: str, company: str) -> list:
    
    connection = sqlite3.connect(config.USER_DB_NAME)
    cursor = connection.cursor()
    
    cursor.execute(
        """SELECT user_id, username
        FROM users
        WHERE rank_and_name = :rank_and_name
        AND company = :company""",
        (rank_and_name, company) # (user_id) is an int while (user_id,) is a tuple containing an int
    )
    
    if (data := cursor.fetchone()):
        connection.close()
        return {
            'id': data[0],
            'username': data[1]
        }
        
    connection.close()
    return data
