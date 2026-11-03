def find_user(users, username):
    for user in users:
        if user["username"] == username:
            return user
    return None
