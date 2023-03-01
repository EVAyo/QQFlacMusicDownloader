from pyDes import des, PAD_PKCS5, CBC
import base64

# des解密


def decryptDES(strs: str, key: str): return des(
    key, CBC, key, padmode=PAD_PKCS5).decrypt(base64.b64decode(str(strs)))


# des加密
def encryptDES(text: str, key: str): return str(base64.b64encode(
    des(key, CBC, key, padmode=PAD_PKCS5).encrypt(text)), 'utf-8')


# 加密字符串
def encryptText(text: str, qq: str):
    key = (qq)[0:8]
    return encryptDES(text, key)


# 解密字符串
def decryptText(text: str, qq: str): return str(decryptDES(
    text.replace("-", ""), (qq)[0:8]), 'utf-8')
