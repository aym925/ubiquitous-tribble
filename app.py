import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# واجهة الموقع الرسومية (HTML + CSS + JavaScript)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مستخرج نقاط متمدرس المغرب</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
            margin: 0;
            padding: 10px;
            color: #1e293b;
            min-height: 100vh;
        }
        .container {
            max-width: 650px;
            margin: 20px auto;
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        h2 {
            text-align: center;
            color: #0369a1;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: #475569;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #cbd5e1;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            transition: border 0.3s;
        }
        input:focus {
            border-color: #0284c7;
            outline: none;
        }
        button {
            width: 100%;
            padding: 14px;
            background-color: #0284c7;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background-color: #0369a1;
        }
        button:disabled {
            background-color: #94a3b8;
            cursor: not-allowed;
        }
        .error {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
            border-right: 4px solid #ef4444;
            font-weight: 500;
        }
        .loading {
            text-align: center;
            display: none;
            font-size: 16px;
            color: #d97706;
            margin-top: 15px;
            font-weight: bold;
            padding: 10px;
            background: #fef3c7;
            border-radius: 8px;
        }
        .results {
            margin-top: 25px;
            display: none;
        }
        .info-box {
            background: #f0f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-right: 4px solid #0284c7;
        }
        .info-box p {
            margin: 5px 0;
            font-size: 15px;
        }
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 15px;
        }
        th, td {
            border: 1px solid #e2e8f0;
            padding: 12px 10px;
            text-align: right;
        }
        th {
            background-color: #0f172a;
            color: white;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f8fafc;
        }
        tr:hover {
            background-color: #f1f5f9;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>🔐 سجل الدخول لاستخراج النقط</h2>
    
    <div id="error-msg" class="error"></div>

    <form id="login-form">
        <div class="form-group">
            <label for="username">اسم المستخدم (Taalim.ma):</label>
            <input type="text" id="username" placeholder="مثال: D136000000@taalim.ma" required>
        </div>
        <div class="form-group">
            <label for="password">كلمة السر (قن مسار):</label>
            <input type="password" id="password" placeholder="••••••••" required>
        </div>
        <button type="submit" id="submit-btn">دخول وجلب النقط</button>
    </form>

    <div id="loading-msg" class="loading">⏳ جاري تسجيل الدخول وقراءة البيانات من مسار... يرجى الانتظار ثواني.</div>

    <div id="results-box" class="results">
        <div class="info-box">
            <h3 style="margin-top:0; color:#0369a1;">🏫 معلومات التلميذ:</h3>
            <p id="school-name"></p>
            <p id="student-level"></p>
            <p id="semester-info"></p>
        </div>

        <h3 style="color:#0f172a;">📊 بيان النقط المستخرجة:</h3>
        <div class="table-container">
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
    
    errorMsg.style.display = 'none';
    resultsBox.style.display = 'none';
    loadingMsg.style.display = 'block';
    submitBtn.disabled = true;
    notesBody.innerHTML = '';

    fetch(`/get-notes?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`)
    .then(response => response.json())
    .then(data => {
        loadingMsg.style.display = 'none';
        submitBtn.disabled = false;
        
        if (data.status === 'success') {
            const info = data.data.school_info;
            document.getElementById('school-name').innerHTML = `<b>المؤسسة:</b> ${info['المؤسسة'] || '-'}`;
            document.getElementById('student-level').innerHTML = `<b>المستوى الدراسي:</b> ${info['المستوى'] || '-'}`;
            document.getElementById('semester-info').innerHTML = `<b>الدورة:</b> ${info['الفصل'] || '-'}`;
            
            const notes = data.data.notes;
            for (const [subject, marks] of Object.entries(notes)) {
                const row = `<tr>
                    <td><b>${subject}</b></td>
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
        errorMsg.innerText = '❌ حدث خطأ أثناء الاتصال بالخادم الداخلي للبرنامج.';
        errorMsg.style.display = 'block';
    });
});
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get-notes')
def get_notes():
    username = request.args.get('username')
    password = request.args.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': '❌ يرجى إدخال الحساب وكلمة المرور'}), 400
    
    try:
        session = requests.Session()
        login_url = "https://moutamadris.men.gov.ma/moutamadris/Account"
        
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Accept-Language': "ar,fr;q=0.9,en;q=0.8",
        }
        
        response = session.get(login_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        
        if not token_input:
            return jsonify({'status': 'error', 'message': '❌ فشل استخراج توكن الحماية، يرجى المحاولة لاحقاً.'}), 500
        
        token = token_input['value']
        
        payload = {
            '__RequestVerificationToken': token,
            'UserName': username,
            'Password': password
        }
        
        response_login = session.post(login_url, data=payload, headers=headers, allow_redirects=False, timeout=20)
        
        if response_login.status_code == 302:
            redirect_url = response_login.headers.get('Location')
            if redirect_url:
                if not redirect_url.startswith('http'):
                    redirect_url = "https://moutamadris.men.gov.ma" + redirect_url
                session.get(redirect_url, headers=headers, timeout=20)
        elif "اسم المستخدم أو كلمة المرور غير صالحة" in response_login.text:
            return jsonify({'status': 'error', 'message': '❌ قن مسار أو اسم المستخدم غير صحيح'}), 401
        else:
            return jsonify({'status': 'error', 'message': '❌ لم يتمكن البرنامج من الدخول للحساب'}), 500
        
        notes_url = "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetBulletins"
        payload_notes = {'Annee': '2025', 'IdSession': '2'}
        
        headers_notes = headers.copy()
        headers_notes.update({
            'X-Requested-With': "XMLHttpRequest",
            'Referer': "https://moutamadris.men.gov.ma/moutamadris/TuteurEleves/GetNotesEleve"
        })
        
        response_notes = session.post(notes_url, data=payload_notes, headers=headers_notes, timeout=20)
        
        if response_notes.status_code == 200:
            soup_notes = BeautifulSoup(response_notes.text, 'html.parser')
            
            info = soup_notes.find_all('dd')
            school_info = {}
            if len(info) >= 4:
                school_info = {
                    'المؤسسة': info[0].text.strip(),
                    'المستوى': info[1].text.strip(),
                    'الفصل': info[2].text.strip()
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
                            note = span.text.strip().replace(',', '.') if span and span.text.strip() else '-'
                            subject_notes[notes_names[i-1]] = note
                        notes_data[subject] = subject_notes
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'school_info': school_info,
                        'notes': notes_data
                    }
                })
            else:
                return jsonify({'status': 'error', 'message': '❌ لم نجد جدول النقط في الحساب حالياً.'}), 404
        else:
            return jsonify({'status': 'error', 'message': '❌ فشل جلب بيانات النقط من خادم مسار'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'خطأ غير متوقع: {str(e)}'}), 500

if __name__ == "__main__":
    # تشغيل السيرفر محلياً على بورت 8080
    app.run(host="0.0.0.0", port=8080)
