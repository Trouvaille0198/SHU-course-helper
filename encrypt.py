import base64
import rsa


def _str2key(s):
    # 对字符串解码
    b_str = base64.b64decode(s)

    if len(b_str) < 162:
        return False

    hex_str = ""

    # 按位转换成16进制
    for x in b_str:
        h = hex(x)[2:]
        h = h.rjust(2, "0")
        hex_str += h

    # 找到模数和指数的开头结束位置
    m_start = 29 * 2
    e_start = 159 * 2
    m_len = 128 * 2
    e_len = 3 * 2

    modulus = hex_str[m_start: m_start + m_len]
    exponent = hex_str[e_start: e_start + e_len]

    return modulus, exponent


def rsa_encrypt(password, pubkey):
    """
    rsa加密
    :param password: 待加密字符串
    :param pubkey: 公钥
    :return: 加密串
    """
    key = _str2key(pubkey)
    modulus = int(key[0], 16)
    exponent = int(key[1], 16)
    pubkey = rsa.PublicKey(modulus, exponent)
    return base64.b64encode(rsa.encrypt(password.encode(), pubkey)).decode()


def encrypt(password, key_str):
    pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(key_str.encode('utf-8'))
    crypto = base64.b64encode(rsa.encrypt(password.encode('utf-8'), pub_key)).decode()
    return crypto
