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
    virales = df[df['virality_score'] > 0.7]  # ajustá el umbral según el dataset
    porcentaje_viral = round(len(virales) / total_reels * 100, 1)
    avg_engagement = round(df['engagement_rate'].mean() * 100, 2)
    mejor_horario = int(df.groupby('posting_time')['virality_score'].mean().idxmax())

    # Gráfico: viralidad promedio por horario
    fig, ax = plt.subplots(figsize=(10, 4))
    horas = df.groupby('posting_time')['virality_score'].mean()
    ax.plot(horas.index, horas.values, marker='o', color='#E1306C')
    ax.set_title('Viralidad promedio según horario de publicación')
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Virality score promedio')
    save_plot('viralidad_por_hora.png')

    return render_template("index.html",
        total_reels=total_reels,
        porcentaje_viral=porcentaje_viral,
        avg_engagement=avg_engagement,
        mejor_horario=mejor_horario,
        plot='viralidad_por_hora.png'
    )

def generate_chart(x, y, type, title, xlabel, ylabel, agg=None):
    df = pd.read_sql(Reel.query.statement, db.engine)
    
    if agg == 'mean':
        df = df.groupby(x)[y].mean().reset_index()
    elif agg == 'sum':
        df = df.groupby(x)[y].sum().reset_index()
        
    plt.figure(figsize=(8,5))
    
    if type == 'line':
        plt.plot(df[x], df[y])
    elif type == 'bar':
        plt.bar(df[x], df[y])
    elif type == 'scatter':
        plt.scatter(df[x], df[y], alpha=0.5)
    else:
        raise ValueError("Tipo de gráfico no soportado")
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(f'static/plots/{title}.png')
    plt.close() 
    return str(title + ".png")

@app.route("/juego", methods=["GET"])
def juego():
    return render_template("juego.html")

@app.route("/audio", methods=["GET"])
def audio():
    df = get_df()
    fig, ax = plt.subplots(figsize=(6, 4))
    trending_avg = df.groupby('trending_audio')['virality_score'].mean()
    etiquetas = ['Sin audio trending', 'Con audio trending']
    ax.bar(etiquetas, trending_avg.values, color=['#405DE6', '#E1306C'])
    ax.set_title('Viralidad promedio: audio trending vs no trending')
    ax.set_ylabel('Virality score promedio')
    save_plot('audio_trending_vs_no.png')

    fig, ax = plt.subplots(figsize=(7, 4))
    sample = df.sample(2000, random_state=42)  # muestra para no saturar el scatter
    ax.scatter(sample['audio_popularity_score'], sample['engagement_rate'],
            alpha=0.3, color='#833AB4', s=10)
    ax.set_title('Popularidad del audio vs Engagement rate')
    ax.set_xlabel('Audio popularity score')
    ax.set_ylabel('Engagement rate')
    save_plot('audio_popularidad_vs_engagement.png')

    mejora_porcentual = round(
        (trending_avg[True] - trending_avg[False]) / trending_avg[False] * 100, 1
    )
    return render_template("audio.html",
        plot1='audio_trending_vs_no.png',
        plot2='audio_popularidad_vs_engagement.png',
        mejora_trending=mejora_porcentual
    )

