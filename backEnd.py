from flask import Flask, request, render_template,jsonify, send_file, abort, Response
from flask import Flask, request, render_template, session, redirect, url_for, send_file
from pymongo import MongoClient
import gridfs
from bson import ObjectId
from flask import Flask, request, render_template, send_file
import io
from bson.errors import InvalidId
import bcrypt
import csv, io, os, datetime
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with a strong secret key!
from urllib.parse import quote_plus

password = quote_plus("zktQ@xud36XNaPZ")
client = MongoClient(f"mongodb+srv://zuhanu:{password}@cluster0.9ynwvoj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["wholeDB"]
vendors = db["vendor_credentials"]
users = db["user_credentials"]
vendorBio = db["vendor_biodata"]
userOrder = db["order_details"]
admin_collection = db["admin_collection"]
fraud_logs_col = db["fraudLogs"]
fs = gridfs.GridFS(db)
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
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
    for key, value in request.form.items():
        if key.startswith("state_"):
            order_id = key.replace("state_", "")
            state = value  # accept OR reject

            # Update order state
            db['order_details'].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"state": state}}
            )

            # If accepted → update vendor revenue
            if state == "accept":

                # Extract bill value from form
                bill_key = f"bill_{order_id}"
                bill_str = request.form.get(bill_key, "0")
                try:
                    bill_amount = float(bill_str)
                except ValueError:
                    bill_amount = 0
                print("Bill received:", bill_amount)

                # Extract vendor_id from form
                vendor_key = f"vendor_{order_id}"
                vendor_id = request.form.get(vendor_key)
                print(vendor_id)
                print("Vendor ID received:", vendor_id)
                vendor_doc = db['vendor_biodata'].find_one({"vendor_id": vendor_id})
                currentRevenue = vendor_doc.get("revenue", 0)
                totalRevenue = currentRevenue + bill_amount
                if vendor_id and bill_amount > 0:
                    # Increment revenue in vendorBio
                    result = db['vendor_biodata'].update_one(
                        {"vendor_id": vendor_id},
                        {"$inc": {"revenue": totalRevenue}}
                    )
                    print("Revenue update matched:", result.matched_count, "modified:", result.modified_count)

    return redirect(url_for('vendorDashboard'))




# ... existing code ...
@app.route('/vendorDashboard')
def vendorDashboard():

    # This is the vendor_credentials._id stored as a string
    current_vendor_id = session['vendor_id']
    print(current_vendor_id)
    # 3. Fetch orders where chosenVendorId matches vendor_id
    my_orders = list(
    db['order_details'].find({
        "chosenVendorId": current_vendor_id,
        "$or": [
            {"state": {"$exists": False}},
            {"state": ""},
            {"state": None}
        ]
    }).sort("date", -1)
)

    print(list(db['order_details'].find({"chosenVendorId": current_vendor_id}, {"state": 1, "_id": 1})))

    return render_template('vendorDashboard.html' ,orders = my_orders, vendor_id = current_vendor_id)


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
                    "images": image_ids,
                    "revenue": 0
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
# Utility to convert ObjectId to string in documents
def oid_to_str(doc):
    if not doc: return doc
    if isinstance(doc, list):
        return [oid_to_str(x) for x in doc]
    if isinstance(doc, dict):
        new_doc = {}
        for k, v in doc.items():
            if k == "_id":
                new_doc["id"] = str(v)
            elif isinstance(v, ObjectId):
                new_doc[k] = str(v)
            else:
                new_doc[k] = oid_to_str(v)
        return new_doc
    return doc

# ------------------ API: USERS ------------------
@app.route("/api/users", methods=["GET"])
def get_users_api():
    try:
        user_list = list(users.find({}))
        cleaned = []
        for u in user_list:
            cleaned.append({
                "id": str(u["_id"]),
                "name": u.get("userName", "Unknown"), # Assuming username is the display name
                "email": u.get("userName", ""),       # Using username as email/contact identifier
                "balance": float(u.get("balance", 0.0)),
                "blocked": u.get("blocked", False)
            })
        return jsonify(cleaned)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/users/<user_id>", methods=["PATCH", "DELETE"])
def manage_user_api(user_id):
    try:
        oid = ObjectId(user_id)
    except:
        return jsonify({"error": "Invalid ID format"}), 400

    if request.method == "DELETE":
        users.delete_one({"_id": oid})
        return jsonify({"success": True})

    if request.method == "PATCH":
        data = request.json
        update_fields = {}
        
        # Map frontend fields to DB fields
        if "email" in data: update_fields["userName"] = data["email"]
        if "balance" in data: update_fields["balance"] = float(data["balance"])
        if "blocked" in data: update_fields["blocked"] = bool(data["blocked"])
        
        if update_fields:
            users.update_one({"_id": oid}, {"$set": update_fields})
        return jsonify({"success": True})

