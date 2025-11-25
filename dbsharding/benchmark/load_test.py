import logging
import time
from sharding.single_db import SingleDatabase
from benchmark.data_generator import DataGenerator

logger = logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class LoadTester:

    def __init__(self, num_users: int = 99999, batch_size: int = 1000):
        self.num_users = num_users
        self.batch_size = batch_size

    def clear_database(self, type: str):
        if type == 'single':
            db = SingleDatabase('config/sharding-config.yaml')
            cursor = None
            try:
                cursor = db.connection.cursor()
                query = "delete from users"
                cursor.execute(query)
                db.connection.commit()
            except db.connection.DatabaseError as e:
                logger.error(f"clear database failed with {e}")
                return
            finally:
                if cursor is not None:
                    cursor.close()
                db.close_connection()
                    
    def benchmark_single_db(self) -> dict:
        self.clear_database('single')

        users = DataGenerator.generate_random_users(self.num_users)
        logger.info(f"no of users generated is {len(users)}")

        db = SingleDatabase('config/sharding-config.yaml')
        logger.info(f"benchmark insertion for {self.num_users} and with batch size {self.batch_size}")

        start_time = time.time()

        for i in range(0, len(users), self.batch_size):
            batch = users[i:i+self.batch_size]
            db.insert_batch_users(batch)

        insert_time = time.time() - start_time
        logger.info(f"insert completed in {insert_time}:.2f seconds")

        logger.info(f"retrieving random users")

        sample_user_ids = [users[i][0] for i in range(0, len(users), len(users)//10)]

        start_time = time.time()
        for userid in sample_user_ids:
            db.get_user(userid)

        read_time = time.time() - start_time

        logger.info(f"read {len(sample_user_ids)} in {read_time}.4f seconds")

        count = db.get_user_count()
        logger.info(f"total no of users in the database is {count}")
        db.close_connection()

        return {
            'database_type': 'Single Database',
            'num_of_users': self.num_users,
            'batch_size': self.batch_size,
            'insert_time': insert_time,
            'read_time': read_time,
            'writes_per_second': self.num_users/ insert_time if insert_time > 0 else 0,
            'reads_per_second': len(sample_user_ids)/ read_time if read_time > 0 else 0,
            'final_count': count
        }


if __name__ == '__main__':
    tester = LoadTester()
    result = tester.benchmark_single_db()
    logger.info(f"benchmark result for single database is {result}")
