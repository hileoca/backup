import os
import requests

download_dir = r"D:\output"  # 请按实际路径修改图片保存目录
os.makedirs(download_dir, exist_ok=True)

# 读取链接
links_file = "list.txt" #图片链接列表，一行一个图片
with open(links_file, "r", encoding="utf-8") as f:
    links = [line.strip() for line in f if line.strip()]

def download_image(url, out_path):
    # 可以根据需要添加 headers，比如 User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; your-bot/1.0)"
    }
    r = requests.get(url, headers=headers, stream=True, timeout=20)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

counter = 1
for url in links:
    try:
        ext = ".jpg"  # 指定图片后缀。也可以尝试从响应头或 URL 推断原始扩展名
        # 若要保留原图片原本扩展名，可以尝试从响应头 Content-Type 推断
        path = os.path.join(download_dir, f"{counter:04d}{ext}") #文件名按顺序用4位自然数重命名
        download_image(url, path)
        print(f"[{counter:04d}] downloaded: {path}")
        counter += 1
    except Exception as e:
        print(f"Error for {url}: {e}")
