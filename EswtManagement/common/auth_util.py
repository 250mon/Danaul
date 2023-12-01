import bcrypt
from ds_exceptions import InvalidPasswordError

def encrypt_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def verify_password(input_password: str, stored_password: bytes):
    # Hash the input password with the same salt used to hash the stored password
    hashed_input_password = bcrypt.hashpw(input_password.encode('utf-8'), stored_password)
    # Compare the hashed input password with the stored password
    return hashed_input_password == stored_password


def check_password_integrity(pw_text, confirm_text):
    if len(pw_text) < 1 or len(confirm_text) < 1:
        raise InvalidPasswordError("비밀번호 형식이 맞지 않습니다")
    elif pw_text != confirm_text:
        raise InvalidPasswordError("재입력 비밀번호가 맞지 않습니다")
