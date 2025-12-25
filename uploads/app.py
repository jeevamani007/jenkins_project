from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jeeva@123",
        database="hotel_db"
    )

MENU_ITEMS = {
    "Idly": 10,
    " Curd rice": 30,
    "Dosai": 25,
    "Biryani": 100,
    "Chapati": 15
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "Jeeva" and password == "1234":
            session["logged_in"] = True
            return redirect(url_for("home"))  
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/home")
def home():
    return render_template("front.html")

@app.route("/billing", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["customer_name"].strip()
        mobile = request.form["mobile"].strip()
        selected_items = request.form.getlist("item")
        quantities = request.form.getlist("qty")

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO customer_bills (customer_name, mobile) VALUES (%s, %s)", (name, mobile))
        bill_id = cursor.lastrowid

        total = 0
        items = []

        for i in range(len(selected_items)):
            item = selected_items[i]
            qty_str = quantities[i]
            if item in MENU_ITEMS and qty_str.isdigit():
                qty = int(qty_str)
                price = MENU_ITEMS[item]
                subtotal = price * qty
                total += subtotal
                items.append((bill_id, item, price, qty, subtotal))

        ordered_item_names = [item[1] for item in items]
        ordered_items_str = ", ".join(ordered_item_names)

        cursor.executemany(
            "INSERT INTO bill_items (bill_id, item_name, price, qty, subtotal) VALUES (%s, %s, %s, %s, %s)",
            items
        )

        cursor.execute(
            "UPDATE customer_bills SET total_amount = %s, ordered_items = %s WHERE id = %s",
            (total, ordered_items_str, bill_id)
        )

        db.commit()
        db.close()

        return render_template("bill.html", name=name, mobile=mobile, items=items, total=total, date=datetime.now())

    return render_template("index.html", menu=MENU_ITEMS)

@app.route("/view")
def view():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, customer_name, mobile, bill_date, total_amount, ordered_items
        FROM customer_bills
        ORDER BY bill_date DESC
    """)
    bills = cursor.fetchall()
    db.close()
    return render_template("view.html", bills=bills)

@app.route("/delete/<int:bill_id>")
def delete(bill_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM customer_bills WHERE id = %s", (bill_id,))
    db.commit()
    db.close()

    return redirect(url_for('view'))

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

