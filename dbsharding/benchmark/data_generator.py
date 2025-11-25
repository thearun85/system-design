import random

class DataGenerator:
    """Generate data for benchmark testing"""

    @staticmethod
    def generate_username(user_id: int) -> str:
        return f"user_{user_id}"

    @staticmethod
    def generate_email(user_id: int) -> str:
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com']
        domain = random.choice(domains)
        return f"user_{user_id}@{domain}"

    @staticmethod
    def generate_random_users(num_users: int, max_user_id: int = 100000) ->list[tuple[int, str, str]]:
        user_ids = random.sample(range(1, max_user_id), num_users)
        users = []
        for user_id in user_ids:
            username = DataGenerator.generate_username(user_id)
            email = DataGenerator.generate_email(user_id)
            users.append((user_id, username, email))

        return users

if __name__ == '__main__':
    print("Testing data generation script")
    print("generating 10 users")
    users = DataGenerator.generate_random_users(10, 1000)
    for user in users:
        print(f"user detail is {user}")
