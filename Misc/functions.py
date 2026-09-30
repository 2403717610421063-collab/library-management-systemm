import hashlib, binascii
import timeago, datetime

salt=b'$#0x--.\'/\\98'
def hash(string):
    dk = hashlib.pbkdf2_hmac('sha256', b'password', salt, 100000)
    return binascii.hexlify(dk).decode("utf-8")

def b_hash(string):
    dk = hashlib.pbkdf2_hmac('sha256', b'password', salt, 100000)
    return binascii.hexlify(dk)
    
def ago(date):
    """
        Calculate a '3 hours ago' type string from a python datetime.
    """
    if date is None:
        return "Recently"
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date.split('.')[0], "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return str(date)
    now = datetime.datetime.now() + datetime.timedelta(seconds = 60 * 3.4)

    try:
        return timeago.format(date, now)
    except Exception:
        return str(date)