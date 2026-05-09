from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"

def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Admin(id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    cur.execute("INSERT OR IGNORE INTO Admin(id, username, password) VALUES (1,'admin','admin')")
    cur.execute("""CREATE TABLE IF NOT EXISTS LandOwner(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, password TEXT,
        aadhaar TEXT, patta TEXT, ec TEXT, status TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS Land(
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, location TEXT, price INTEGER, status TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS User(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, password TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS Booking(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, land_id INTEGER,
        hours INTEGER, amount INTEGER, payment TEXT)""")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/owner_register', methods=['GET','POST'])
def owner_register():
    if request.method == 'POST':
        data = (request.form['name'], request.form['phone'], request.form['password'],
                request.form['aadhaar'], request.form['patta'], request.form['ec'], 'Pending')
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO LandOwner(name,phone,password,aadhaar,patta,ec,status) VALUES (?,?,?,?,?,?,?)", data)
        conn.commit(); conn.close()
        return render_template('message.html', msg="Registered! Wait for admin approval.", link="/owner_login", link_text="Go to Login")
    return render_template('owner_register.html')

@app.route('/owner_login', methods=['GET','POST'])
def owner_login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM LandOwner WHERE phone=? AND password=? AND status='Approved'",
                    (request.form['phone'], request.form['password']))
        user = cur.fetchone(); conn.close()
        if user:
            session['owner_id'] = user[0]
            return redirect('/add_land')
        else:
            return render_template('message.html', msg="Not approved or invalid login.", link="/owner_login", link_text="Try Again")
    return render_template('owner_login.html')

@app.route('/add_land', methods=['GET','POST'])
def add_land():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO Land(owner_id,location,price,status) VALUES (?,?,?,'Pending')",
                    (session['owner_id'], request.form['location'], request.form['price']))
        conn.commit(); conn.close()
        return render_template('message.html', msg="Land added. Waiting for admin approval.", link="/add_land", link_text="Add More")
    return render_template('add_land.html')

@app.route('/user_register', methods=['GET','POST'])
def user_register():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO User(name,phone,password) VALUES (?,?,?)",
                    (request.form['name'], request.form['phone'], request.form['password']))
        conn.commit(); conn.close()
        return redirect('/user_login')
    return render_template('user_register.html')

@app.route('/user_login', methods=['GET','POST'])
def user_login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE phone=? AND password=?",
                    (request.form['phone'], request.form['password']))
        user = cur.fetchone(); conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect('/search_land')
        else:
            return render_template('message.html', msg="Invalid login.", link="/user_login", link_text="Try Again")
    return render_template('user_login.html')

@app.route('/search_land', methods=['GET','POST'])
def search_land():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if request.method == 'POST':
        loc = request.form['location']
        cur.execute("SELECT * FROM Land WHERE location LIKE ? AND status='Approved'", ('%'+loc+'%',))
    else:
        cur.execute("SELECT * FROM Land WHERE status='Approved'")
    lands = cur.fetchall(); conn.close()
    return render_template('search_land.html', lands=lands)

@app.route('/book/<int:land_id>', methods=['GET','POST'])
def book(land_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM Land WHERE id=?", (land_id,))
    land = cur.fetchone()
    if request.method == 'POST':
        hours = int(request.form['hours'])
        amount = hours * land[3]
        cur.execute("INSERT INTO Booking(user_id,land_id,hours,amount,payment) VALUES (?,?,?,?,?)",
                    (session['user_id'], land_id, hours, amount, "Paid"))
        conn.commit(); conn.close()
        return render_template('message.html', msg=f"Booking successful! Total: ₹{amount}. Pay to: 9876543210", link="/search_land", link_text="Back to Search")
    conn.close()
    return render_template('book.html', land=land)

@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM Admin WHERE username=? AND password=?",
                    (request.form['username'], request.form['password']))
        admin = cur.fetchone(); conn.close()
        if admin:
            session['admin'] = True
            return redirect('/admin_dashboard')
        else:
            return render_template('message.html', msg="Invalid admin credentials.", link="/admin_login", link_text="Try Again")
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM LandOwner WHERE status='Pending'")
    owners = cur.fetchall()
    cur.execute("SELECT * FROM Land WHERE status='Pending'")
    lands = cur.fetchall()
    cur.execute("SELECT * FROM Booking")
    bookings = cur.fetchall()
    conn.close()
    return render_template('dashboard_admin.html', owners=owners, lands=lands, bookings=bookings)

@app.route('/approve_owner/<int:id>')
def approve_owner(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE LandOwner SET status='Approved' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin_dashboard')

@app.route('/reject_owner/<int:id>')
def reject_owner(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE LandOwner SET status='Rejected' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin_dashboard')

@app.route('/approve_land/<int:id>')
def approve_land(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE Land SET status='Approved' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin_dashboard')

@app.route('/reject_land/<int:id>')
def reject_land(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE Land SET status='Rejected' WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/admin_dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
