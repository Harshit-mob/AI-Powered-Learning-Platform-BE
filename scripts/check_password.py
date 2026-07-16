import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.api.v1.auth_utils import verify_password

def main():
    hash_str = "$argon2id$v=19$m=65536,t=3,p=4$FQKAUIrRWutdC0GI0boXwg$WOXj/UYVBUE9k51IRtQn9FGSyRiM1O0/OaRbkVIb+qo"
    for password in ["test@123"]:
        is_valid = verify_password(password, hash_str)
        print(f"Password '{password}' matches hash: {is_valid}")

if __name__ == "__main__":
    main()
