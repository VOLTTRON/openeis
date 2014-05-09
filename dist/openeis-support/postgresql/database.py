DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'openeis',
        'USER': 'openeis',
    }
}

def readconf():
    import re
    global DATABASES
    try:
        with open('/etc/postgresql/9.1/main/postgresql.conf') as file:
            conf = file.read(100000)
    except FileNotFoundError:
        return
    match = re.search(r'(?:\n|^)\s*port\s*=\s*(\d+)', conf, re.M | re.S)
    if match:
        port = int(match.group(1))
    if port != 5432:
        DATABASE['default']['PORT'] = port
readconf()
del readconf
