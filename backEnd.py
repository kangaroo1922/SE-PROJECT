from flask import Flask, request, render_template
from flask import Flask, request, render_template, session, redirect, url_for, send_file
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from flask import Flask, request, render_template, send_file
import io
from bson.errors import InvalidId
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with a strong secret key!
client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.3.5")
db = client["wholeDB"]
vendors = db["vendor_credentials"]
users = db["user_credentials"]
vendorBio = db["vendor_biodata"]
userOrder = db["order_details"]
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
        vendor_id = request.form.get('vendor_id')
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
            "chosenVendorId": vendor_id,
            "userName": userName,
            "user_id": user_id,
            "contact": contact,
            "description": description,
            "date": date,
            "address": address,
            "cardNumber": cardNumber,
            "expiry": expiry,
            "cvv": cvv
        })
        
        # Retrieve vendor for the success page (Safe Lookup)
        try:
            current_vendor = vendorBio.find_one({"_id": ObjectId(vendor_id)})
        except InvalidId:
            # Fallback: Try searching by the custom string 'vendor_id'
            current_vendor = vendorBio.find_one({"vendor_id": vendor_id})

        return render_template('bookingpanel.html', message="Booking submitted successfully!", vendor=current_vendor)

    # --- PART 2: LOADING THE PAGE (GET) ---
    else:
        vendor_id_from_url = request.args.get('vendor_id')
        
        if not vendor_id_from_url:
            return "Error: No vendor ID provided in URL. Please go back and select a vendor."

        # --- THE FIX: Robust ID Lookup ---
        try:
            # 1. First try to find by the MongoDB ObjectId
            target_vendor = vendorBio.find_one({"_id": ObjectId(vendor_id_from_url)})
        except InvalidId:
            # 2. If that crashes, it's likely a custom string ID or dirty data.
            #    Try searching by the "vendor_id" field instead.
            target_vendor = vendorBio.find_one({"vendor_id": vendor_id_from_url})
        
        # 3. If still not found, the ID is garbage
        if not target_vendor:
            return f"Error: Vendor with ID '{vendor_id_from_url}' not found in database.", 404

        return render_template('bookingpanel.html', vendor=target_vendor)    
# ... existing code ...
@app.route('/vendorDashboard')
def vendorDashboard():
    # 1. Security Check
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))

    current_vendor_id = session['vendor_id']

    # 2. Query the 'order_details' collection
    # Fetch orders for this vendor, sorted by newest date first
    my_orders = list(db['order_details'].find(
        {"chosenVendorId": current_vendor_id}
    ).sort("date", -1))

    # 3. Render the dashboard
    return render_template('vendorDashboard.html', orders=my_orders)



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
            {"vendor_id": vendor_id},  # each vendor has one bio
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

if __name__ == '__main__':
    app.run(debug=True)
