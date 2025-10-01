from flask import Flask
""" create an object 'app' from the Flask module.
__name__ set to __main__ if the script is running directly
from the main file
"""
app = Flask(__name__)
# set the routing to the main page
# 'route' decorator is used to access the root URL
@app.route('/')
def index():
    return "Hello Python Flask"

# set the 'app' to run if you execute the file directly(not when it is imported)
if __name__ == '__main__':
    app.run(debug=True)