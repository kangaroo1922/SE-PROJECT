from flask import Flask, request, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.3.5")
db = client["wholeDB"]
vendors = db["vendor_credentials"]

@app.route('/')
def home():
    return render_template('vendorSignUp.html')

@app.route('/vendorSignUp', methods=['POST'])
def vendor_signup():
    userName = request.form.get('userName')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    if not userName or not password or not confirm:
        return render_template('vendorSignUp.html', message="⚠️ Please fill in all fields.")
    if password != confirm:
        return render_template('vendorSignUp.html', message="⚠️ Passwords do not match.")
    if vendors.find_one({"userName": userName}):
        return render_template('vendorSignUp.html', message=f"⚠️ Vendor '{userName}' already exists!")

    vendors.insert_one({"userName": userName, "password": password})
    return render_template('vendorSignUp.html', message=f"✅ Vendor '{userName}' registered successfully!")


@app.route('/vendorLogin' , methods=['GET' ,'POST'])
def vendor_login():
    if request.method == 'POST':
            userName = request.form.get('userName')
            password = request.form.get('password')
            if not userName or not password:
                return render_template('vendorLogin.html' , message="Please enter both username and password.")
            #database fetching
            vendor_doc = vendors.find_one({
            "userName": userName,
            "password": password
            })
        #checking for the validity of the extracted usernames and passwords
            if vendor_doc:
            #login successful ho gaya boyss
                return render_template('vendorLogin.html', message = "Login successful!")
            else:
                return render_template('vendorLogin.html', message = "Login failed credentials do not match!")
    return render_template('vendorLogin.html', message=None)
if __name__ == '__main__':
    app.run(debug=True)