@app.route("/perfil", methods=["GET"])
def perfil():
    df = get_df()

    bins = [0, 1000, 10000, 100000, 500000, float('inf')]
    labels = ['<1K', '1K-10K', '10K-100K', '100K-500K', '500K+']
    df['follower_range'] = pd.cut(df['creator_followers'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_por_rango = df.groupby('follower_range', observed=True)['virality_score'].mean()
    ax.bar(viral_por_rango.index, viral_por_rango.values, color='#F77737')
    ax.set_title('Viralidad promedio según cantidad de seguidores')
    ax.set_xlabel('Rango de seguidores')
    ax.set_ylabel('Virality score promedio')
    save_plot('perfil_seguidores_viralidad.png')

    # 2. Mejor y peor horario para publicar
    fig, ax = plt.subplots(figsize=(10, 4))
    viral_por_hora = df.groupby('posting_time')['virality_score'].mean()
    colores = ['#E1306C' if v == viral_por_hora.max() else
            '#405DE6' if v == viral_por_hora.min() else '#AAAAAA'
        for v in viral_por_hora.values]
    ax.bar(viral_por_hora.index, viral_por_hora.values, color=colores)
    ax.set_title('Viralidad promedio por horario (rojo=mejor, azul=peor)')
    ax.set_xlabel('Hora')
    ax.set_ylabel('Virality score promedio')
    save_plot('perfil_horario.png')

    mejor_hora = int(viral_por_hora.idxmax())
    peor_hora = int(viral_por_hora.idxmin())


    return render_template("perfil.html",
        plot1='perfil_seguidores_viralidad.png',
        plot2='perfil_horario.png',
        mejor_hora=mejor_hora,
        peor_hora=peor_hora
    )

@app.route("/imagen")
def imagen():
    df = get_df()
    bins = [0, 15, 30, 60, 90, float('inf')]
    labels = ['0-15s', '15-30s', '30-60s', '60-90s', '90s+']
    df['duracion_rango'] = pd.cut(df['reel_length_sec'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    viral_duracion = df.groupby('duracion_rango', observed=True)['virality_score'].mean()
    ax.bar(viral_duracion.index, viral_duracion.values, color='#FCAF45')
    ax.set_title('Viralidad según duración del reel')
    ax.set_xlabel('Duración')
    ax.set_ylabel('Virality score promedio')
    save_plot('imagen_duracion.png')

    # 2. Calidad de video vs gancho inicial (¿qué importa más?)
    fig, ax = plt.subplots(figsize=(7, 4))
    corr_calidad = df['video_quality_score'].corr(df['virality_score'])
    corr_gancho = df['hook_strength_score'].corr(df['virality_score'])
    corr_edicion = df['editing_quality_score'].corr(df['virality_score'])
    factores = ['Calidad de video', 'Gancho inicial', 'Calidad de edición']
    correlaciones = [corr_calidad, corr_gancho, corr_edicion]
    colores = ['#E1306C' if c == max(correlaciones) else '#AAAAAA' for c in correlaciones]
    ax.barh(factores, correlaciones, color=colores)
    ax.set_title('¿Qué factor visual impacta más en la viralidad?')
    ax.set_xlabel('Correlación con virality score')
    save_plot('imagen_factores.png')

    return render_template("imagen.html",
        plot1='imagen_duracion.png',
        plot2='imagen_factores.png',
        corr_gancho=round(corr_gancho, 3),
        corr_calidad=round(corr_calidad, 3)
    )

@app.route("/interacciones")
def interacciones():
    df = get_df()

    # 1. Likes / guardados / compartidos por horario
    fig, ax = plt.subplots(figsize=(10, 5))
    for col, color in [('likes', '#E1306C'), ('saves', '#405DE6'), ('shares', '#F77737')]:
        serie = df.groupby('posting_time')[col].mean()
        ax.plot(serie.index, serie.values, label=col.capitalize(), color=color)
    ax.set_title('Interacciones promedio por horario')
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Cantidad promedio')
    ax.legend()
    save_plot('interacciones_horario.png')

    # 2. ¿Qué tipo de interacción lleva más a Explorar?
    fig, ax = plt.subplots(figsize=(8, 4))
    metricas = ['likes', 'comments', 'shares', 'saves']
    correlaciones = [df[m].corr(df['explore_page_boost'].astype(int)) for m in metricas]
    colores = ['#E1306C' if c == max(correlaciones) else '#AAAAAA' for c in correlaciones]
    ax.bar([m.capitalize() for m in metricas], correlaciones, color=colores)
    ax.set_title('¿Qué interacción predice mejor aparecer en Explorar?')
    ax.set_ylabel('Correlación con explore_page_boost')
    save_plot('interacciones_explorar.png')

    mejor_interaccion = metricas[correlaciones.index(max(correlaciones))].capitalize()

    return render_template("interacciones.html",
        plot1='interacciones_horario.png',
        plot2='interacciones_explorar.png',
        mejor_interaccion=mejor_interaccion
    )

@app.route("/caption")  
def caption():
    df = get_df()

    # 1. Longitud del caption vs completion rate
    bins = [0, 50, 150, 300, float('inf')]
    labels = ['Corto (<50)', 'Medio (50-150)', 'Largo (150-300)', 'Muy largo (300+)']
    df['caption_rango'] = pd.cut(df['caption_length'], bins=bins, labels=labels)

    fig, ax = plt.subplots(figsize=(8, 4))
    completion_caption = df.groupby('caption_rango', observed=True)['completion_rate'].mean()
    ax.bar(completion_caption.index, completion_caption.values, color='#833AB4')
    ax.set_title('Tasa de completion según longitud del caption')
    ax.set_xlabel('Longitud del caption')
    ax.set_ylabel('Completion rate promedio')
    save_plot('caption_longitud.png')

    # 2. Cantidad de hashtags vs non_follower_reach_ratio
    fig, ax = plt.subplots(figsize=(8, 4))
    hashtag_reach = df.groupby('hashtags_count')['non_follower_reach_ratio'].mean()
    ax.plot(hashtag_reach.index, hashtag_reach.values, color='#405DE6', marker='o', markersize=3)
    ax.set_title('Hashtags usados vs alcance a no-seguidores')
    ax.set_xlabel('Cantidad de hashtags')
    ax.set_ylabel('Non-follower reach ratio promedio')
    save_plot('caption_hashtags.png')

    return render_template("caption.html",
        plot1='caption_longitud.png',
        plot2='caption_hashtags.png'
    )

if __name__ == "__main__":
    app.run(debug=True)