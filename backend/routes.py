from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=['GET'])
def health():
    return jsonify({"status": "OK"})

@app.route("/count",methods=['GET'])
def count():
    count_number=20
    return jsonify({"count":count_number})

@app.route("/song", methods=['GET'])
def songs():
    try:
        songs_list = list(db.songs.find({}))
        print(f"Fetched Songs: {songs_list}")  # Debugging output
        formatted_songs = [{"id": song["id"], "title": song["title"], "lyrics": song["lyrics"]} for song in songs_list]
        return jsonify({"songs": formatted_songs}), 200
    except Exception as e:
        print(f"Error: {e}")  # Print the error to understand it
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/song/<int:id>", methods=['GET'])
def get_song_by_id(id):
    # Fetch the song by its id
    song = db.songs.find_one({"id": id})
    
    if song:
        # If the song is found, return it as JSON
        formatted_song = {
            "id": song["id"],
            "title": song["title"],
            "lyrics": song["lyrics"]
        }
        return jsonify(formatted_song), 200
    else:
        # If the song is not found, return a message with a 404 error
        return jsonify({"message": "song with id not found"}), 404

@app.route("/song", methods=["POST"])
def create_song():
    # Extract data from the request body
    song_data = request.get_json()

    # Check if the song with the given id already exists
    existing_song = db.songs.find_one({"id": song_data["id"]})
    
    if existing_song:
        # If the song already exists, return a 302 response with a message
        return jsonify({"Message": f"song with id {song_data['id']} already present"}), 302
    
    # If the song doesn't exist, insert the new song into the database
    new_song = {
        "id": song_data["id"],
        "lyrics": song_data["lyrics"],
        "title": song_data["title"]
    }

    db.songs.insert_one(new_song)

    # Return the inserted song details with a 201 CREATED status
    return jsonify({"inserted id": str(new_song["id"])}), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        # Extract updated data from the request body
        updated_data = request.get_json()
        if not updated_data:
            return jsonify({"message": "No data provided"}), 400

        # Find the song by id
        song = db.songs.find_one({"id": id})
        
        if not song:
            # If the song is not found, return a 404 response
            return jsonify({"message": "song not found"}), 404

        # Prepare the updated song data
        update_values = {"$set": updated_data}

        # Update the song in the database
        result = db.songs.update_one({"id": id}, update_values)

        if result.matched_count > 0:
            if result.modified_count > 0:
                # If the song was updated, return the updated song with a 200 OK status
                updated_song = db.songs.find_one({"id": id})
                return jsonify(updated_song), 200
            else:
                # If no fields were modified, return a message indicating no changes were made
                return jsonify({"message": "song found, but nothing updated"}), 200
        else:
            return jsonify({"message": "song not found"}), 404

    except Exception as e:
        # Catch any unexpected exceptions and return a 500 error
        return jsonify({"message": str(e)}), 500



@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        # Attempt to delete the song by id
        result = mongo.db.songs.delete_one({"id": id})

        if result.deleted_count == 0:
            # If no document was deleted, return a 404 with a message
            return jsonify({"message": "song not found"}), 404
        
        # If song is successfully deleted, return 204 No Content
        return '', 204

    except Exception as e:
        # Catch any unexpected exceptions and return a 500 error
        return jsonify({"message": str(e)}), 500