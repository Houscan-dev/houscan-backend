# 프로젝트 루트/scripts/add_announcement_id.py
import os, json, re
from django.conf import settings
from announcements.models import Announcement


def run():
    print("▶️ 시작: JSON 파일에 announcement_id를 추가합니다")

    DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')
    DOC_TYPES = [ t for t, _ in Announcement._meta.get_field('documents').related_model.ANNOUNCE_TYPES ]

    for doc_type in DOC_TYPES:
        folder = os.path.join(DATA_ROOT, doc_type)
        if not os.path.isdir(folder):
            print(f"  ⚠️ 폴더 없음: {folder}")
            continue

        for fname in os.listdir(folder):
            if not fname.endswith('.json'):
                continue
            base = re.sub(rf'_{doc_type}\.json$', '', fname)

            qs = Announcement.objects.filter(title=base)
            if qs.count() != 1:
                print(f"  ❌ 매칭 실패 ({qs.count()}건): {base}")
                continue
            ann = qs.first()

            path = os.path.join(folder, fname)
            with open(path, 'r+', encoding='utf-8') as fp:
                data = json.load(fp)
                data['announcement_id'] = ann.id
                fp.seek(0)
                json.dump(data, fp, ensure_ascii=False, indent=2)
                fp.truncate()

            print(f"  ✅ [{doc_type}] {fname} → announcement_id={ann.id}")

    print("✅ add_announcement_id 완료!")