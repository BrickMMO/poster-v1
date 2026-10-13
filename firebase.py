import firebase_admin
from firebase_admin import credentials, db
import sys, tty, termios

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://brickmmoposter-default-rtdb.firebaseio.com/"
})

ref = db.reference("poster-1")
data = ref.get() or {}
fans = data.get("fans", False)
lights = data.get("lights", False)


def show():
    print("\033[2J\033[H", end="")
    print("BRICKMMO POSTER\n")
    print(f"Fans:   {'ON' if fans else 'OFF'}")
    print(f"Lights: {'ON' if lights else 'OFF'}\n")
    print("F = Fans   L = Lights")


def changed(e):
    global fans, lights
    if e.path == "/":
        fans = e.data.get("fans", False)
        lights = e.data.get("lights", False)
    elif e.path == "/fans":
        fans = e.data
    elif e.path == "/lights":
        lights = e.data
    show()


show()
ref.listen(changed)

old = termios.tcgetattr(sys.stdin)
try:
    tty.setcbreak(sys.stdin.fileno())

    while True:
        key = sys.stdin.read(1).lower()

        if key in "fl":
            name = "fans" if key == "f" else "lights"
            value = not (fans if key == "f" else lights)
            ref.child(name).set(value)

finally:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)

