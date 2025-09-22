import requests
from bs4 import BeautifulSoup # 安装依赖 pip install beautifulsoup4
import time
import csv

# 配置
ORG_URL = "https://github.com/kanripo"  # 组织主页
REPOS_TYPE_URL = "https://github.com/orgs/kanripo/repositories"

# 若无认证，GitHub 对某些头部和速率可能有限制。若有 Token，请填入如下：
GITHUB_TOKEN = ""  # 例如 "ghp_xxx..."，若为空则不使用认证

HEADERS = {
    "User-Agent": "GitHub-Repo-Scraper/1.0",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# 调整分页参数
PER_PAGE = 30  # GitHub 默认每页 30 条，可以改成你网页实际显示数量
TOTAL_PAGES = 312  # 分页总数

def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def extract_repo_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    # GitHub 的仓库列表中，仓库链接通常在 <a> 标签中，指向 /<owner>/<repo>
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 匹配 /{owner}/{repo}，且不是组织页内的子链接（如 /kanripo? 或 /kanripo/repositories）
        if href.startswith("/") and not href.startswith("//"):
            # 过滤掉页面中的其他链接，确保是仓库页的顶层链接
            # 典型仓库链接形如 "/owner/repo"
            parts = href.strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                # 过滤掉组织的子页面链接如 /kanripo/repositories 等
                if owner and repo:
                    full = f"https://github.com/{owner}/{repo}"
                    # 只保留顶级仓库页面，排除组织的子页面（如 /kanripo/xxx），但上面的筛选已经包含 owner/repo
                    links.append(full)
    # 去重
    return sorted(set(links))

def save_to_csv(repo_urls, out_path="repositories.csv"):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["repository_url"])
        for url in repo_urls:
            writer.writerow([url])
    print(f"Saved {len(repo_urls)} repositories to {out_path}")

def main():
    all_repos = set()

    for page in range(1, TOTAL_PAGES + 1):
        # 构造分页 URL
        # 原页面可能带有其他参数，可按实际网格拼接，这里以 type=all&page=N 为例
        url = f"{REPOS_TYPE_URL}?type=all&page={page}"
        print(f"Fetching page {page}/{TOTAL_PAGES}: {url}")

        try:
            html = fetch_page(url)
        except requests.HTTPError as e:
            print(f"HTTPError on page {page}: {e}")
            break
        except requests.RequestException as e:
            print(f"RequestException on page {page}: {e}")
            break

        links = extract_repo_links(html)
        print(f"  Found {len(links)} candidate links on this page.")

        # 由于同一仓库可能在多页链接中出现（理论上不太可能），这里做去重
        before = len(all_repos)
        all_repos.update(links)
        after = len(all_repos)
        print(f"  Total unique repos so far: {after} (added {after - before})")

        # 简单限速，避免触发速率限制
        time.sleep(0.5)

    print(f"总共提取到 {len(all_repos)} 个仓库地址。")

    # 保存输出
    save_to_csv(sorted(all_repos), out_path="kanripo_repositories.csv")

if __name__ == "__main__":
    main()
