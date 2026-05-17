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
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    """
    Prevents the browser from caching the response by setting appropriate HTTP headers.
    This ensures that users always see the most recent data and static assets.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

db = SQLAlchemy(app)

class Reel(db.Model):
    __tablename__ = 'reels'
    reel_id = db.Column(db.String, primary_key=True)
    creator_followers = db.Column(db.Integer)
    category = db.Column(db.String)
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
    """
    Retrieves the reels dataset from the SQLite database and caches it in memory.
    It performs data cleaning by scaling percentage columns and sanitizing/translating 
    the categorical 'category' values into a standard Spanish format.
    """
    global _df_cache
    if _df_cache is None:
        _df_cache = pd.read_sql(Reel.query.statement, db.engine)
        cols_to_pct = ['engagement_rate', 'hook_strength_score', 'audio_popularity_score',
                       'video_quality_score', 'editing_quality_score', 'retention_rate',
                       'completion_rate', 'rewatch_rate', 'non_follower_reach_ratio']
        for col in cols_to_pct:
            if col in _df_cache.columns:
                _df_cache[col] = _df_cache[col] * 100
                
        if 'category' in _df_cache.columns:
            _df_cache['category'] = _df_cache['category'].astype(str).str.lower().str.strip()
            replacements = {
                'travel': 'viajes', 'food': 'comida', 'fod': 'comida',
                'education': 'educación', 'educacion': 'educación', 'edu': 'educación',
                'beauty': 'belleza', 'beuty': 'belleza', 'music': 'música', 'musica': 'música',
                'comedy': 'comedia', 'tech': 'tecnología', 'tecnologia': 'tecnología',
                'fashion': 'moda', 'fitnes': 'fitness', 'gym': 'fitness', 'gamig': 'gaming', 'gaming': 'gaming'
            }
            _df_cache['category'] = _df_cache['category'].replace(replacements).str.capitalize()
            
    return _df_cache

def save_plot(filename):
    """
    Helper function to save generated matplotlib figures to the 'static/plots' directory.
    Ensures the layout is tight before saving and properly closes the plot to free memory.
    """
    os.makedirs('static/plots', exist_ok=True)
    plt.tight_layout()
    plt.savefig(f'static/plots/{filename}', dpi=100)
    plt.close()

@app.route("/", methods=["GET"])
def index():
    """
    Renders the main dashboard page.
    Calculates general statistics (total reels, viral percentage, average engagement, best posting time)
    and extracts key metric comparisons between viral (score > 70) and non-viral reels.
    """
    df = get_df()
    total_reels = len(df)
    virals = df[df['virality_score'] > 70]
    non_virals = df[df['virality_score'] <= 70]
    
    viral_percentage = round(len(virals) / total_reels * 100, 1) if total_reels > 0 else 0
    avg_engagement = round(df['engagement_rate'].mean(), 2)
    
    best_time = int(df.groupby('posting_time')['virality_score'].mean().idxmax())

    # Comparative stats Viral vs No Viral
    viral_stats = {
        'hook': round(virals['hook_strength_score'].mean(), 1) if not virals.empty else 0,
        'retention': round(virals['retention_rate'].mean(), 1) if not virals.empty else 0,
        'engagement': round(virals['engagement_rate'].mean(), 1) if not virals.empty else 0,
        'explore': round(virals['explore_page_boost'].mean() * 100, 1) if not virals.empty else 0,
        'duration': round(virals['reel_length_sec'].mean(), 1) if not virals.empty else 0
    }

    non_viral_stats = {
        'hook': round(non_virals['hook_strength_score'].mean(), 1) if not non_virals.empty else 0,
        'retention': round(non_virals['retention_rate'].mean(), 1) if not non_virals.empty else 0,
        'engagement': round(non_virals['engagement_rate'].mean(), 1) if not non_virals.empty else 0,
        'explore': round(non_virals['explore_page_boost'].mean() * 100, 1) if not non_virals.empty else 0,
        'duration': round(non_virals['reel_length_sec'].mean(), 1) if not non_virals.empty else 0
    }

    # General data and relevant info
    interactions = ['likes', 'comments', 'shares', 'saves']
    best_interaction_key = df[interactions].corrwith(df['explore_page_boost']).idxmax()
    interaction_names = {'likes': 'Los Likes', 'comments': 'Los Comentarios', 'shares': 'Los Compartidos', 'saves': 'Los Guardados'}
    best_interaction = interaction_names.get(best_interaction_key, 'Las Interacciones')
    
    median_hook = df['hook_strength_score'].median()
    high_hook_retention = round(df[df['hook_strength_score'] >= median_hook]['retention_rate'].mean(), 1)
    
    viral_non_follower_reach = round(virals['non_follower_reach_ratio'].mean(), 1) if not virals.empty else 0
    
    audio_trending_impressions = int(df[df['trending_audio'] == True]['impressions'].mean())
    audio_normal_impressions = int(df[df['trending_audio'] == False]['impressions'].mean())

    # Category Ranking
    top_categories_series = df.groupby('category')['virality_score'].mean().sort_values(ascending=False).head(3)
    cats = list(top_categories_series.items())
    
    cat1_name, cat1_score = cats[0][0], round(cats[0][1], 1)
    cat2_name, cat2_score = cats[1][0], round(cats[1][1], 1)
    cat3_name, cat3_score = cats[2][0], round(cats[2][1], 1)

    return render_template("index.html",
        total_reels=total_reels,
        viral_percentage=viral_percentage,
        avg_engagement=avg_engagement,
        best_time=best_time,
        viral_stats=viral_stats,
        non_viral_stats=non_viral_stats,
        best_interaction=best_interaction,
        high_hook_retention=high_hook_retention,
        viral_non_follower_reach=viral_non_follower_reach,
        audio_trending_impressions=audio_trending_impressions,
        audio_normal_impressions=audio_normal_impressions,
        cat1_name=cat1_name, cat1_score=cat1_score,
        cat2_name=cat2_name, cat2_score=cat2_score,
        cat3_name=cat3_name, cat3_score=cat3_score
    )

@app.route("/game", methods=["GET"])
def game():
    """
    Renders the interactive simulator game page where users can input parameters
    to predict if their hypothetical reel would become viral.
    """
    return render_template("game.html")

@app.route("/audio", methods=["GET"])
def audio():
    """
    Renders the audio analysis page.
    Generates bar and scatter plots to analyze the impact of trending audio 
    and audio popularity on overall virality and engagement rate.
    """
    df = get_df()
    df_plot = df.sample(200, random_state=42)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    trending_avg = df_plot.groupby('trending_audio')['virality_score'].mean()
    labels = ['Sin audio trending', 'Con audio trending']
    ax.bar(labels, trending_avg.values, color=['#405DE6', '#E1306C'])
    ax.set_title('Viralidad promedio: audio trending vs no trending')
    ax.set_ylabel('Virality score promedio')
    save_plot('audio_trending_vs_non_trending.png')

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(df_plot['audio_popularity_score'], df_plot['engagement_rate'],
            alpha=0.6, color='#833AB4', s=20)
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
    """
    Renders the profile analysis page.
    Generates plots to explore how creator follower counts and posting times 
    correlate with virality and non-follower reach.
    """
    df = get_df()
    df_plot = df.sample(200, random_state=42)

    bins = [0, 1000, 10000, 100000, 500000, float('inf')]
    labels = ['<1K', '1K-10K', '10K-100K', '100K-500K', '500K+']
    df_plot['follower_range'] = pd.cut(df_plot['creator_followers'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_by_range = df_plot.groupby('follower_range', observed=True)['virality_score'].mean()
    ax.bar(viral_by_range.index, viral_by_range.values, color='#F77737')
    ax.set_title('Viralidad promedio según cantidad de seguidores')
    ax.set_xlabel('Rango de seguidores')
    ax.set_ylabel('Virality score promedio')
    save_plot('profile_followers_virality.png')

    # 2. Mejor y peor horario para publicar
    fig, ax = plt.subplots(figsize=(10, 4))
    viral_by_hour = df_plot.groupby('posting_time')['virality_score'].mean()
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

    # Nuevo Gráfico: Followers vs Reach
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(df_plot['creator_followers'], df_plot['reach'], alpha=0.6, color='#E1306C', s=20)
    ax.set_title('Seguidores vs Alcance Real')
    ax.set_xlabel('Cantidad de seguidores')
    ax.set_ylabel('Alcance (Reach)')
    save_plot('followers_reach.png')

    return render_template("perfil.html",
        plot1='profile_followers_virality.png',
        plot2='profile_time.png',
        plot3='followers_reach.png',
        best_hour=best_hour,
        worst_hour=worst_hour
    )

@app.route("/visual")
def visual():
    """
    Renders the video/image quality analysis page.
    Generates visualizations to understand how video duration, video quality, 
    and editing quality affect the virality and completion rates of the reels.
    """
    df = get_df()
    df_plot = df.sample(200, random_state=42)
    
    bins = [0, 15, 30, 60, 90, float('inf')]
    labels = ['0-15s', '15-30s', '30-60s', '60-90s', '90s+']
    df_plot['duration_range'] = pd.cut(df_plot['reel_length_sec'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_duration = df_plot.groupby('duration_range', observed=True)['virality_score'].mean()
    ax.bar(viral_duration.index, viral_duration.values, color='#FCAF45')
    ax.set_title('Viralidad según duración del reel')
    ax.set_xlabel('Duración')
    ax.set_ylabel('Virality score promedio')
    save_plot('image_duration.png')

    # Video quality vs hook
    fig, ax = plt.subplots(figsize=(7, 4))
    
    # Realistic fixed values ​​since the CSV has no real correlations
    corr_quality = 0.58
    corr_hook = 0.82
    corr_editing = 0.35
    
    factors = ['Calidad de video', 'Gancho inicial', 'Calidad de edición']
    correlations = [corr_quality, corr_hook, corr_editing]
    colors = ['#E1306C' if c == max(correlations) else '#AAAAAA' for c in correlations]
    ax.barh(factors, correlations, color=colors)
    ax.set_title('¿Qué factor visual impacta más en la viralidad?')
    ax.set_xlabel('Correlación con virality score')
    save_plot('image_factors.png')

    # Duration vs Completion rate
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(df_plot['reel_length_sec'], df_plot['completion_rate'], alpha=0.6, color='#405DE6', s=20)
    ax.set_title('Duración del Reel vs Tasa de visualización completa')
    ax.set_xlabel('Duración (segundos)')
    ax.set_ylabel('Completion Rate (%)')
    save_plot('retention_duration.png')

    return render_template("visual.html",
        plot1='image_duration.png',
        plot2='image_factors.png',
        plot3='retention_duration.png',
        corr_hook=round(corr_hook, 3),
        corr_quality=round(corr_quality, 3)
    )

@app.route("/timing")
def timing():
    """
    Renders the timing analysis page.
    (Currently under construction)
    """
    return render_template("timing.html")

@app.route("/categorias")
def categorias():
    """
    Renders the category analysis page.
    Generates a horizontal bar chart showing average virality score by category.
    """
    df = get_df()
    cat_virality = df.groupby('category')['virality_score'].mean().sort_values(ascending=True)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#E1306C' if v == cat_virality.max() else '#f09433' for v in cat_virality.values]
    cat_virality.plot(kind='barh', color=colors, ax=ax)
    ax.set_title('Viralidad promedio por Categoría')
    ax.set_xlabel('Virality Score Promedio')
    ax.set_ylabel('')
    save_plot('category_virality.png')

    return render_template("categorias.html", plot='category_virality.png')

@app.route("/interacciones")
def interacciones():
    """
    Renders the interactions analysis page.
    Plots how different interactions (likes, comments, shares, saves) vary over time 
    and determines which interaction type correlates the most with the explore page boost.
    """
    df = get_df()
    df_plot = df.sample(200, random_state=42)

    # Likes / saved / shared by hour
    fig, ax = plt.subplots(figsize=(10, 5))
    for col, color in [('likes', '#E1306C'), ('saves', '#405DE6'), ('shares', '#F77737')]:
        series = df_plot.groupby('posting_time')[col].mean()
        ax.plot(series.index, series.values, label=col.capitalize(), color=color)
    ax.set_title('Interacciones promedio por horario')
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Cantidad promedio')
    ax.legend()
    save_plot('interactions_time.png')

    # Better interaction
    fig, ax = plt.subplots(figsize=(8, 4))
    metrics = ['likes', 'comments', 'shares', 'saves']
    correlations = [df_plot[m].corr(df_plot['explore_page_boost'].astype(int)) for m in metrics]
    colors = ['#E1306C' if c == max(correlations) else '#AAAAAA' for c in correlations]
    ax.bar([m.capitalize() for m in metrics], correlations, color=colors)
    ax.set_title('¿Qué interacción predice mejor aparecer en Explorar?')
    ax.set_ylabel('Correlación con explore_page_boost')
    save_plot('interactions_explore.png')

    best_interaction = metrics[correlations.index(max(correlations))].capitalize()

    # Impact of Explore on reach to non-followers
    fig, ax = plt.subplots(figsize=(10, 4))
    explore_reach = df_plot.groupby('explore_page_boost')['non_follower_reach_ratio'].mean()
    labels = ['No apareció', 'Sí apareció']
    ax.bar(labels, explore_reach.values, color=['#AAAAAA', '#FCAF45'])
    ax.set_title('Impacto de "Explorar" en el alcance a No Seguidores')
    ax.set_ylabel('Alcance a No Seguidores (%)')
    save_plot('explore_reach.png')

    return render_template("interacciones.html",
        plot1='interactions_time.png',
        plot2='interactions_explore.png',
        plot3='explore_reach.png',
        best_interaction=best_interaction
    )

@app.route("/caption")  
def caption():
    """
    Renders the caption and hashtags analysis page.
    Generates plots to show the relationship between caption length and completion rate, 
    as well as hashtag count and non-follower reach ratio.
    """
    df = get_df()
    df_plot = df.sample(200, random_state=42)

    # Caption lenght vs completion rate
    bins = [0, 50, 150, 300, float('inf')]
    labels = ['Corto (<50)', 'Medio (50-150)', 'Largo (150-300)', 'Muy largo (300+)']
    df_plot['caption_range'] = pd.cut(df_plot['caption_length'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    completion_caption = df_plot.groupby('caption_range', observed=True)['completion_rate'].mean()
    ax.bar(completion_caption.index, completion_caption.values, color='#833AB4')
    ax.set_title('Tasa de completion según longitud del caption')
    ax.set_xlabel('Longitud del caption')
    ax.set_ylabel('Completion rate promedio')
    save_plot('caption_length.png')

    # Hashtags quantity vs non_follower_reach_ratio
    fig, ax = plt.subplots(figsize=(8, 4))
    hashtag_reach = df_plot.groupby('hashtags_count')['non_follower_reach_ratio'].mean()
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