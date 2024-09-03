import requests
import json
from datetime import datetime,timedelta
import arxiv
import re
import os

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

def upload_bitable_datas(tenant_access_token, app_token, table_id, payload):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {tenant_access_token}'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

def sanitize_filename(title):
    # 替换非法字符并修剪长度
    title = re.sub(r'[<>:"/\\|?*]', '', title)  # 移除非法字符
    # title = title.replace(' ', '_')  # 替换空格
    return title[:255]  # 限制文件名长度

def get_arxiv_datas(keywords_lsit,submission_date):
    papers_data_list=[]
    existed_name = set()
    for keyword in keywords_lsit:
        category = "quant-ph"
        # 构建查询字符串
        query = f"all:{keyword} AND cat:{category}"
        
        # 搜索 arxiv
        client = arxiv.Client(page_size=50, delay_seconds=5) 
        search = arxiv.Search(
            query=query,
            max_results=100,
            sort_by=arxiv.SortCriterion.LastUpdatedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # 跳过经常出现的UnexpectedEmptyPageError
        while True:
            try:
                for result in client.results(search):
                    if result.updated.date() == submission_date.date():
                        
                        paper_name = sanitize_filename(result.title)
                        paper_abstract = result.summary
                        paper_authors = ",".join(i.name for i in result.authors)
                        paper_url = result.pdf_url
                        
                        # 将date对象转换为datetime对象
                        dt = datetime.combine(submission_date.date(), datetime.min.time())
                        # 获取秒级时间戳并转换为毫秒级时间戳
                        timestamp_ms = int(dt.timestamp() * 1000)
                        
                        if paper_name not in existed_name:
                            paper_info = {
                                "题目": paper_name,
                                "作者": f"{paper_authors}",
                                "摘要": paper_abstract,
                                "PDF链接": {"link":paper_url},
                                "更新日期": timestamp_ms,
                                "研究方向": [keyword]
                            }
                            feishu_paper_info = {"fields":paper_info}
                            papers_data_list.append(feishu_paper_info)
                        else:
                            for papers_data in papers_data_list:
                                if papers_data['fields']['题目'] == paper_name:
                                    papers_data['fields']['研究方向'].append(keyword)
                        
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
    
app_id = 'cli_a647fad3dc78500d'
app_secret = 'B3LuYvv13rZaKjgiHyIb7gTDVnr18KFe'

# 从环境变量中获取敏感信息
# app_id = os.getenv("APP_ID")
# app_secret = os.getenv("APP_SECRET")
tenant_access_token = get_tenant_access_token(app_id,app_secret)
app_token = 'ZMM2bIkPOaDyxNsJBKZcInFCnlc'
table_id = 'tbl5DsCcQbnG0JbH'

# keywords = "quantum machine learning"
keywords_list = ["quantum machine learning","quantum error mitigation","QAOA","quantum compiling","quantum algorithm"]
submission_date = datetime.now() - timedelta(days=4)
# submission_date = datetime(2024, 7, 25)

papers_data_list = get_arxiv_datas(keywords_list,submission_date)
upload_data = json.dumps({"records":papers_data_list})
upload_bitable_datas(tenant_access_token, app_token, table_id,upload_data)


# 定义起始日期
start_date = datetime(2024, 8, 20)
# 定义结束日期
end_date = datetime(2024, 8, 28)

def supply_date_data(start_date,end_date):
    current_date = start_date
    while current_date <= end_date:
        payload = get_arxiv_datas(keywords_list,current_date)
        upload_bitable_datas(tenant_access_token, app_token, table_id,payload)
        # print(current_date.strftime('%Y-%m-%d'))  # 格式化输出日期
        current_date += timedelta(days=1)  # 每次循环增加一天


# chat_id = 'oc_d2ce116cf4a34227195daf8a0281730e' # 量子算法群
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

# 每日更新论文的name
name = ",".join(name_list)

at_content = "<at user_id=\\\"all\\\"></at>"
link_content = "[每日论文更新](https://scn0xfel4hbc.feishu.cn/base/ZMM2bIkPOaDyxNsJBKZcInFCnlc?table=tbl5DsCcQbnG0JbH&view=vewu9R1ebn)"
main_content = f"{submission_date.date()}论文更新共计{paper_num}篇，包含方向有：{name}，欢迎大家点击链接阅读"
# text_content = at_content + " " + main_content + "\\n" + link_content

if paper_num == 0:
    text_content = at_content + "昨日无论文更新，往日论文链接" + "\\n" + link_content
else:
    text_content = at_content + " " + main_content + "\\n" + link_content

send_messages(text_content,chat_id)