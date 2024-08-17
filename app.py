from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    flash,
    send_file,
)
from dotenv import load_dotenv
import MySQLdb
import os
import io
import base64  # Optional if you want to encode/decode BLOBs using base64


load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for session-based flash messages
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"jpg", "jpeg", "png", "gif"}

connection = MySQLdb.connect(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    passwd=os.getenv("DATABASE_PASSWORD"),
    db=os.getenv("DATABASE"),
    autocommit=True,
    ssl_mode="VERIFY_IDENTITY",
)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )

def insert_photo(filename, photo_data):
    """Insert the uploaded photo into the database."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO wedding_photos (filename, photo) VALUES (%s, %s)",
            (filename, photo_data)
        )
        connection.commit()
    except MySQLdb.Error as e:
        print("MySQL Error:", e)
    finally:
        cursor.close()

def get_photo(photo_id):
    """Retrieve photo from the database."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT filename, photo FROM wedding_photos WHERE id = %s", (photo_id,))
        result = cursor.fetchone()
        if result:
            filename, photo_data = result
            return filename, photo_data
    except MySQLdb.Error as e:
        print("MySQL Error:", e)
    finally:
        cursor.close()
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
        insert_photo(filename, photo_data)  # Insert the photo into the database
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
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, filename, photo FROM wedding_photos")
        photos = cursor.fetchall()

        # Convert the BLOB data to a format that can be displayed in HTML
        photo_list = []
        for photo in photos:
            photo_id = photo[0]
            filename = photo[1]
            photo_data = base64.b64encode(photo[2]).decode("utf-8")

            photo_list.append({"id": photo_id, "filename": filename, "photo_data": photo_data})

    except MySQLdb.Error as e:
        print("MySQL Error:", e)
        photo_list = []
    finally:
        cursor.close()

    return render_template("gallery.html", photos=photo_list)


@app.route("/photo/<int:photo_id>")
def show_photo(photo_id):
    """Serve the photo from the database."""
    filename, photo_data = get_photo(photo_id)
    if photo_data:
        mimetype = 'image/jpeg'  # Default MIME type; adjust as needed
        if filename.lower().endswith(".png"):
            mimetype = 'image/png'
        elif filename.lower().endswith(".gif"):
            mimetype = 'image/gif'
        return send_file(
            io.BytesIO(photo_data),
            attachment_filename=filename,
            mimetype=mimetype
        )
    else:
        return "Photo not found", 404

if __name__ == "__main__":

    # Run the Flask app
    app.run(debug=True)
