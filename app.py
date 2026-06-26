from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime

app = Flask(__name__)

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        'status': 'success',
        'message': '✅ نقاطي API - استخراج نقاط متمدرسين',
        'endpoints': {
            '/': 'الصفحة الرئيسية',
            '/get-notes?username=...&password=...': 'جلب النقاط'
        },
        'example': '/get-notes?username=D166027860@taalim.ma&password=AYMNaymn@1234'
    })

@app.route('/get-notes')
def get_notes():
    """جلب نقاط المراقبة المستمرة"""
    
    # جلب المعاملات
    username = request.args.get('username')
    password = request.args.get('password')
    
    # التحقق من وجود البيانات
    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': '❌ يجب إدخال اسم المستخدم وكلمة المرور',
            'usage': '/get-notes?username=USERNAME&password=PASSWORD'
        }), 400
    
    try:
        # ====== 1. إنشاء جلسة جديدة ======
        session = requests.Session()
        
        # ====== 2. جلب صفحة تسجيل الدخول ======
        login_url = "https://moutamadris.men.gov.ma/moutamadris/Account"
        
        headers_get = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 9; Pixel 4 Build/PQ3A.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/81.0.4044.117 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            'Accept-Encoding': "gzip, deflate",
            'Cache-Control': "max-age=0",
            'Upgrade-Insecure-Requests': "1",
            'Referer': "https://moutamadris.men.gov.ma/moutamadris/Account",
            'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        response = session.get(login_url, headers=headers_get, timeout=30)
        
        # استخراج التوكن
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        
        if not token_input:
            return jsonify({
                'status': 'error',
                'message': '❌ فشل في استخراج التوكن'
            }), 500
        
        token = token_input['value']
        
        # ====== 3. تسجيل الدخول ======
        payload = {
            '__RequestVerificationToken': token,
            'UserName': username,
            'Password': password
        }
        
        headers_post = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 9; Pixel 4 Build/PQ3A.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/81.0.4044.117 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            'Accept-Encoding': "gzip, deflate",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "max-age=0",
            'Upgrade-Insecure-Requests': "1",
            'Origin': "https://moutamadris.men.gov.ma",
            'Referer': login_url,
            'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        response_login = session.post(login_url, data=payload, headers=headers_post, allow_redirects=False, timeout=30)
        
        # التحقق من النتيجة
        if response_login.status_code == 302:
            # متابعة التوجيه إلى Dashboard
            redirect_url = response_login.headers.get('Location')
            if redirect_url:
                if not redirect_url.startswith('http'):
                    redirect_url = "https://moutamadris.men.gov.ma" + redirect_url
                session.get(redirect_url, headers=headers_get, timeout=30)
                
        elif "اسم المستخدم أو كلمة المرور غير صالحة" in response_login.text:
            return jsonify({
                'status': 'error',
                'message': '❌ اسم المستخدم أو كلمة المرور غير صالحة'
            }), 401
        else:
            return jsonify({
                'status': 'error',
                'message': f'❌ فشل تسجيل الدخول - الحالة: {response_login.status_code}'
            }), 500
        
        # ====== 4. جلب النقاط ======
        notes_url = "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetBulletins"
        
        payload_notes = {
            'Annee': '2025',
            'IdSession': '2'
        }
        
        headers_notes = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 9; Pixel 4 Build/PQ3A.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/81.0.4044.117 Mobile Safari/537.36",
            'Accept-Encoding': "gzip, deflate",
            'X-Requested-With': "XMLHttpRequest",
            'Origin': "https://moutamadris.men.gov.ma",
            'Referer': "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetNotesEleve",
            'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        response_notes = session.post(notes_url, data=payload_notes, headers=headers_notes, timeout=30)
        
        # ====== 5. استخراج النقاط ======
        if response_notes.status_code == 200:
            soup_notes = BeautifulSoup(response_notes.text, 'html.parser')
            
            # معلومات المؤسسة
            info = soup_notes.find_all('dd')
            school_info = {}
            if len(info) >= 4:
                school_info = {
                    'المؤسسة': info[0].text.strip(),
                    'المستوى': info[1].text.strip(),
                    'الفصل': info[2].text.strip(),
                    'عدد_التلاميذ': info[3].text.strip()
                }
            
            # استخراج النقاط من الجدول
            table = soup_notes.find('table', class_='grid-table')
            notes_data = {}
            
            if table:
                rows = table.find_all('tr')[1:]  # تخطي الرأس
                notes_names = ['الفرض الأول', 'الفرض الثاني', 'الفرض الثالث', 'الفرض الرابع', 'الأنشطة المندمجة']
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 6:
                        subject = cells[0].text.strip()
                        subject_notes = {}
                        
                        for i in range(1, 6):
                            span = cells[i].find('span')
                            if span and span.text.strip():
                                note = span.text.strip().replace(',', '.')
                                subject_notes[notes_names[i-1]] = note
                            else:
                                subject_notes[notes_names[i-1]] = '-'
                        
                        notes_data[subject] = subject_notes
            else:
                return jsonify({
                    'status': 'error',
                    'message': '❌ لم يتم العثور على جدول النقاط'
                }), 404
            
            # ====== 6. إرجاع النتيجة ======
            return jsonify({
                'status': 'success',
                'message': '✅ تم جلب النقاط بنجاح',
                'data': {
                    'school_info': school_info,
                    'notes': notes_data,
                    'timestamp': datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'❌ فشل في جلب النقاط - الحالة: {response_notes.status_code}'
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': '❌ انتهت مهلة الاتصال - الخادم بطيء جداً'
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'error',
            'message': '❌ فشل الاتصال بالسيرفر - تأكد من الانترنت'
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'❌ حدث خطأ: {str(e)}'
        }), 500

if __name__ == "__main__":
    app.run(debug=True)