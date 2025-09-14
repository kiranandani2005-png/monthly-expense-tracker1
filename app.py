from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USERS_FILE = 'data/users.json'
TRANSACTIONS_FILE = 'data/transactions.json'

# Admin credentials
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

# ----------------- Utility Functions -----------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# ----------------- Routes -----------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------- USER AUTH ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        users = load_json(USERS_FILE)

        if phone in users and users[phone]['password'] == password:
            session['phone'] = phone
            session['username'] = users[phone]['username']
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials"

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        phone = request.form['phone']
        username = request.form['username']
        email = request.form['email']
        aadhaar = request.form['aadhaar']
        password = request.form['password']

        users = load_json(USERS_FILE)

        if phone in users:
            error = "Phone already registered"
        else:
            users[phone] = {
                "username": username,
                "email": email,
                "aadhaar": aadhaar,
                "password": password
            }
            save_json(users, USERS_FILE)
            transactions = load_json(TRANSACTIONS_FILE)
            transactions[phone] = []
            save_json(transactions, TRANSACTIONS_FILE)
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = ""
    password = None
    if request.method == 'POST':
        phone = request.form['phone']
        email = request.form['email']
        aadhaar = request.form['aadhaar']

        users = load_json(USERS_FILE)
        if phone in users and users[phone]['email'] == email and users[phone]['aadhaar'] == aadhaar:
            password = users[phone]['password']
        else:
            error = "User not found or details incorrect"

    return render_template('forgot_password.html', error=error, password=password)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- ADMIN AUTH ----------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid admin credentials"

    return render_template('admin_login.html', error=error)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# ---------- USER DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'phone' not in session:
        return redirect(url_for('login'))

    phone = session['phone']
    username = session['username']
    transactions = load_json(TRANSACTIONS_FILE).get(phone, [])

    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = income - expense

    return render_template('dashboard.html', username=username, transactions=transactions,
                           income=income, expense=expense, balance=balance)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'phone' not in session:
        return redirect(url_for('login'))

    phone = session['phone']
    transactions = load_json(TRANSACTIONS_FILE)
    user_txns = transactions.get(phone, [])

    t_type = request.form['type']
    amount = float(request.form['amount'])
    note = request.form['note']
    now = datetime.now()

    txn = {
        'type': t_type,
        'amount': amount,
        'note': note,
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'month': now.strftime('%B'),
        'year': now.year
    }

    user_txns.append(txn)
    transactions[phone] = user_txns
    save_json(transactions, TRANSACTIONS_FILE)
    return redirect(url_for('dashboard'))

# ---------- GRAPHS ----------
@app.route('/graphs')
def graphs():
    if 'phone' not in session:
        return redirect(url_for('login'))
    return render_template('graphs.html', username=session['username'])

@app.route('/get_transactions')
def get_transactions():
    if 'phone' not in session:
        return jsonify([])

    phone = session['phone']
    transactions = load_json(TRANSACTIONS_FILE)
    return jsonify(transactions.get(phone, []))

@app.route('/compare')
def compare():
    if 'phone' not in session:
        return redirect(url_for('login'))

    phone = session['phone']
    transactions = load_json(TRANSACTIONS_FILE).get(phone, [])

    now = datetime.now()
    this_month = now.strftime('%B')
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%B')

    this_total = sum(t['amount'] if t['type'] == 'income' else -t['amount']
                     for t in transactions if t['month'] == this_month and t['year'] == now.year)

    last_total = sum(t['amount'] if t['type'] == 'income' else -t['amount']
                     for t in transactions if t['month'] == last_month and t['year'] == now.year)

    diff = this_total - last_total
    status = "Profit" if diff > 0 else "Loss" if diff < 0 else "Same"

    return jsonify({
        'this_month_total': this_total,
        'last_month_total': last_total,
        'difference': diff,
        'status': status
    })

# ---------- ADMIN PAGE ----------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    users = load_json(USERS_FILE)
    transactions = load_json(TRANSACTIONS_FILE)
    return render_template('admin.html', users=users, transactions=transactions)

@app.route('/delete_user/<phone>')
def delete_user(phone):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    users = load_json(USERS_FILE)
    transactions = load_json(TRANSACTIONS_FILE)

    users.pop(phone, None)
    transactions.pop(phone, None)

    save_json(users, USERS_FILE)
    save_json(transactions, TRANSACTIONS_FILE)

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
