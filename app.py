from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    flash,
    send_file,
    jsonify
)
import pymongo
import io
import base64
import os
from dotenv import load_dotenv
from bson import ObjectId  # Correct import for ObjectId

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Use the SECRET_KEY from the .env file
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"jpg", "jpeg", "png", "gif"}
app.secret_key = os.getenv('SECRET_KEY')
load_dotenv()

# MongoDB connection using the environment variable
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client.get_database("weddingCluster")
photos_collection = db.get_collection("wedding_photos")

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )

def insert_photo(filename, photo_data):
    """Insert the uploaded photo into MongoDB."""
    photo_document = {
        "filename": filename,
        "photo": photo_data
    }
    photos_collection.insert_one(photo_document)

def get_photo(photo_id):
    """Retrieve a photo from MongoDB."""
    photo = photos_collection.find_one({"_id": photo_id})
    if photo:
        return photo["filename"], photo["photo"]
    return None, None

@app.route("/")
def index():
    """Redirect to the upload form page."""
    return redirect(url_for("upload_form"))

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload."""
    if "photo" not in request.files:
        flash("No file part", "error")
        return redirect(url_for("upload_form"))

    file = request.files["photo"]

    if file and allowed_file(file.filename):
        filename = file.filename
        photo_data = file.read()  # Read the file as binary data
        insert_photo(filename, photo_data)  # Insert the photo into MongoDB
        flash("File uploaded successfully", "success")
        return redirect(url_for("gallery"))
    else:
        flash("File type not allowed", "error")
        return redirect(url_for("upload_form"))

@app.route("/upload-form")
def upload_form():
    """Render the upload form page."""
    return render_template("index.html")

@app.route("/gallery")
def gallery():
    """Render the gallery page with uploaded photos."""
    photos = photos_collection.find()

    # Convert the binary data to a format that can be displayed in HTML
    photo_list = []
    for photo in photos:
        photo_id = str(photo["_id"])
        filename = photo["filename"]
        photo_data = base64.b64encode(photo["photo"]).decode("utf-8")

        photo_list.append({"id": photo_id, "filename": filename, "photo_data": photo_data})

    return render_template("gallery.html", photos=photo_list)

@app.route("/photo/<photo_id>")
def show_photo(photo_id):
    """Serve a photo as a base64 encoded image."""
    photo = photos_collection.find_one({"_id":ObjectId(photo_id)})
    print("im here",photo_id)

    if photo:
        # Convert the binary data to a base64 string
        photo_data = base64.b64encode(photo["photo"]).decode("utf-8")
        
        # Return the photo data in a JSON response
        return jsonify({"photo_data": photo_data})
    else:
        return jsonify({"error": "Photo not found"}), 404
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)
