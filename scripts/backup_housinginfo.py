import shutil
import os
from datetime import datetime

HOUSING_INFO_DIR = "media/announcements/housing_info"
BACKUP_BASE_DIR = "media/announcements/backup_housing_info"

def backup_housing_info():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_BASE_DIR, f"backup_{timestamp}")

    # backup_dir 존재 여부 체크
    if os.path.exists(backup_dir):
        print(f"❗ 백업 폴더가 이미 존재합니다: {backup_dir}")
        return

    # copytree가 직접 새 폴더 생성
    shutil.copytree(HOUSING_INFO_DIR, backup_dir)

    print(f"✅ 백업 완료: {backup_dir}")

if __name__ == "__main__":
    backup_housing_info()
