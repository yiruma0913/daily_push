import requests
import json
from datetime import datetime, timedelta
import arxiv
import re
import os


def sanitize_filename(title):
    # 替换非法字符并修剪长度
    title = re.sub(r'[<>:"/\\|?*]', "", title)  # 移除非法字符
    # title = title.replace(' ', '_')  # 替换空格
    return title[:255]  # 限制文件名长度


def dateto13timestamp(submission_date):
    # 将datetime对象转换为timestamp对象
    dt = datetime.combine(submission_date.date(), datetime.min.time())
    # 获取秒级时间戳并转换为毫秒级时间戳
    timestamp_ms = int(dt.timestamp() * 1000)
    return timestamp_ms


def extractParenthesesContent(keyword):
    start = keyword.find("(")
    end = keyword.find(")")
    if start != -1 and end != -1:
        result = keyword[start + 1 : end]
        return result
    else:
        return keyword


def get_tenant_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret})
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    return response.json()["tenant_access_token"]


def upload_bitable_datas(tenant_access_token, app_token, table_id, payload):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)


def send_messages(tenant_access_token, text_content, chat_id):
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


def get_update_paper_num(tenant_access_token, app_token, table_id):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?page_size=100"
    timestamp_ms = dateto13timestamp(submission_date)
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
    # print(response.text)
    num = len(response.json()["data"]["items"])
    keywords_name_set = set()
    response_list = response.json()["data"]["items"]
    for data in response_list:
        for i in data["fields"]["研究方向"]:
            keywords_name_set.add(i)
    keywords_name = ",".join(keywords_name_set)
    return num, keywords_name


def combine_text_content(paper_num, keywords_name):
    at_content = '<at user_id=\\"all\\"></at>'
    link_content = "[每日论文更新](https://scn0xfel4hbc.feishu.cn/base/ZMM2bIkPOaDyxNsJBKZcInFCnlc?table=tbl5DsCcQbnG0JbH&view=vewu9R1ebn)"
    main_content = f"{submission_date.date()}论文更新共计{paper_num}篇，包含方向有：{keywords_name}，欢迎大家点击链接阅读"
    # text_content = at_content + " " + main_content + "\\n" + link_content

    if paper_num == 0:
        text_content = (
            at_content
            + f"{submission_date.date()}无论文更新，往日论文链接如下"
            + "\\n"
            + link_content
        )
    else:
        text_content = at_content + " " + main_content + "\\n" + link_content
    return text_content


def get_arxiv_datas(keywords_lsit, submission_date):
    papers_data_list = []
    existed_name = set()
    for keyword in keywords_lsit:
        if "+" in keyword:
            parts = keyword.split("+")
            part_before_plus = parts[0]
            part_after_plus = parts[1]
            query = f"abs:%22{part_before_plus}%22 AND abs:%22{part_after_plus}%22"
        else:
            category = "quant-ph"
            if "(" in keyword or ")" in keyword:
                query = f"abs:{keyword} AND cat:{category}"
            else:  # 构建查询字符串
                query = f"abs:%22{keyword}%22 AND cat:{category}"

        # 搜索 arxiv
        client = arxiv.Client(page_size=100, delay_seconds=5)
        search = arxiv.Search(
            query=query,
            max_results=100,
            sort_by=arxiv.SortCriterion.LastUpdatedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        keyword_short_name = extractParenthesesContent(keyword)

        # 跳过经常出现的UnexpectedEmptyPageError
        while True:
            try:
                for result in client.results(search):
                    if result.updated.date() == submission_date.date():

                        paper_name = sanitize_filename(result.title)
                        paper_abstract = result.summary
                        paper_authors = ",".join(i.name for i in result.authors)
                        paper_url = result.pdf_url

                        timestamp_ms = dateto13timestamp(submission_date)

                        if paper_name not in existed_name:
                            paper_info = {
                                "题目": paper_name,
                                "作者": f"{paper_authors}",
                                "摘要": paper_abstract,
                                "PDF链接": {"link": paper_url},
                                "更新日期": timestamp_ms,
                                "研究方向": [keyword_short_name],
                            }
                            feishu_paper_info = {"fields": paper_info}
                            papers_data_list.append(feishu_paper_info)
                        else:
                            for papers_data in papers_data_list:
                                if papers_data["fields"]["题目"] == paper_name:
                                    papers_data["fields"]["研究方向"].append(
                                        keyword_short_name
                                    )

                        existed_name.add(paper_name)

                # info_data = {"records":papers_data}
                # payload = json.dumps(info_data)

                # json_name = f"{keyword}--{submission_date.date()}.json"
                # json_path = os.path.join(save_dir,json_name)
                # if not os.path.exists(json_path):
                #     # 保存所有文章信息到 JSON 文件
                #     with open(json_path, 'w') as json_file:
                #         json.dump(papers_data, json_file, indent=4)
                # else:
                #     print(f"{json_name} already exists")
                break
            except arxiv.UnexpectedEmptyPageError:
                print("Reached an empty page, continuing to next set of results.")
                continue

    return papers_data_list


def main():
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    papers_data_list = get_arxiv_datas(keywords_list, submission_date)
    upload_data = json.dumps({"records": papers_data_list})
    if papers_data_list:
        upload_bitable_datas(tenant_access_token, app_token, table_id, upload_data)
    paper_num, keywords_name = get_update_paper_num(
        tenant_access_token, app_token, table_id
    )
    text_content = combine_text_content(paper_num, keywords_name)
    send_messages(tenant_access_token, text_content, chat_id)


if __name__ == "__main__":
    # app_id = 'cli_a647fad3dc78500d'
    # app_secret = 'B3LuYvv13rZaKjgiHyIb7gTDVnr18KFe'
    # 从环境变量中获取敏感信息
    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")

    app_token = "ZMM2bIkPOaDyxNsJBKZcInFCnlc"
    table_id = "tbl5DsCcQbnG0JbH"
    view_id = "vewu9R1ebn"

    chat_id = 'oc_d2ce116cf4a34227195daf8a0281730e' # 量子算法群
    # chat_id = "oc_82d99fc295c740ebbbc8764dbcfdc15f"  # test

    # keywords = "quantum machine learning"
    keywords_list = [
        "quantum machine learning",
        "quantum error mitigation",
        "quantum compiling",
        "quantum algorithm",
        "Quantum Amplitude Amplification",
        "quantum circuit knitting",
        "quantum simulation",
        "quantum walk",
        "Grover Algorithm",
        "Shor Algorithm",
        "HHL Algorithm",
        "reinforcement learning+stock trading",
        "reinforcement learning+optimization",
        "large language model+fine tuning",
        "Quantum Approximate Optimization Algorithm(QAOA)",
        "variational quantum algorithm(VQA)",
        "Quantum Fourier Transform(QFT)",
        "Quantum Phase Estimation(QPE)",
        "Quantum Amplitude Estimation(QAE)",
        "Variation Quantum Estimation(VQE)",
        "Variation Quantum Deflation(VQD)",
    ]

    submission_date = datetime.now() - timedelta(days=1)
    # submission_date = datetime(2024, 7, 25)

    main()
