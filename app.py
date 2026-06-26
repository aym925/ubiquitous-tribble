from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# واجهة الموقع (HTML + CSS) مدمجة داخل الكود لتسهيل الرفع على Vercel
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مستخرج نقاط متمدرس</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 30px auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        h2 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 25px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-sizing: border-box;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
            border-left: 5px solid #f5c6cb;
        }
        .loading {
            text-align: center;
            display: none;
            font-size: 16px;
            color: #e67e22;
            margin-top: 15px;
            font-weight: bold;
        }
        .results {
            margin-top: 30px;
            display: none;
        }
        .info-box {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-right: 5px solid #3498db;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: right;
        }
        th {
            background-color: #2c3e50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>🔐 تسجيل الدخول - مسار متمدرس</h2>
    
    <div id="error-msg" class="error"></div>

    <form id="login-form">
        <div class="form-group">
            <label for="username">اسم المستخدم (Taalim.ma):</label>
            <input type="text" id="username" placeholder="مثال: D123456789@taalim.ma" required>
        </div>
        <div class="form-group">
            <label for="password">كلمة السر:</label>
            <input type="password" id="password" placeholder="••••••••" required>
        </div>
        <button type="submit" id="submit-btn">جلب نقاط المراقبة المستمرة</button>
    </form>

    <div id="loading-msg" class="loading">⏳ جاري الاتصال بخادم مسار واستخراج البيانات... يرجى الانتظار (قد يستغرق دقيقة)</div>

    <div id="results-box" class="results">
        <div class="info-box">
            <h3>🏫 معلومات التلميذ والمؤسسة:</h3>
            <p id="school-name"></p>
            <p id="student-level"></p>
            <p id="semester-info"></p>
        </div>

        <h3>📊 جدول النقط:</h3>
        <table id="notes-table">
            <thead>
                <tr>
                    <th>المادة</th>
                    <th>الفرض 1</th>
                    <th>الفرض 2</th>
                    <th>الفرض 3</th>
                    <th>الفرض 4</th>
                    <th>الأنشطة</th>
                </tr>
            </thead>
            <tbody id="notes-body">
                </tbody>
        </table>
    </div>
</div>

<script>
document.getElementById('login-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');
    const loadingMsg = document.getElementById('loading-msg');
    const resultsBox = document.getElementById('results-box');
    const submitBtn = document.getElementById('submit-btn');
    const notesBody = document.getElementById('notes-body');
    
    // إعادة تعيين الواجهة
    errorMsg.style.display = 'none';
    resultsBox.style.display = 'none';
    loadingMsg.style.display = 'block';
    submitBtn.disabled = true;
    notesBody.innerHTML = '';

    // إرسال الطلب إلى الـ API الداخلي للسكربت
    fetch(`/get-notes?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`)
    .then(response => response.json())
    .then(data => {
        loadingMsg.style.display = 'none';
        submitBtn.disabled = false;
        
        if (data.status === 'success') {
            // ملء معلومات المؤسسة
            const info = data.data.school_info;
            document.getElementById('school-name').innerText = `المؤسسة: ${info['المؤسسة'] || '-'}`;
            document.getElementById('student-level').innerText = `المستوى: ${info['المستوى'] || '-'}`;
            document.getElementById('semester-info').innerText = `الفصل: ${info['الفصل'] || '-'}`;
            
            // ملء جدول النقاط
            const notes = data.data.notes;
            for (const [subject, marks] of Object.entries(notes)) {
                const row = `<tr>
                    <td><strong>${subject}</strong></td>
                    <td>${marks['الفرض الأول'] || '-'}</td>
                    <td>${marks['الفرض الثاني'] || '-'}</td>
                    <td>${marks['الفرض الثالث'] || '-'}</td>
                    <td>${marks['الفرض الرابع'] || '-'}</td>
                    <td>${marks['الأنشطة المندمجة'] || '-'}</td>
                </tr>`;
                notesBody.innerHTML += row;
            }
            
            resultsBox.style.display = 'block';
        } else {
            errorMsg.innerText = data.message;
            errorMsg.style.display = 'block';
        }
    })
    .catch(err => {
        loadingMsg.style.display = 'none';
        submitBtn.disabled = false;
        errorMsg.innerText = '❌ حدث خطأ أثناء الاتصال بالسيرفر، أعد المحاولة.';
        errorMsg.style.display = 'block';
    });
});
</script>

