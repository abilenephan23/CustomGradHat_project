import hashlib
import hmac
from datetime import datetime
import urllib.parse
import random
from fastapi import Request
from payos import PayOS, ItemData, PaymentData



import os
from dotenv import load_dotenv

load_dotenv()

vnp_TmnCode = os.getenv('TMN_CODE')
vnp_HashSecret = os.getenv('HASH_SECRET')
vnp_Url = os.getenv('SANDBOX_URL')
vnp_ReturnUrl = os.getenv('RETURN_URL')


def generate_secure_hash(payload, secret_key):
    sorted_payload = sorted(payload.items())
    data_string = '&'.join(f"{key}={urllib.parse.quote_plus(str(value))}" for key, value in sorted_payload)
    secure_hash = hmac.new(secret_key.encode(), data_string.encode(), hashlib.sha512).hexdigest()
    return secure_hash

# function create random number base on leghth as inputimport random

def random_number_string(length: int) -> str:
    """
    Generate a random number string of the specified length.

    Args:
    length (int): The length of the random number string.

    Returns:
    str: A random number string of the given length.
    """
    if length <= 0:
        raise ValueError("Length must be a positive integer.")
    
    return ''.join(random.choices('0123456789', k=length))


def get_payment_url(amount,order_id,ip_address):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    payload = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': vnp_TmnCode,
        'vnp_Amount': str(int(amount * 100)),
        'vnp_CreateDate': timestamp,
        'vnp_CurrCode': 'VND',
        'vnp_IpAddr': ip_address,
        'vnp_Locale': 'vn',
        'vnp_OrderInfo': 'Thanh toan don hang tai Spotlight. So tien ' + str(int(amount))+' VND',
        'vnp_OrderType': '200000',
        'vnp_ReturnUrl': vnp_ReturnUrl+"?vnp_Data="+str(order_id),
        'vnp_TxnRef': random_number_string(8)
    }

    payload['vnp_SecureHash'] = generate_secure_hash(payload, vnp_HashSecret)

    final_url = f"{vnp_Url}?{urllib.parse.urlencode(payload)}"

    return final_url

    # response = requests.get(final_url)
    # print(response.url)
