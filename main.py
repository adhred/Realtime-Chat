from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "reddy"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(Length):
   while True:
      code= ""
      for _ in range(Length):
         code += random.choice(ascii_uppercase)

      if code not in rooms:
         break
      
   return code

   
#MAIN

@app.route("/", methods =["POST", "GET"])
def main():
  
  session.clear()

  if request.method == "POST":
    name = request.form.get("name")
    code = request.form.get("code")
    join = request.form.get("join", False)
    create = request.form.get("create", False)
    public = request.form.get("public", False)

    if not name:
       return render_template("main.html", error="Please enter a name", code=code, name=name)

    if join != False and not code and not public:
       return render_template("main.html", error="Please enter the room code", code=code, name=name)

    room = code
    
    if public:
       room = "public"
    elif join != False:
       if not code:
          return render_template("main.html", error="Enter room code", code=code, name=name)
    elif create != False:
       room = generate_unique_code(4)
    else:
       return render_template("main.html", error="Invalid action", code=code, name=name)

    if room not in rooms:
       if room != "public" and join != False:
          return render_template("main.html", error="Room does not exist", code=code, name=name)
       rooms[room] = {"members": 0, "messages": []}
    
    session["room"] = room
    session["name"] = name

    return redirect(url_for("room"))
 
  return render_template("main.html")

#ROOM

@app.route("/room")
def room():
   
   room = session.get("room")
   if room is None or session.get("name") is None or room not in rooms:
      return redirect(url_for("main"))
   return render_template("room.html", code=room, messages=rooms[room]["messages"])

#MESSAGES

@socketio.on("message")
def message(data):
   room = session.get("room")

   if room not in rooms:
      return
   
   content = {
      "name": session.get("name"),
      "message": data["data"]
   }

   send(content, to=room)
   rooms[room]["messages"].append(content)
   print(f"{session.get('name')} said: {data['data']}")

#CONNECT

@socketio.on("connect")
def connect(auth):
   room = session.get("room")
   name = session.get("name")

   if not room or not name:
      return
   
   if room not in rooms:
      leave_room(room)
      return
   
   join_room(room)
   send({"name": name, "message": "has entered the room"}, to=room)
   rooms[room]["members"] += 1
   print(f"{name} joined room {room}")

#DISCONNECT

@socketio.on("disconnect")
def disconnect():
   room = session.get("room")
   name = session.get("name")
   leave_room(room)


   if room in rooms:
      rooms[room]["members"] -= 1
      if rooms[room]["members"] <= 0 and room != "public":
         del rooms[room]

   send({"name": name, "message": "has left the room"}, to=room)
   print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)