import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.api.v1.auth_utils import get_password_hash, verify_password

def test():
    password = "MySuperSecretPassword123!"
    hashed = get_password_hash(password)
    print(f"Hashed: {hashed}")
    
    is_valid = verify_password(password, hashed)
    print(f"Valid: {is_valid}")
    
    is_invalid = verify_password("wrong", hashed)
    print(f"Invalid: {is_invalid}")

if __name__ == "__main__":
    test()
