from flask import Flask, request, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.3.5")
db = client["wholeDB"]
vendors = db["vendor_credentials"]
users = db["user_credentials"]

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


@app.route('/userSignUp' , methods=['GET' , 'POST'])
def userSignUp():
    if request.method == 'GET':
        return render_template('userSignUp.html' , message=None)
    if request.method == 'POST':
        userName = request.form.get('userName')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if not userName or not password or not confirm:
            return render_template('userSignUp.html', message="Please fill in all fields.")
        if password != confirm:
            return render_template('userSignUp.html', message="Passwords do not match.")
        if users.find_one({"userName": userName}):
            return render_template('userSignUp.html', message="User '{userName}' already exists!")
        users.insert_one({"userName": userName, "password": password})
    return render_template('userSignUp.html',message=None)

@app.route('/userLogin' , methods=['GET' , 'POST'])
def userLogin():
    if request.method == 'GET':
        return render_template('userLogin.html')
    if request.method == 'POST':
        userName = request.form.get('userName')
        password = request.form.get('password')
        if not userName or not password:
            return render_template('userLogin.html' , message="please enter both the username and password")
        user_doc = users.find_one({
            "userName":userName,
            "password":password
        })
        if user_doc:
            return render_template('userLogin.html' , message="Login successful")
        else:
            return render_template('userLogin.html', message="Login failed, incorrect password or username")
    return render_template('userLogin.html' , message=None)

@app.route('/vendorSignUp' , methods=['GET', 'POST'])
def vendor_signup():
    if request.method == 'GET':
        return render_template('vendorSignUp.html' , message=None)
    if request.method == 'POST':
        userName = request.form.get('userName')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if not userName or not password or not confirm:
            return render_template('vendorSignUp.html', message="Please fill in all fields.")
        if password != confirm:
            return render_template('vendorSignUp.html', message="Passwords do not match.")
        if vendors.find_one({"userName": userName}):
            return render_template('vendorSignUp.html', message="Vendor '{userName}' already exists!")
        vendors.insert_one({"userName": userName, "password": password})
    return render_template('vendorSignUp.html' , message=None)

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
