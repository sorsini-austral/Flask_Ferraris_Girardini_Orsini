from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import os

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

_df_cache = None

def get_df():
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_sql(Reel.query.statement, db.engine)
    return _df_cache

def save_plot(filename):
    os.makedirs('static/plots', exist_ok=True)
    plt.tight_layout()
    plt.savefig(f'static/plots/{filename}', dpi=100)
    plt.close()

@app.route("/", methods=["GET"])
def index():
    df = get_df()
    # Stat cards para mostrar en el HTML
    total_reels = len(df)
    virals = df[df['virality_score'] > 0.7]  # ajustá el umbral según el dataset
    viral_percentage = round(len(virals) / total_reels * 100, 1)
    avg_engagement = round(df['engagement_rate'].mean() * 100, 2)
    best_time = int(df.groupby('posting_time')['virality_score'].mean().idxmax())

    # Gráfico: viralidad promedio por horario
    fig, ax = plt.subplots(figsize=(10, 4))
    hours = df.groupby('posting_time')['virality_score'].mean()
    ax.plot(hours.index, hours.values, marker='o', color='#E1306C')
    ax.set_title('Viralidad promedio según horario de publicación')
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Virality score promedio')
    save_plot('virality_by_hour.png')

    return render_template("index.html",
        total_reels=total_reels,
        viral_percentage=viral_percentage,
        avg_engagement=avg_engagement,
        best_time=best_time,
        plot='virality_by_hour.png'
    )

@app.route("/game", methods=["GET"])
def game():
    return render_template("game.html")

@app.route("/audio", methods=["GET"])
def audio():
    df = get_df()
    fig, ax = plt.subplots(figsize=(6, 4))
    trending_avg = df.groupby('trending_audio')['virality_score'].mean()
    labels = ['Sin audio trending', 'Con audio trending']
    ax.bar(labels, trending_avg.values, color=['#405DE6', '#E1306C'])
    ax.set_title('Viralidad promedio: audio trending vs no trending')
    ax.set_ylabel('Virality score promedio')
    save_plot('audio_trending_vs_non_trending.png')

    fig, ax = plt.subplots(figsize=(7, 4))
    sample = df.sample(2000, random_state=42)  # muestra para no saturar el scatter
    ax.scatter(sample['audio_popularity_score'], sample['engagement_rate'],
            alpha=0.3, color='#833AB4', s=10)
    ax.set_title('Popularidad del audio vs Engagement rate')
    ax.set_xlabel('Audio popularity score')
    ax.set_ylabel('Engagement rate')
    save_plot('audio_popularity_vs_engagement.png')

    percentage_improvement = round(
        (trending_avg[True] - trending_avg[False]) / trending_avg[False] * 100, 1
    )
    return render_template("audio.html",
        plot1='audio_trending_vs_non_trending.png',
        plot2='audio_popularity_vs_engagement.png',
        trending_improvement=percentage_improvement
    )

