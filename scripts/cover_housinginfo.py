import os
import shutil

SRC_DIR = "media/announcements/merged_by_name"
DST_DIR = "media/announcements/housing_info"

def overwrite_files(src, dst):
    if not os.path.exists(src):
        print(f"❌ 소스 폴더가 존재하지 않음: {src}")
        return
    if not os.path.exists(dst):
        print(f"❌ 대상 폴더가 존재하지 않음: {dst}")
        return

    for filename in os.listdir(src):
        if filename.endswith(".json"):
            src_path = os.path.join(src, filename)
            dst_path = os.path.join(dst, filename)
            shutil.copy2(src_path, dst_path)
            print(f"✅ 덮어씀: {filename}")

    print("🎉 모든 파일 덮어쓰기 완료!")

if __name__ == "__main__":
    overwrite_files(SRC_DIR, DST_DIR)
