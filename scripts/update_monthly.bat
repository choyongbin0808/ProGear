@echo off
rem ProGear 월 1회 데이터 갱신 (Windows 작업 스케줄러에 등록해서 사용)
rem 연락처를 넣으려면 아래 줄의 rem을 지우고 이메일을 적으세요.
rem set PROGEAR_CONTACT=your-email@example.com
rem Supabase에 자동으로 올리려면 scripts\secrets.bat 파일을 만들고 아래 두 줄을 적으세요. (git에 올라가지 않는 파일)
rem   set SUPABASE_URL=https://<프로젝트 id>.supabase.co
rem   set SUPABASE_SECRET_KEY=<secret 키>
cd /d "%~dp0.."
if exist scripts\secrets.bat call scripts\secrets.bat
py scripts\update_all.py >> scripts\work\update.log 2>&1
