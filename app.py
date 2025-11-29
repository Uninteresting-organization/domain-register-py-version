from flask import Flask, render_template, request, redirect, url_for, session
import requests
import json
import os

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_for_dev') 

CLIENT_ID = 'YOUR_CLIENT_ID' 
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'http://127.0.0.1:5000/auth/discord/callback'
DISCORD_API_BASE = 'https://discord.com/api/v10'
SCOPES = 'identify email' 
AUTH_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES.replace(' ', '%20')}"

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('register'))
        
    return render_template('login.html', discord_auth_url=AUTH_URL)

@app.route('/auth/discord/callback')
def discord_callback():
    code = request.args.get('code')

    if not code:
        return redirect(url_for('index'))

    try:
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPES
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        token_response = requests.post(
            f"{DISCORD_API_BASE}/oauth2/token",
            data=token_data,
            headers=headers
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')

        user_response = requests.get(
            f"{DISCORD_API_BASE}/users/@me",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_response.raise_for_status()
        user_data = user_response.json()

        session['user_id'] = user_data.get('id')
        session['username'] = user_data.get('username')
        session['email'] = user_data.get('email')
        
        return redirect(url_for('register'))

    except requests.exceptions.HTTPError as e:
        print(f"Discord API 錯誤: {e.response.text}")
        return "Discord 登入失敗，請檢查 Client ID/Secret 和 Redirect URI。", 500
    except Exception as e:
        print(f"登入過程中發生錯誤: {e}")
        return "發生未知錯誤。", 500

@app.route('/register')
def register():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('register.html', 
                           user_id=session['user_id'],
                           user_email=session.get('email', '未提供電子郵件'))

@app.route('/submit-registration', methods=['POST'])
def submit_registration():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    subdomain = request.form.get('subdomain')
    target = request.form.get('target')
    user_id = session['user_id']
    
   
    full_domain = f"{subdomain}.您的主域名.com"
    
    return render_template('success.html', 
                           subdomain=full_domain,
                           target=target,
                           user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True)
