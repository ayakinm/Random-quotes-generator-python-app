git import random

from flask import Flask, render_template

app = Flask(__name__)

QUOTES = [
    {
        "text": "The secret of getting ahead is getting started.",
        "author": "Mark Twain",
    },
    {
        "text": "It always seems impossible until it's done.",
        "author": "Nelson Mandela",
    },
    {
        "text": "Great things are done by a series of small things brought together.",
        "author": "Vincent van Gogh",
    },
    {
        "text": "You miss 100% of the shots you don't take.",
        "author": "Wayne Gretzky",
    },
    {
        "text": "Act as if what you do makes a difference. It does.",
        "author": "William James",
    },
]


@app.get("/")
def home():
    return render_template("index.html", quote=random.choice(QUOTES))


if __name__ == "__main__":
    app.run(debug=True)