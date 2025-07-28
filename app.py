# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
import pymongo
from pymongo import MongoClient
import numpy as np
import pandas as pd
from dotenv import load_dotenv, find_dotenv

#Database
load_dotenv(find_dotenv())
uri = os.environ.get("URI")
client = MongoClient(uri)
db_Option = client.Stocks

app = Flask(__name__)
app.secret_key = 'LAGUZ'

@app.route('/')
def index():
    """
    Route to render the index.html template.

    This function is responsible for handling the '/' route. It returns the rendered
    'index.html' template.

    Returns:
        The rendered 'index.html' template.
    """
    # Render the 'index.html' template and return it
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)