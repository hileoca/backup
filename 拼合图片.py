import os
from PIL import Image

# 配置
base_dir = r"D:\images"            # 分块所在目录
output_dir = r"D:\images\output"   # 拼合后图片输出目录
chunk_prefix = ""                    # 若分块命名没有前缀，则留空；若有前缀请在此填充
# 文件命名规则示例：001-1.jpg, 001-2.jpg, ..., 133-8.jpg
# 这里假设实际文件名中没有扩展名，或使用 .jpg 作为实际扩展名
# 本示例为每图片分为上下2行各4块共8块

# 支持两种可能的文件命名形式：
# 1) exactly "001-1" 等（无扩展名），可用 os.path.splitext 去扩展名
# 2) "001-1.jpg" 之类，需处理扩展名

def collect_chunks(base_dir):
    """
    收集所有分块，按大图编号分组。
    返回字典: { "001": [path_to_chunk1, path_to_chunk2, ..., path_to_chunk8], ... }
    """
    groups = {}
    for fname in os.listdir(base_dir):
        if fname.startswith('.'):
            continue
        path = os.path.join(base_dir, fname)
        if not os.path.isfile(path):
            continue

        name, ext = os.path.splitext(fname)
        if ext.lower() not in {'.jpg', '.jpeg', ''}:
            # 允许没有扩展名，或扩展名为 jpg/jpeg
            pass

        # 解析成 “大图编号-分块编号”
        # 例如 "001-1.jpg" -> id_part="001", chunk_no=1
        if '-' in name:
            id_part, chunk_part = name.split('-', 1)
            # 只处理合法的 3 位大图编号和 1-8 的分块编号
            if len(id_part) == 3 and chunk_part.isdigit():
                chunk_no = int(chunk_part)
                if 1 <= chunk_no <= 8:
                    # 规范化为 3 位编号
                    big_id = id_part
                    groups.setdefault(big_id, []).append((chunk_no, path))
    # 将每个大图的分块按 chunk_no 排序
    for big_id in list(groups.keys()):
        blocks = sorted(groups[big_id], key=lambda x: x[0])
        # 只保留路径，且确保有 8 块
        blocks_paths = [p for _, p in blocks]
        if len(blocks_paths) != 8:
            print(f"Warning: 大图 {big_id} 共有 {len(blocks_paths)} 个分块，预期 8 个。跳过该大图。")
            del groups[big_id]
        else:
            groups[big_id] = blocks_paths
    return groups

def ensure_output_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def merge_chunks_for_big(big_id, chunk_paths, output_dir):
    """
    给定一个大图编号 big_id 和其 8 块分块路径，按要求拼接并保存为 {big_id}.jpg
    chunk_paths 应该是长度为 8 的列表，按顺序对应 1-8。
    """
    images = []
    for cp in chunk_paths:
        try:
            img = Image.open(cp)
            # 如需要，可以统一转换到 RGBA 或 RGB
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)
        except Exception as e:
            print(f"Error opening chunk {cp} for {big_id}: {e}")
            return False

    # 每张大图的分块尺寸相同，拿第一张的尺寸
    w, h = images[0].size

    # 需要确认分块排布：
    # 1-4 为第一行，5-8 为第二行
    row1 = images[0:4]
    row2 = images[4:8]

    # 横向拼接：将每行的四块拼成一张大图的一半宽度
    def horizontal_concat(img_list):
        total_width = sum(img.size[0] for img in img_list)
        max_height = max(img.size[1] for img in img_list)
        # 假设所有高度相同，否则取最大值并居中
        new_im = Image.new("RGB", (total_width, max_height))
        x_offset = 0
        for im in img_list:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]
        return new_im

    row1_img = horizontal_concat(row1)
    row2_img = horizontal_concat(row2)

    # 竖向拼接：将两行拼在一起
    final_width = max(row1_img.size[0], row2_img.size[0])
    final_height = row1_img.size[1] + row2_img.size[1]

    final_img = Image.new("RGB", (final_width, final_height))
    final_img.paste(row1_img, (0, 0))
    final_img.paste(row2_img, (0, row1_img.size[1]))

    # 保存
    out_path = os.path.join(output_dir, f"{big_id}.jpg")
    try:
        final_img.save(out_path, format="JPEG")
        print(f"Saved: {out_path}")
        return True
    except Exception as e:
        print(f"Error saving {out_path}: {e}")
        return False
    finally:
        # 释放内存
        for im in images:
            im.close()
        final_img.close()
        row1_img.close()
        row2_img.close()

def main():
    ensure_output_dir(output_dir)
    groups = collect_chunks(base_dir)
    total = len(groups)
    print(f"发现大图分块组数: {total}")

    success_count = 0
    for big_id, paths in sorted(groups.items()):
        ok = merge_chunks_for_big(big_id, paths, output_dir)
        if ok:
            success_count += 1

    print(f"拼接完成。成功 {success_count} 张，失败 {total - success_count} 张。")

if __name__ == "__main__":
    main()
