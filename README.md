<img src="https://github.com/user-attachments/assets/75ec9668-4042-4853-9a51-2398e52cb4e2" width="250" />

### 나에게 맞는 청약 공고와 순위를 한눈에 확인하세요
하우스캔은 **청년을 위한 개인 맞춤형 청약 정보**를 쉽고 빠르게 제공합니다. <br />
AI를 통해 나의 정보를 분석하여 지원 자격에 해당하는지 알 수 있습니다.  <br />
자격이 충족된다면 몇 순위에 해당하는지, 충족되지 않는다면 그 이유를 함께 설명해드립니다.  <br />
청약 공고에 관해 궁금한 점이 생긴다면 언제든 챗봇에게 질문해 보세요!


### 📸 Demo Video
- <a href='https://youtu.be/jyJlv0aYP5U'>시연 영상</a>

### 🗂️ Directory Structure
```
📦 backend-directory
 ┣ 📂announcements
 ┃ ┣ 📜housing_eligibility_analyzer.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tasks.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py
 ┣ 📂houscan
 ┃ ┣ 📜celery.py
 ┃ ┣ 📜settings.py
 ┃ ┣ 📜urls.py
 ┃ ┣ 📜utils.py
 ┃ ┣ 📜views.py
 ┃ ┗ 📜wsgi.py
 ┣ 📂profiles
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜signals.py
 ┃ ┣ 📜tasks.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py
 ┣ 📂scripts
 ┃ ┣ 📜add_announcements_id.py
 ┃ ┣ 📜add_id_housing_info.py
 ┃ ┣ 📜create_announcements.py
 ┃ ┣ 📜import_housing_info_to_db.py
 ┃ ┣ 📜load_announcements.py
 ┗ 📂users
 ┃ ┣ 📜authentication.py
 ┃ ┣ 📜backends.py
 ┃ ┣ 📜models.py
 ┃ ┣ 📜serializers.py
 ┃ ┣ 📜tests.py
 ┃ ┣ 📜urls.py
 ┃ ┗ 📜views.py

```
### 📆 Development Period
2025.03 - 2025.06
<br/>
> 본 프로젝트는 2025년 성신여자대학교 AI융합학부 캡스톤디자인 프로젝트입니다.

```
houscan
├─ Pipfile
├─ Pipfile.lock
├─ README.md
├─ analyzer.py
├─ announcements
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ management
│  │  ├─ __init__.py
│  │  └─ commands
│  │     ├─ __init__.py
│  │     ├─ import_ai_summary.py
│  │     └─ update_titles_from_json.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_alter_housinginfo_type.py
│  │  ├─ 0003_alter_housinginfo_house_type_and_more.py
│  │  ├─ 0004_housingeligibilityanalysis.py
│  │  ├─ 0005_alter_announcementdocument_data_file.py
│  │  ├─ 0006_housingeligibilityanalysis_reasons_and_more.py
│  │  ├─ 0007_announcement_ai_summary_json_and_more.py
│  │  ├─ 0008_rename_posted_date_announcement_announcement_date.py
│  │  ├─ 0009_alter_announcement_announcement_date.py
│  │  ├─ 0010_alter_housinginfo_id.py
│  │  ├─ 0011_remove_housinginfo_house_type_and_more.py
│  │  ├─ 0012_housinginfo_house_type_housinginfo_supply_households_and_more.py
│  │  ├─ 0013_alter_housinginfo_type.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ services
│  │  └─ eligibility_service.py
│  ├─ tasks.py
│  ├─ urls.py
│  └─ views.py
├─ chroma_db
├─ extracted_json
│  ├─ (2022__1차)은평구 청년 창업인의 집 1호점_2호점 입주자 모집 공고문(최종).json
│  ├─ 1_ [공고문] 2020-3차 청년 매입임대주택 입주자모집 공고문(홈페이지 공개용).json
│  ├─ 1_ [공고문] 2021년 2차 청년 매입임대주택 입주자모집(2021_12_30_) 공고문_홈페이지 공개용.json
│  ├─ 1_ [공고문] 2022년 2차 청년 매입임대주택 입주자모집공고문(홈페이지 공개용)(1).json
│  ├─ 1_[공고문] 2023년 2차 청년 매입임대주택 입주자모집공고문(홈페이지 공개용)(수정).json
│  ├─ 2019-2차 역세권청년주택(공공임대) 입주자모집공고문(1101).json
│  ├─ 2020년 제1차역세권청년주택(공공임대) 입주자모집 공고문_웹용.json
│  ├─ 2020년 청년창업인 임대주택 입주자 모집공고.json
│  ├─ 2020년 청년창업인 임대주택 입주자 모집공고문(재공급).json
│  ├─ 2023년 1차 행복주택 입주자 모집 공고문(2023_ 6_ 28_)(최종).json
│  ├─ 2023년 2차 청년안심주택(구_역세권청년주택) 공고문-웹 게시용.json
│  ├─ 2023년 3차 청년안심주택-공고문-웹용(최종).json
│  ├─ 2024년 2차 청년안심주택 공고문-최종(웹용).json
│  ├─ [공고문] 2020-2차 청년 매입임대주택 입주자모집 공고.json
│  ├─ [공고문] 청년 매입임대주택 신규세대 입주자 모집 공고(2019_12_24_) 공고문.json
│  ├─ [마을과집]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250307.json
│  ├─ [수정] 2024년 1차 청년안심주택 공고문-최종(웹용).json
│  ├─ [한지붕협동조합]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250308.json
│  ├─ [한지붕협동조합]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250324.json
│  ├─ [한지붕협동조합]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250407_독산동 913.json
│  ├─ [한지붕협동조합]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250407_시흥동824-16.json
│  ├─ [협동조합 큰바위얼굴]SH특화형 매입임대주택(청년) 입주자 모집 공고문_20250403.json
│  ├─ 제3차 청년안심주택-공고문(웹용)최종.json
│  ├─ 강동구 청년가죽창작마을 입주자 모집 공고문(2017_09_12_공고).json
│  ├─ 도봉구 청년도전숙 잔여세대 입주자모집공고문(2019_08_23_).json
│  └─ 역세권청년주택 입주자모집공고문(종로구 숭인동 207-32_공공임대).json
├─ houscan
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ celery.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ utils.py
│  ├─ views.py
│  └─ wsgi.py
├─ manage.py
├─ media
│  └─ announcements
│     └─ announcement_titles_by_id.json
├─ profiles
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_initial.py
│  │  ├─ 0003_profile_is_eligible_profile_priority_info.py
│  │  ├─ 0004_remove_profile_is_eligible_and_more.py
│  │  ├─ 0005_profile_is_eligible_profile_priority_info.py
│  │  ├─ 0006_profile_is_married_profile_residence.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ signals.py
│  ├─ tasks.py
│  ├─ urls.py
│  └─ views.py
├─ requirements.txt
├─ scripts
│  └─ data
│     └─ announcement_title_update_map.json
├─ static
├─ titles.json
├─ update_ann.sql
└─ users
   ├─ __init__.py
   ├─ admin.py
   ├─ apps.py
   ├─ authentication.py
   ├─ backends.py
   ├─ migrations
   │  ├─ 0001_initial.py
   │  └─ __init__.py
   ├─ models.py
   ├─ serializers.py
   ├─ tests.py
   ├─ urls.py
   └─ views.py

```