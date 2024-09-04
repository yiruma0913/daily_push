from matplotlib import table
import requests
import json
from datetime import datetime, timedelta
import arxiv
import re


def get_tenant_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret})
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    return response.json()["tenant_access_token"]


app_id = "cli_a647fad3dc78500d"
app_secret = "B3LuYvv13rZaKjgiHyIb7gTDVnr18KFe"
tenant_access_token = get_tenant_access_token(app_id, app_secret)
app_token = "ZMM2bIkPOaDyxNsJBKZcInFCnlc"
table_id = "tbl5DsCcQbnG0JbH"
view_id = "vewu9R1ebn"

chat_id = "oc_82d99fc295c740ebbbc8764dbcfdc15f"  # test
submission_date = datetime.now() - timedelta(days=4)
# 将date对象转换为datetime对象
dt = datetime.combine(submission_date.date(), datetime.min.time())
# 获取秒级时间戳并转换为毫秒级时间戳
timestamp_ms = int(dt.timestamp() * 1000)


def send_messages(text_content, chat_id):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps(
        {
            # "content": f"{{\"text\":\"<at user_id=\\\"all\\\"></at>{text_content}\"}}",
            "content": f'{{"text":"{text_content}"}}',
            "msg_type": "text",
            "receive_id": f"{chat_id}",
        }
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)


at_content = '<at user_id=\\"all\\"></at>'
main_content = "测试"
link_content = "[每日论文更新](https://scn0xfel4hbc.feishu.cn/base/ZMM2bIkPOaDyxNsJBKZcInFCnlc?table=tbl5DsCcQbnG0JbH&view=vewu9R1ebn)"
text_content = at_content + " " + main_content + "\\n" + link_content

# send_messages(text_content,chat_id)


def get_update_paper_num():
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?page_size=100"
    payload = json.dumps(
        {
            "automatic_fields": False,
            "field_names": ["题目", "研究方向"],
            "filter": {
                "conditions": [
                    {
                        "field_name": "更新日期",
                        "operator": "is",
                        "value": ["ExactDate", f"{timestamp_ms}"],
                    }
                ],
                "conjunction": "and",
            },
            "sort": [{"desc": True, "field_name": "更新日期"}],
            "view_id": f"{view_id}",
        }
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    keywords_name_set = set()
    response_list = response.json()["data"]["items"]
    for data in response_list:
        for i in data["fields"]["研究方向"]:
            keywords_name_set.add(i)
    keywords_name = ",".join(keywords_name_set)
    print(keywords_name)


get_update_paper_num()
