ALLOWED_HOSTS = []
PROTECTED_MEDIA_METHOD = 'X-Accel-Redirect'

def readconf():
    import re
    global ALLOWED_HOSTS
    try:
        with open('/etc/nginx/conf.d/openeis.conf') as file:
            conf = file.read(100000)
    except FileNotFoundError:
        return
    match = re.search(r'(?:\n|{|;)\s*server_name\s+([^;]*);', conf, re.M | re.S)
    if match:
        ALLOWED_HOSTS.extend(match.group(1).split())
readconf()
del readconf
