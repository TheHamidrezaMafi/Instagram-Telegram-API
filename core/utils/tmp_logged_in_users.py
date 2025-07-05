from datetime import datetime

# In-memory store of logged-in users
tmp_logged_in_users = {}

def update_or_add_user(telegram_id, user_login):
    """
    Adds a new user or updates the existing one with a new Instagram instance and timestamps.
    """
    now = datetime.now().isoformat()
    if telegram_id in tmp_logged_in_users:
        tmp_logged_in_users[telegram_id]['last_used'] = now
        tmp_logged_in_users[telegram_id]['instagram_object'] = user_login
        tmp_logged_in_users[telegram_id]['username'] = user_login.username
    else:
        tmp_logged_in_users[telegram_id] = {
            'first_login': now,
            'last_used': now,
            'username': user_login.username,
            'instagram_object': user_login,
        }

def get_user(telegram_id):
    """Returns the Instagram login instance (if exists)"""
    user = tmp_logged_in_users.get(telegram_id)
    return user.get('instagram_object') if user else None

def delete_user(telegram_id):
    """Removes a user from the dict"""
    if telegram_id in tmp_logged_in_users:
        del tmp_logged_in_users[telegram_id]

def update_last_used(telegram_id):
    """Updates the last used timestamp for the user"""
    if telegram_id in tmp_logged_in_users:
        tmp_logged_in_users[telegram_id]['last_used'] = datetime.now().isoformat()