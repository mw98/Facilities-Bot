import psycopg2
import config    

# Create table of users if it does not exist
def create_if_not_exists() -> None:
    
    try:
        with psycopg2.connect(config.USER_DATABASE_URL, sslmode = 'require') as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id        BIGINT PRIMARY KEY,
                        rank_and_name  TEXT NOT NULL,
                        company        TEXT NOT NULL,
                        username       TEXT NOT NULL,
                        UNIQUE (rank_and_name, company)
                    );
                    """
                )
    except Exception as error:
        print(f'Could not create users db: {error}')
    finally:
        connection.close()
    return


# Create a new user or replace an existing one  
def add_user(user_id: int, user_data: dict) -> int:
    
    state = 0
    try:
        with psycopg2.connect(config.USER_DATABASE_URL, sslmode = 'require') as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (user_id, rank_and_name, company, username)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET (rank_and_name, company, username) = (EXCLUDED.rank_and_name, EXCLUDED.company, EXCLUDED.username);
                    """,
                (user_id, user_data['rank_and_name'], user_data['company'], user_data['username'])
                )
    except Exception as error:
        print(f'Could not add user to db: {error}')
        state = -1
    finally:
        connection.close()
    return state


# Retrieve an existing user profile
def retrieve_user(user_id: int):
    
    user_data = None
    try:
        with psycopg2.connect(config.USER_DATABASE_URL, sslmode = 'require') as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT rank_and_name, company, username
                    FROM users
                    WHERE user_id = %s
                    """,
                    (user_id,) # (user_id) is an int while (user_id,) is a tuple containing an int
                )
                user_data = cursor.fetchone()
    except Exception as error:
        print(f'Could not retrieve user from db: {error}')
    finally:
        connection.close()
    
    if user_data:
        return {
            'rank_and_name': user_data[0],
            'company': user_data[1],
            'username': user_data[2]
        }
    return
    

# Retrieve users by rank and name and company
def retrieve_user_by_rank_name_company(rank_and_name: str, company: str) -> list:
    
    user_data = None
    try:
        with psycopg2.connect(config.USER_DATABASE_URL, sslmode = 'require') as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username
                    FROM users
                    WHERE rank_and_name = %s
                    AND company = %s
                    """,
                    (rank_and_name, company)
                )
                user_data = cursor.fetchone()
    except Exception as error:
        print(f'Could not retrieve user from db: {error}')
    finally:
        connection.close()
    
    if user_data:
        return {
            'id': user_data[0],
            'username': user_data[1]
        }
    return