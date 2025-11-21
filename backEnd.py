from flask import Flask, request, render_template
from flask import Flask, request, render_template, session, redirect, url_for, send_file
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from flask import Flask, request, render_template, send_file
import io
from bson.errors import InvalidId
import bcrypt
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with a strong secret key!
client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.3.5")
db = client["wholeDB"]
vendors = db["vendor_credentials"]
users = db["user_credentials"]
vendorBio = db["vendor_biodata"]
userOrder = db["order_details"]
admin_collection = db["admin_collection"]
fs = gridfs.GridFS(db)
@app.route("/profile/<vendor_id>")
def profile(vendor_id):
    vendor = vendorBio.find_one({"vendor_id": vendor_id})
    if not vendor:
        return "Vendor not found", 404

    image_ids = vendor.get("images", [])
    image_ids = [str(i) for i in image_ids]
    return render_template("vendorSide.html", vendor=vendor, image_ids=image_ids)


@app.route("/image/<image_id>")
def get_image(image_id):
    """Return an image from GridFS."""
    try:
        image_file = fs.get(ObjectId(image_id))
        return send_file(io.BytesIO(image_file.read()), mimetype="image/jpeg")
    except:
        return "Image not found", 404
@app.route('/vendorSide')
def vendorSide():
    return render_template('vendorSide.html')
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')
@app.route('/faq')
def faq():
    return render_template('FAQ.html')

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
            session["client_name"] = user_doc["userName"]
            session["client_id"] = str(user_doc["_id"])
            return redirect(url_for('clientside'))
        else:
            return render_template('userLogin.html', message="Login failed, incorrect password or username")
    return render_template('userLogin.html' , message=None)


@app.route('/clientside' , methods=['GET' , 'POST'])
def clientside():
    return render_template('clientside.html',message=None)



@app.route('/getContent/<vendorId>')
def getContent(vendorId):
    vendor = vendorBio.find_one({"_id": ObjectId(vendorId)})
    imageIds = vendor.get("images" , [])
    imageIds = [str(i) for i in imageIds]
    return render_template('clientside.html' , vendor = vendor, imageIds=imageIds)


@app.route('/search', methods=['GET' , 'POST'])
def search():
    searchString = request.form.get("query")
    name = vendorBio.find_one({"full_name":searchString})
    if not name:
        return redirect(url_for('clientside'))
    return redirect(url_for('getContent',vendorId=str(name["_id"])))
@app.route('/allVendors', methods=['GET' , 'POST'])
def allVendors():
    allVendors = list(vendorBio.find())

    # For each vendor, also load its image IDs
    for v in allVendors:
        v["imageIds"] = v.get("images", [])


    return render_template("clientside.html", vendors=allVendors)


@app.route('/bookingpanel', methods=['GET', 'POST'])
def booking_details():
    # --- PART 1: SAVING THE DATA (POST) ---
    if request.method == 'POST':
        bill = request.form.get('bill')
        vendor_id = request.form.get('vendor_id')
        chosen_vendor = vendorBio.find_one({"vendor_id":vendor_id})
        fullName = request.form.get('name')
        contact = request.form.get('contact')
        description = request.form.get('description')
        date = request.form.get('date')
        address = request.form.get('address')
        cardNumber = request.form.get('cardNumber')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')
        
        # Helper to get session data safely
        userName = session.get("client_name")
        user_id = session.get("client_id")

        if not userName:
            return redirect(url_for('userLogin'))

        # Insert the order
        db['order_details'].insert_one({
            "fullName": fullName,
            "chosenVendorId": str(chosen_vendor["vendor_id"]),
            "userName": userName,
            "user_id": user_id,
            "contact": contact,
            "description": description,
            "date": date,
            "address": address,
            "cardNumber": cardNumber,
            "expiry": expiry,
            "cvv": cvv,
            "bill":bill,
            "state":''
        })
        
        # Retrieve vendor for the success page (Safe Lookup)
        try:
            current_vendor = vendorBio.find_one({"vendor_id": vendor_id})
        except InvalidId:
            # Fallback: Try searching by the custom string 'vendor_id'
            current_vendor = vendorBio.find_one({"vendor_id": vendor_id})

        return render_template('bookingpanel.html', message="Booking submitted successfully! Your total bill is", vendor=current_vendor, bill = bill)

    # --- PART 2: LOADING THE PAGE (GET) ---
    else:
        vendor_id = request.args.get('vendor_id')
        bill = request.args.get('bill')
        current_vendor = vendorBio.find_one({"vendor_id": vendor_id})

    return render_template('bookingpanel.html', vendor=current_vendor, bill=bill)
