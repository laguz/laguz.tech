# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, Markup, jsonify, redirect, url_for
import pymongo
from pymongo import MongoClient
import numpy as np
import pandas as pd

#Database
#client = MongoClient(uri)

app = Flask(__name__)
app.secret_key = 'LAGUZ'

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)
