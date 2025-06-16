<img src="https://github.com/user-attachments/assets/75ec9668-4042-4853-9a51-2398e52cb4e2" width="250" />

### 나에게 맞는 청약 공고와 순위를 한눈에 확인하세요
하우스캔은 **청년을 위한 개인 맞춤형 청약 정보**를 쉽고 빠르게 제공합니다. <br />
AI를 통해 나의 정보를 분석하여 지원 자격에 해당하는지 알 수 있습니다.  <br />
자격이 충족된다면 몇 순위에 해당하는지, 충족되지 않는다면 그 이유를 함께 설명해드립니다.  <br />
청약 공고에 관해 궁금한 점이 생긴다면 언제든 챗봇에게 질문해 보세요!

### 🙌 Participants
<table>
  <tr>
    <td>윤나경
    </td>
    <td>Leader, Design, Frontend</td>
  </tr>
    <td>김하정</td>
    <td>Backend</td>
  </tr>
    <td>이연우</td>
    <td>AI</td>
  </tr>
</table>

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
### 실행 방법 (코드 동작 확인 용)
```
git clone
https://github.com/Houscan-dev/houscan-backend.git
```
```
디렉토리 이동
cd Housman-backend
```
```
가상환경 설치
python -m venv venv 
```
```
가상환경 실행
source venv/Scripts/activate (window)
source venv/bin/activate (Mac/linux)
```
```
필요한 라이브러리 설치
pip install -r requirements.txt
```
```
.env 파일 생성 (발급받은 key값을 추가)
cp .env.example .env
```
```
마이그레이션
python manage.py makemigrations
python manage.py migrate
```
```
런서버 실행
python manage.py runserver
```
### 📆 Development Period
2025.03 - 2025.06
<br/>
> 본 프로젝트는 2025년 성신여자대학교 AI융합학부 캡스톤디자인 프로젝트입니다.