@app.route('/updateOrders', methods=['POST'])
def updateOrders():
    orders = list(request.form.lists())

    # request.form contains flat data → state_<id>: value

    for key, value in request.form.items():
        if key.startswith("state_"):
            order_id = key.replace("state_", "")
            state = value  # 'accept' or 'reject'

            db['order_details'].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"state": state}}
            )

    return redirect(url_for('vendorDashboard'))


# ... existing code ...
@app.route('/vendorDashboard')
def vendorDashboard():
    # 1. Security Check
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))

    # This is the vendor_credentials._id stored as a string
    current_vendor_id = session['vendor_id']
    # 3. Fetch orders where chosenVendorId matches vendor_id
    my_orders = list(
        db['order_details']
        .find({"chosenVendorId": current_vendor_id,
               "state": {"$exists": False}
               })
        
        .sort("date", -1)
    )

    # 4. Render dashboard
    return render_template(
        'vendorDashboard.html',
        orders=my_orders,
        vendor=current_vendor_id
    )


#route to the user order dashboard
# route in your backend
@app.route('/userDashboard', methods=['GET'])
def userDashboard():
    userId = session.get('client_id')
    if not userId:
        return redirect(url_for('userLogin'))

    # Get all orders for this user
    my_orders = list(
        db['order_details']
        .find({"user_id": userId})
        .sort("date", -1)
    )

    # Collect vendor IDs from orders
    vendor_ids = [o['chosenVendorId'] for o in my_orders if o.get('chosenVendorId')]

    # Convert IDs to proper type depending on your DB
    # Example: if vendor_id in DB is ObjectId, convert them
    # vendor_ids = [ObjectId(v) for v in vendor_ids]

    # Fetch all vendor bios matching these IDs
    vendors_list = list(db['vendor_biodata'].find({"vendor_id": {"$in": vendor_ids}}))

    # Build dict with string keys (for easy lookup in template)
    vendors_dict = {str(v['vendor_id']): v for v in vendors_list}

    return render_template('userDashboard.html', orders=my_orders, vendors_dict=vendors_dict)


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
                session["vendor_user"] = vendor_doc["userName"]
                session["vendor_id"] = str(vendor_doc["_id"])
                return redirect(url_for("vendorPanelUpdateBio"))

            else:
                return render_template('vendorLogin.html', message = "Login failed credentials do not match!")
    return render_template('vendorLogin.html', message=None)
@app.route('/vendorPanelUpdateBio', methods=['GET', 'POST'])
def vendorPanelUpdateBio():
    if request.method == 'POST':
        # Ensure vendor is logged in
        if "vendor_user" not in session:
            return redirect(url_for("vendor_login"))

        userName = session["vendor_user"]
        vendor_id = session["vendor_id"]

        name = request.form.get('name')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        about = request.form.get('about')
        package1 = request.form.get('package1')
        package2 = request.form.get('package2')
        package3 = request.form.get('package3')
        files = request.files.getlist('images')

        image_ids = []
        for file in files:
            if file and file.filename != '':
                image_id = fs.put(file, filename=file.filename)
                image_ids.append(str(image_id))

        # Replace (not append) vendor bio + images
        vendorBio.update_one(
            {"vendor_id": str(vendor_id),},  # each vendor has one bio
            {
                "$set": {
                    "vendor_id": vendor_id,
                    "userName": userName,
                    "full_name": name,
                    "date_of_birth": dob,
                    "phone_number": phone,
                    "about": about,
                    "package1": package1,
                    "package2": package2,
                    "package3": package3,
                    "images": image_ids
                }
            },
            upsert=True
        )

        return render_template(
            'vendorPanelUpdateBio.html',
            message="Profile updated successfully!"
        )

    return render_template('vendorPanelUpdateBio.html', message=None)
def create_admin():
    existing = admin_collection.find_one({"username": "admin"})
    if not existing:
        hashed_pass = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        admin_collection.insert_one({
            "username": "admin",
            "password": hashed_pass
        })
        print("Default admin created.")
    else:
        print("Admin already exists.")
@app.route('/adminLogin', methods=['GET', 'POST'])
def adminLogin():
    create_admin()
    if request.method == 'POST':
        username = request.form.get('userName')
        password = request.form.get('password')

        admin = admin_collection.find_one({"username": username})

        if admin:
            # Check password hash
            if bcrypt.checkpw(password.encode('utf-8'), admin["password"]):
                session["admin"] = username
                return redirect(url_for('adminPanel'))
            else:
                return render_template('adminLogin.html',
                                       message="Incorrect password")
        else:
            return render_template('adminLogin.html',
                                   message="Admin user not found")

    return render_template('adminLogin.html')
@app.route('/adminPanel', methods=['GET' , 'POST'])
def adminPanel():
    if request.method == 'GET':
        return render_template('adminPanel.html')
if __name__ == '__main__':
    app.run(debug=True)
