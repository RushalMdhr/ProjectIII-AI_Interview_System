def user_talking(message):
    return {
        'role': 'user',
        'content': message
    }

def assistant_talking(message):
    return {
        'role': 'assistant',
        'content': message
    }

def system_talking(message):
    return {
        'role': 'system',
        'content': message
    }