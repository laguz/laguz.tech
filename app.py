# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, Markup, jsonify

app = Flask(__name__)
app.secret_key = 'LAGUZ'

@app.route('/')
def index():
    return 'Luis Alberto Guzman Zorrilla.'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)
