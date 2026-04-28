from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Reel(db.Model):
    __tablename__ = 'reels'
    reel_id = db.Column(db.String, primary_key=True)
    creator_id = db.Column(db.String)
    creator_followers = db.Column(db.Integer)
    posting_time = db.Column(db.Integer)
    reel_length_sec = db.Column(db.Integer)
    hook_strength_score = db.Column(db.Float)
    caption_length = db.Column(db.Integer)
    hashtags_count = db.Column(db.Integer)
    trending_audio = db.Column(db.Boolean)
    audio_popularity_score = db.Column(db.Float)
    video_quality_score = db.Column(db.Float)
    editing_quality_score = db.Column(db.Float)
    avg_watch_time_sec = db.Column(db.Float)
    retention_rate = db.Column(db.Float)
    completion_rate = db.Column(db.Float)
    rewatch_rate = db.Column(db.Float)
    likes = db.Column(db.Integer)
    comments = db.Column(db.Integer)
    shares = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    engagement_rate = db.Column(db.Float)
    impressions = db.Column(db.Integer)
    reach = db.Column(db.Integer)
    non_follower_reach_ratio = db.Column(db.Float)
    explore_page_boost = db.Column(db.Boolean)
    virality_score = db.Column(db.Float)

@app.route("/", methods=["GET"])
def index():
    return render_template("base.html")

if __name__ == "__main__":
    app.run(debug=True)