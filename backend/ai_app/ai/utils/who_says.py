def user_talking(content):
    return {'role': 'user', 'content': content}
def assistant_talking(content):
    return {'role': 'assistant', 'content': content}
def system_talking(content):
    return {'role': 'system', 'content': content}