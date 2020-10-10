from logging import log
from googletrans import Translator as GoogleTrans


from typing import Optional

import http.client
import urllib
import hashlib
import random
import json
import logging
import os
import time 

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models


class Translator(object):
    def __init__(self):
        pass

    def translate(self, text: str) -> str:
        pass

    def translate_with_rate(self, text: str, rate: float) -> str:

        time.sleep(rate)
        return self.translate(text)

    def translate_long_text(self, text: str) -> str:

        if len(text) >= 5000:
            #!TODO: 如果大于 5000 个字符，怎么分段翻译能够保证翻译的质量更好呢?
            pass

class EmptyTranslator(Translator):

    def translate(self, text: str) -> str:
        return text


class GoogleTranslator(Translator):
    """ https://github.com/ssut/py-googletrans"""

    def __init__(self):
        self.translator = GoogleTrans(service_urls=[
            'translate.google.cn',
        ])

    def translate(self, text: str):
        translation = self.translator.translate(text, dest="zh-CN")
        return translation.text


class BaiduTranslator(Translator):
    """Use baidu fanyi api to translate text from en to zh"""
    """https://fanyi-api.baidu.com/product/11"""

    def __init__(self, appid: str, appkey: str):
        self.appid = appid
        self.appkey = appkey

    def translate(self, text: str):

        api_response = self.api_request(text)

        if "trans_result" in api_response.keys():
            return api_response["trans_result"][0]["dst"]
        else:
            logging.error(
                f"baidu fanyi api error code: {api_response['error_code']}")

        return

    def api_request(self, text: str):
        """simply copy from the baidu fanyi python3 sdk"""
        fromLang = 'en'  # 原文语种
        toLang = 'zh'  # 译文语种
        myurl = '/api/trans/vip/translate'
        salt = random.randint(32768, 65536)
        sign = self.appid + text + str(salt) + self.appkey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = myurl + '?appid=' + self.appid + '&q=' + urllib.parse.quote(text) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
            salt) + '&sign=' + sign

        try:
            httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient.request('GET', myurl)

            # response是HTTPResponse对象
            response = httpClient.getresponse()
            result_all = response.read().decode("utf-8")
            result = json.loads(result_all)

            return result

        except Exception as e:
            logging.error(f"can not use baidu fanyi api with: {e}")
        finally:
            if httpClient:
                httpClient.close()

        return


class CaiyunTranslator(Translator):

    """caiyun https://open.caiyunapp.com/%E4%BA%94%E5%88%86%E9%92%9F%E5%AD%A6%E4%BC%9A%E5%BD%A9%E4%BA%91%E5%B0%8F%E8%AF%91_API"""

    def __init__(self, token: str):
        if token == None:
            logging.error(f"empty token")

        self.token = token

    def translate(self, text: str):

        api_response = self.api_request(text)

        return api_response["target"]

    def api_request(self, text: str):
        url = "http://api.interpreter.caiyunai.com/v1/translator"
        direction = "auto2zh"

        payload = {
            "source": text,
            "trans_type": direction,
            "request_id": "caiyun_translator",
            "detect": True,
        }

        response_data = ""
        req = urllib.request.Request(url)
        req.add_header("Content-Type", "application/json")
        req.add_header("x-authorization", "token " + self.token)

        with urllib.request.urlopen(req, data=json.dumps(payload).encode("utf-8")) as f:
            read_data = f.read()
            response_data = read_data.decode('unicode_escape')
            response_data = response_data.replace("\n", "")

        try:
            loads_data = json.loads(response_data)
            return loads_data
        except Exception as e :
            logging.error(f"error to loads data:{e}")
            logging.error(f"data is {response_data}")

        return json.loads(response_data)


class TencentTranslator(Translator):
    def __init__(self, secret_id: str, secret_key: str):
        if secret_id != None and secret_key != None:
            self.secret_id = secret_id
            self.secret_key = secret_key
        else:
            logging.error("You must specify the secret_id and secret_key for TencentTranslator")

    def translate(self, text: str) -> str:
        resp =  self.api_request(text)
        return resp
    
    def api_request(self, text: str) -> str:
        try: 
            cred = credential.Credential(self.secret_id, self.secret_key)
            # cred = credential.Credential()
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tmt.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tmt_client.TmtClient(cred, "ap-shanghai", clientProfile) 

            req = models.TextTranslateRequest()
            params = {
                "SourceText": text,
                "Source": "en",
                "Target": "zh",
                "ProjectId": 0
            }
            req.from_json_string(json.dumps(params))

            resp = client.TextTranslate(req)
            
            return resp.TargetText

        except TencentCloudSDKException as err: 
            logging.error(f"Error to use TencentAPI with {err}")
            return ""



if __name__ == "__main__":

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    baidu_appid = os.getenv("BAIDU_APPID")
    baidu_appkey = os.getenv("BAIDU_APPKEY")

    origin_text = ""
    with open("translator_test_text.txt", "r") as f:
        origin_text = f.read()

    print("----origin text----")
    print(origin_text)

    # print("\n\n")
    # print("----google translate-----")
    # google_translator = GoogleTranslator()
    # print(google_translator.translate(origin_text))

    # print("\n\n")
    # print("----baidu translate-----")
    # baidu_translator = BaiduTranslator(baidu_appid, baidu_appkey)
    # print(baidu_translator.translate_with_rate(origin_text, 1.5))

    # print("\n\n")
    # print("----Caiyun translate-----")
    # caiyun_translator = CaiyunTranslator("3975l6lr5pcbvidl6jl2")
    # print(caiyun_translator.translate(origin_text))

    # print("\n\n")
    # print("----Tencent translate-----")
    tencent_translator = TencentTranslator("ss", "ss")
    print(tencent_translator.translate(origin_text))