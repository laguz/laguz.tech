# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, flash, Markup, jsonify, redirect, url_for
import pymongo
from pymongo import MongoClient
import numpy as np
import pandas as pd
from dotenv import load_dotenv, find_dotenv

#This a test for the local import
#from model import TDSession

#Database
load_dotenv(find_dotenv())
uri = os.environ.get("URI")
client = MongoClient(uri)
db_Option = client.Options

app = Flask(__name__)
app.secret_key = 'LAGUZ'

@app.route('/')
def index():
    return "Luis Guzman"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
