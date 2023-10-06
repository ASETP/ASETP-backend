import requests
import concurrent.futures
import csv
from tqdm import tqdm

# 定义API URL
api_url = "https://api.stackexchange.com/2.3/search"

# 设置查询参数，使用关键字搜索与异常和报错相关的问题
params = {
    "site": "stackoverflow",
    "pagesize": 100,  # 每次请求获取的问题数量
    "intitle": "exception",  # 使用关键字搜索
    "key": "OcugRWcRkGc4BmksZoNdag(("  # 替换为你的Stack Exchange API密钥
}

# 创建空的questions列表
questions = []
page = 1

# 创建CSV文件并写入标题行
with open("stackoverflow_data_exception.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Question ID", "Question Title", "Answer ID", "Answer"])

# 使用多线程并行获取数据
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    while len(questions) < 5000:
        # 发送请求
        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            questions.extend(items)
            page += 1
            params["page"] = page

        else:
            print(f"Error: {response.status_code}")
            break

    # 处理问题及答案，这里处理逻辑与之前的代码类似
    def process_question(question):
        question_id = question["question_id"]
        title = question["title"]

        # 获取问题的答案
        answers_api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
        answers_params = {
            "site": "stackoverflow",
            "pagesize": 3,  # 获取前3个答案，修改为你想要的数量
            "order": "desc",
            "sort": "votes",  # 根据投票数排序
            "filter": "withbody",  # 只获取包含答案内容的数据
            "key": "OcugRWcRkGc4BmksZoNdag(("  # 替换为你的Stack Exchange API密钥
        }

        answers_response = requests.get(answers_api_url, params=answers_params)

        if answers_response.status_code == 200:
            answers_data = answers_response.json()
            answers = answers_data.get("items", [])

            # 仅处理有至少一个回答且回答数大于等于3的问题
            if len(answers) >= 3:
                # 输出问题标题
                print(f"Question ID: {question_id}")
                print(f"Title: {title}")

                # 输出问题的前三个回答并写入CSV文件
                for answer in answers[:3]:
                    answer_id = answer["answer_id"]
                    answer_body = answer["body"]
                    print(f"Answer ID: {answer_id}")

                    # 写入CSV文件的stackoverflow_data_每一行
                    with open("stackoverflow_data_exception.csv", mode="a", newline="", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        writer.writerow([question_id, title, answer_id, answer_body])

                print("\n" + "=" * 50 + "\n")
        else:
            print(f"Error getting answers for question {question_id}")

    # 使用多线程处理问题
    for question in questions:
        executor.submit(process_question, question)

print("数据已写入CSV文件。")
