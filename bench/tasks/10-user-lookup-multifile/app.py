from helpers import find_user

def user_label(users, username):
    user = find_user(users, username)
    return user["display"] if user else None