</body>
</html>
"""

@app.route('/')
def home():
    """عرض صفحة تسجيل الدخول الواجهة الرسومية"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/get-notes')
def get_notes():
    """خلفية جلب البيانات (API)"""
    username = request.args.get('username')
    password = request.args.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': '❌ يجب إدخال اسم المستخدم وكلمة المرور'}), 400
    
    try:
        session = requests.Session()
        login_url = "https://moutamadris.men.gov.ma/moutamadris/Account"
        
        headers_get = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Cache-Control': "max-age=0",
            'Upgrade-Insecure-Requests': "1",
            'Referer': "https://moutamadris.men.gov.ma/moutamadris/Account",
            'Accept-Language': "ar,fr;q=0.9,en;q=0.8",
        }
        
        response = session.get(login_url, headers=headers_get, timeout=30)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        
        if not token_input:
            return jsonify({'status': 'error', 'message': '❌ فشل في استخراج التوكن (قد يكون السيرفر محظوراً حالياً من متمدرس)'}), 500
        
        token = token_input['value']
        
        payload = {
            '__RequestVerificationToken': token,
            'UserName': username,
            'Password': password
        }
        
        headers_post = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "max-age=0",
            'Upgrade-Insecure-Requests': "1",
            'Origin': "https://moutamadris.men.gov.ma",
            'Referer': login_url,
            'Accept-Language': "ar,fr;q=0.9,en;q=0.8",
        }
        
        response_login = session.post(login_url, data=payload, headers=headers_post, allow_redirects=False, timeout=30)
        
        if response_login.status_code == 302:
            redirect_url = response_login.headers.get('Location')
            if redirect_url:
                if not redirect_url.startswith('http'):
                    redirect_url = "https://moutamadris.men.gov.ma" + redirect_url
                session.get(redirect_url, headers=headers_get, timeout=30)
                
        elif "اسم المستخدم أو كلمة المرور غير صالحة" in response_login.text:
            return jsonify({'status': 'error', 'message': '❌ اسم المستخدم أو كلمة المرور غير صالحة'}), 401
        else:
            return jsonify({'status': 'error', 'message': f'❌ فشل تسجيل الدخول - الحالة: {response_login.status_code}'}), 500
        
        notes_url = "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetBulletins"
        
        payload_notes = {
            'Annee': '2025',
            'IdSession': '2'
        }
        
        headers_notes = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept-Encoding': "gzip, deflate, br",
            'X-Requested-With': "XMLHttpRequest",
            'Origin': "https://moutamadris.men.gov.ma",
            'Referer': "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetNotesEleve",
            'Accept-Language': "ar,fr;q=0.9,en;q=0.8",
        }
        
        response_notes = session.post(notes_url, data=payload_notes, headers=headers_notes, timeout=30)
        
        if response_notes.status_code == 200:
            soup_notes = BeautifulSoup(response_notes.text, 'html.parser')
            
            info = soup_notes.find_all('dd')
            school_info = {}
            if len(info) >= 4:
                school_info = {
                    'المؤسسة': info[0].text.strip(),
                    'المستوى': info[1].text.strip(),
                    'الفصل': info[2].text.strip(),
                    'عدد_التلاميذ': info[3].text.strip()
                }
            
            table = soup_notes.find('table', class_='grid-table')
            notes_data = {}
            
            if table:
                rows = table.find_all('tr')[1:]
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
                return jsonify({'status': 'error', 'message': '❌ لم يتم العثور على جدول النقاط أو تم حظر السيرفر من طرف متمدرس'}), 404
        else:
            return jsonify({'status': 'error', 'message': f'❌ فشل في جلب النقاط - الحالة: {response_notes.status_code}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'status': 'error', 'message': '❌ انتهت مهلة الاتصال - خادم مسار بطيء جداً أو قام بحظر السيرفر'}), 504
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'❌ حدث خطأ داخلي: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
