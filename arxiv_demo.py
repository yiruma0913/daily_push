import arxiv
from datetime import datetime,timedelta
import time
import re
import json

def sanitize_filename(title):
    # 替换非法字符并修剪长度
    title = re.sub(r'[<>:"/\\|?*]', '', title)  # 移除非法字符
    # title = title.replace(' ', '_')  # 替换空格
    return title[:255]  # 限制文件名长度

def get_arxiv_datas(keyword,submission_date):
    category = "quant-ph"
    # 构建查询字符串
    query = f"all:{keyword} AND cat:{category}"
    
    # 搜索 arxiv
    client = arxiv.Client(page_size=50, delay_seconds=5) 
    search = arxiv.Search(
        query=query,
        max_results=100,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers_data = []
    
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
                    
                    paper_info = {
                        "题目": paper_name,
                        "作者": f"{paper_authors}",
                        "摘要": paper_abstract,
                        "PDF链接": paper_url,
                        "更新日期": timestamp_ms,
                        "研究方向": keyword
                    }
                    feishu_paper_info = {"fields":paper_info}
                    # 将当前文章信息添加到 papers_data 列表中
                    papers_data.append(feishu_paper_info)
            info_data = {"records":papers_data}
            payload = json.dumps(info_data)
            
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
        
    return payload

keywords = "quantum machine learning"

submission_date = datetime.now() - timedelta(days=1)
# submission_date = datetime(2024, 7, 25)
payload = get_arxiv_datas(keywords,submission_date)
print(payload)