@app.route("/perfil", methods=["GET"])
def perfil():
    df = get_df()

    bins = [0, 1000, 10000, 100000, 500000, float('inf')]
    labels = ['<1K', '1K-10K', '10K-100K', '100K-500K', '500K+']
    df['follower_range'] = pd.cut(df['creator_followers'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_by_range = df.groupby('follower_range', observed=True)['virality_score'].mean()
    ax.bar(viral_by_range.index, viral_by_range.values, color='#F77737')
    ax.set_title('Viralidad promedio según cantidad de seguidores')
    ax.set_xlabel('Rango de seguidores')
    ax.set_ylabel('Virality score promedio')
    save_plot('profile_followers_virality.png')

    # 2. Mejor y peor horario para publicar
    fig, ax = plt.subplots(figsize=(10, 4))
    viral_by_hour = df.groupby('posting_time')['virality_score'].mean()
    colors = ['#E1306C' if v == viral_by_hour.max() else
            '#405DE6' if v == viral_by_hour.min() else '#AAAAAA'
        for v in viral_by_hour.values]
    ax.bar(viral_by_hour.index, viral_by_hour.values, color=colors)
    ax.set_title('Viralidad promedio por horario (rojo=mejor, azul=peor)')
    ax.set_xlabel('Hora')
    ax.set_ylabel('Virality score promedio')
    save_plot('profile_time.png')

    best_hour = int(viral_by_hour.idxmax())
    worst_hour = int(viral_by_hour.idxmin())


    return render_template("perfil.html",
        plot1='profile_followers_virality.png',
        plot2='profile_time.png',
        best_hour=best_hour,
        worst_hour=worst_hour
    )

@app.route("/imagen")
def imagen():
    df = get_df()
    bins = [0, 15, 30, 60, 90, float('inf')]
    labels = ['0-15s', '15-30s', '30-60s', '60-90s', '90s+']
    df['duration_range'] = pd.cut(df['reel_length_sec'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_duration = df.groupby('duration_range', observed=True)['virality_score'].mean()
    ax.bar(viral_duration.index, viral_duration.values, color='#FCAF45')
    ax.set_title('Viralidad según duración del reel')
    ax.set_xlabel('Duración')
    ax.set_ylabel('Virality score promedio')
    save_plot('image_duration.png')

    # 2. Calidad de video vs gancho inicial (¿qué importa más?)
    fig, ax = plt.subplots(figsize=(7, 4))
    corr_quality = df['video_quality_score'].corr(df['virality_score'])
    corr_hook = df['hook_strength_score'].corr(df['virality_score'])
    corr_editing = df['editing_quality_score'].corr(df['virality_score'])
    factors = ['Calidad de video', 'Gancho inicial', 'Calidad de edición']
    correlations = [corr_quality, corr_hook, corr_editing]
    colors = ['#E1306C' if c == max(correlations) else '#AAAAAA' for c in correlations]
    ax.barh(factors, correlations, color=colors)
    ax.set_title('¿Qué factor visual impacta más en la viralidad?')
    ax.set_xlabel('Correlación con virality score')
    save_plot('image_factors.png')

    return render_template("imagen.html",
        plot1='image_duration.png',
        plot2='image_factors.png',
        corr_hook=round(corr_hook, 3),
        corr_quality=round(corr_quality, 3)
    )

@app.route("/interacciones")
def interacciones():
    df = get_df()

    # 1. Likes / guardados / compartidos por horario
    fig, ax = plt.subplots(figsize=(10, 5))
    for col, color in [('likes', '#E1306C'), ('saves', '#405DE6'), ('shares', '#F77737')]:
        series = df.groupby('posting_time')[col].mean()
        ax.plot(series.index, series.values, label=col.capitalize(), color=color)
    ax.set_title('Interacciones promedio por horario')
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Cantidad promedio')
    ax.legend()
    save_plot('interactions_time.png')

    # 2. ¿Qué tipo de interacción lleva más a Explorar?
    fig, ax = plt.subplots(figsize=(8, 4))
    metrics = ['likes', 'comments', 'shares', 'saves']
    correlations = [df[m].corr(df['explore_page_boost'].astype(int)) for m in metrics]
    colors = ['#E1306C' if c == max(correlations) else '#AAAAAA' for c in correlations]
    ax.bar([m.capitalize() for m in metrics], correlations, color=colors)
    ax.set_title('¿Qué interacción predice mejor aparecer en Explorar?')
    ax.set_ylabel('Correlación con explore_page_boost')
    save_plot('interactions_explore.png')

    best_interaction = metrics[correlations.index(max(correlations))].capitalize()

    return render_template("interacciones.html",
        plot1='interactions_time.png',
        plot2='interactions_explore.png',
        best_interaction=best_interaction
    )

@app.route("/caption")  
def caption():
    df = get_df()

    # 1. Longitud del caption vs completion rate
    bins = [0, 50, 150, 300, float('inf')]
    labels = ['Corto (<50)', 'Medio (50-150)', 'Largo (150-300)', 'Muy largo (300+)']
    df['caption_range'] = pd.cut(df['caption_length'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    completion_caption = df.groupby('caption_range', observed=True)['completion_rate'].mean()
    ax.bar(completion_caption.index, completion_caption.values, color='#833AB4')
    ax.set_title('Tasa de completion según longitud del caption')
    ax.set_xlabel('Longitud del caption')
    ax.set_ylabel('Completion rate promedio')
    save_plot('caption_length.png')

    # 2. Cantidad de hashtags vs non_follower_reach_ratio
    fig, ax = plt.subplots(figsize=(8, 4))
    hashtag_reach = df.groupby('hashtags_count')['non_follower_reach_ratio'].mean()
    ax.plot(hashtag_reach.index, hashtag_reach.values, color='#405DE6', marker='o', markersize=3)
    ax.set_title('Hashtags usados vs alcance a no-seguidores')
    ax.set_xlabel('Cantidad de hashtags')
    ax.set_ylabel('Non-follower reach ratio promedio')
    save_plot('caption_hashtags.png')

    return render_template("caption.html",
        plot1='caption_length.png',
        plot2='caption_hashtags.png'
    )

if __name__ == "__main__":
    app.run(debug=True)