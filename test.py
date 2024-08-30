import requests
import json
from datetime import datetime,timedelta
import arxiv
import re

def get_tenant_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    return response.json()['tenant_access_token']

app_id = 'cli_a647fad3dc78500d'
app_secret = 'B3LuYvv13rZaKjgiHyIb7gTDVnr18KFe'
tenant_access_token = get_tenant_access_token(app_id,app_secret)
app_token = 'ZMM2bIkPOaDyxNsJBKZcInFCnlc'
table_id = 'tbl5DsCcQbnG0JbH'

chat_id = 'oc_82d99fc295c740ebbbc8764dbcfdc15f' # test

def send_messages(text_content,chat_id):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        # "content": f"{{\"text\":\"<at user_id=\\\"all\\\"></at>{text_content}\"}}",
        "content":f"{{\"text\":\"{text_content}\"}}",
        "msg_type": "text",
        "receive_id": f"{chat_id}"
    })
    
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {tenant_access_token}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    
at_content = "<at user_id=\\\"all\\\"></at>"
main_content = "测试"
link_content = "[每日论文更新](https://scn0xfel4hbc.feishu.cn/base/ZMM2bIkPOaDyxNsJBKZcInFCnlc?table=tbl5DsCcQbnG0JbH&view=vewu9R1ebn)"
text_content = at_content + " " + main_content + "\\n" + link_content

send_messages(text_content,chat_id)