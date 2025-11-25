import logging
import yaml
import mysql.connector
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SingleDatabase:
    """Single database implementation for sharding benchmark"""

    def __init__(self, config_path: str = "../config/sharding-config.yaml"):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        db_config = config['single-db']
        self.connection = mysql.connector.connect(
            host = db_config['host'],
            port = db_config['port'],
            user = db_config['user'],
            password = db_config['password'],
            database = db_config['database'],
            auth_plugin = db_config['auth']
        )

        logger.info("connected to single database")

    def insert_user(self, user_id: int, username: str, email: str) -> bool:
        """Insert a single user. Returns True on success, False on failure."""
        cursor = None
        try:
            cursor = self.connection.cursor()
            query = """
                insert into users(user_id, username, email)
                values(%s, %s, %s)
            """
            cursor.execute(query, (user_id, username, email))
            self.connection.commit()
            return True
        except self.connection.IntegrityError as e:
            logger.error(f"Integrity error while inserting user {user_id}: {e}")       
            self.connection.rollback()
            return False
        except self.connection.DatabaseError as e:
            logger.error(f"Database error while inserting user {user_id}: {e}")
            self.connection.rollback()
            return False
        finally:
            if cursor is not None:
                cursor.close()

    def insert_batch_users(self, users: list[tuple[int, str, str]]) -> bool:
        """Insert a multiple users"""
        cursor = None

        try:
            cursor = self.connection.cursor()
            query = """
                insert into users(user_id, username, email)
                values(%s, %s, %s)
            """
            cursor.executemany(query, users)
            self.connection.commit()
            return True
        except self.connection.DatabaseError as e:
            logger.error(f"insert failed with error {e}")
            self.connection.rollback()
            return False
        
        finally:
            if cursor is not None:
                cursor.close()

    def get_user(self, user_id: int) -> dict[str, Any]|None:
        """Retrieve a user by User ID"""
        cursor = None

        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "select * from users where user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            return user
        except self.connection.DatabaseError as e:
            logger.error(f"get_user failed for user id {user_id} with error: {e}")
            return None
        finally:
            if cursor is not None:
                cursor.close()

    def get_all_users(self) -> list[dict[str, Any]]|None:
        """Retrieve all the users in the database"""
        cursor = None
        users = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """select * from users"""
            cursor.execute(query)
            users = cursor.fetchall()
            
            return users
        except self.connection.DatabaseError as e:
            logger.error(f"query failed with error :{e}")
            return None
        finally:
            if cursor is not None:
                cursor.close()
            

    def get_user_count(self) -> tuple[int|None, bool]:
        """Fetch the number of users in the database"""
        cursor = None
        count = None
        try:
            cursor = self.connection.cursor()
            query = "select count(*) from users"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            return (count, True)
        except self.connection.DatabaseError as e:
            logger.error(f"count fetch failed with error : {e}")
            return (None, False)
        finally:
            if cursor is not None:
                cursor.close()

    def close_connection(self):
        """Close the database connection"""
        if self.connection.is_connected():
            self.connection.close()
            logger.info("database connection closed")


if __name__ == '__main__':
    logger.info("Start testing Single database")
    db = SingleDatabase()
    status = db.insert_user(1, 'test001', 'test001@example.com')
    if (status):
        logger.info(f"user inserted successfully with user id 1")
    user = db.get_user(1)
    if user is not None:
        logger.info(f"user fetched with details {user}")
    else:  
        logger.error("user fetch failed for user id 1")
    count, success = db.get_user_count()
    if success:
        logger.info(f"no of users in the database is {count}")
    else:
        logger.error("user count query failed")

    users = [
        (2, 'test002', 'test002@example.com'),
        (3, 'test003', 'test003@example.com'),
        (4, 'test004', 'test004@example.com'),
        (5, 'test005', 'test005@example.com')]

    result = db.insert_batch_users(users)
    if result:
        logger.info("users inserted")
    else:
        logger.error("bulk insertion failed")

    result = db.get_all_users()
    if result:
        logger.info(f"users list is {users}")
    else:
        logger.error("bulk fetch failed")

    count, success = db.get_user_count()
    if success:
        logger.info(f"no of users in the database after bulk insert is {count}")
    else:
        logger.error("user count query failed")
    
    db.close_connection()
    
