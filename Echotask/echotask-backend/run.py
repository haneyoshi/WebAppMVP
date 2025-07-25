# ***** a Luancher

from app import create_app
# in Python, when a folder(app) has a file called __init__.py inside it, Python treats that folder as a module.

app = create_app()

if __name__ == "__main__":
    # If this file (run.py) is the main file that was executed (not imported), then run the following code.
    # If you just imported run.py somewhere else, the code inside that if block would not run.
    app.run(debug=True)
    # when "app" runs, tells Flask to call(automatically) "hello()" and shows whatever it returns
 

 # activate virtual environment while working on the project by enter this in PowerShell:
 #  -> .venv\Scripts\Activate