# ------------------ API: VENDORS ------------------
@app.route("/api/vendors", methods=["GET"])
def get_vendors_api():
    try:
        # Vendor data is split: Credentials (auth/block status) + Biodata (profile/revenue)
        creds = list(vendors.find({}))
        merged_list = []
        
        for v in creds:
            vid = str(v["_id"])
            bio = vendorBio.find_one({"vendor_id": vid}) or {}
            
            merged_list.append({
                "id": vid,
                "name": bio.get("full_name") or v.get("userName", "Unknown"),
                "rating": float(bio.get("rating", 0.0)),
                "revenue": float(bio.get("revenue", 0.0)),
                "reviews": int(bio.get("reviews", 0)),
                "blocked": v.get("blocked", False)
            })
        return jsonify(merged_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/vendors/<vendor_id>", methods=["PATCH", "DELETE"])
def manage_vendor_api(vendor_id):
    try:
        oid = ObjectId(vendor_id)
    except:
        return jsonify({"error": "Invalid ID format"}), 400

    if request.method == "DELETE":
        vendors.delete_one({"_id": oid})
        vendorBio.delete_one({"vendor_id": vendor_id})
        return jsonify({"success": True})

    if request.method == "PATCH":
        data = request.json
        
        # 1. Update Credentials Collection (Blocked Status / Username)
        cred_updates = {}
        if "blocked" in data: cred_updates["blocked"] = data["blocked"]
        if cred_updates:
            vendors.update_one({"_id": oid}, {"$set": cred_updates})
        
        # 2. Update Biodata Collection (Name, Revenue, Rating)
        bio_updates = {}
        if "name" in data: bio_updates["full_name"] = data["name"]
        if "rating" in data: bio_updates["rating"] = float(data["rating"])
        if "revenue" in data: bio_updates["revenue"] = float(data["revenue"])
        
        if bio_updates:
            vendorBio.update_one({"vendor_id": vendor_id}, {"$set": bio_updates})
            
        return jsonify({"success": True})

# ------------------ API: FRAUD HANDLER ------------------
@app.route("/api/fraud/handle", methods=["POST"])
def fraud_handler():
    try:
        # Logic: Find unblocked vendor with highest revenue
        all_bios = list(vendorBio.find().sort("revenue", -1))
        target_vendor = None
        
        for bio in all_bios:
            if bio.get("revenue", 0) > 1000000:
                # Check credential status
                cred = vendors.find_one({"_id": ObjectId(bio["vendor_id"])})
                if cred and not cred.get("blocked", False):
                    target_vendor = bio
                    break
        
        if not target_vendor:
            return jsonify({"success": False, "error": "No high-revenue active vendors found."}), 404

        vid = target_vendor["vendor_id"]
        extracted_amount = float(target_vendor.get("revenue", 0))

        # 1. Block Vendor
        vendors.update_one({"_id": ObjectId(vid)}, {"$set": {"blocked": True}})
        
        # 2. Seize Revenue
        vendorBio.update_one({"vendor_id": vid}, {"$set": {"revenue": 0}})

        # 3. Refund Users (Top 3 users, simulated distribution)
        recipients = list(users.find().limit(3))
        refund_logs = []
        if recipients:
            amount_per_user = (extracted_amount * 0.8) / len(recipients)
            for u in recipients:
                users.update_one({"_id": u["_id"]}, {"$inc": {"balance": amount_per_user}})
                refund_logs.append({"id": str(u["_id"]), "amount": amount_per_user})
        
        # 4. Log Action
        log_entry = {
            "ts": datetime.datetime.now(),
            "vendor_name": target_vendor.get("full_name", "Unknown"),
            "vendor_id": vid,
            "extracted": extracted_amount,
            "refunded": refund_logs
        }
        fraud_logs_col.insert_one(log_entry)

        return jsonify({
            "success": True, 
            "vendor": target_vendor.get("full_name"), 
            "extracted": extracted_amount,
            "refunded_count": len(refund_logs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ------------------ API: EXPORT CSV ------------------
@app.route("/api/export/vendors.csv")
def export_csv_api():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Vendor ID", "Name", "Revenue", "Rating", "Blocked Status"])
    
    creds = vendors.find()
    for v in creds:
        vid = str(v["_id"])
        bio = vendorBio.find_one({"vendor_id": vid}) or {}
        writer.writerow([
            vid,
            bio.get("full_name", v.get("userName")),
            bio.get("revenue", 0),
            bio.get("rating", 0),
            "Blocked" if v.get("blocked") else "Active"
        ])
        
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", 
                    headers={"Content-Disposition": "attachment;filename=pixora_vendors_report.csv"})

if __name__ == '__main__':
    app.run(debug=True)
