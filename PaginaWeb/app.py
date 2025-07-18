from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import base64
import io
from PIL import Image
import time
import json
from datetime import datetime, timedelta
import onnxruntime as ort
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'grupo01'

# Configuraciones MySQL
app.config['MYSQL_HOST'] = '192.168.0.101'       # IP servidor BDD
app.config['MYSQL_USER'] = 'root'               # Usuario BDD
app.config['MYSQL_PASSWORD'] = 'root'           # Contraseña BDD
app.config['MYSQL_DB'] = 'dyzen_db'             # Nombre de la BDD

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + app.config['MYSQL_USER'] + ':' + app.config['MYSQL_PASSWORD'] + '@' + app.config['MYSQL_HOST'] + '/' + app.config['MYSQL_DB']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuración
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modelos de base de datos
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    compressed_path = db.Column(db.String(255))
    original_size = db.Column(db.Integer)
    compressed_size = db.Column(db.Integer)
    compression_level = db.Column(db.Integer, default=16)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    username = db.Column(db.String(50), default='Anónimo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subreddit = db.Column(db.String(50), default='pics')
    post_metadata = db.Column(db.Text)

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    username = db.Column(db.String(50), default='Anónimo')
    content = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    user_ip = db.Column(db.String(50))
    vote_type = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_ip', 'comment_id', name='unique_vote'),
    )

class NetworkMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ip = db.Column(db.String(50))
    bandwidth = db.Column(db.Float)
    latency = db.Column(db.Float)
    quality = db.Column(db.String(20))
    recommended_compression = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    """Initializar base de datos"""
    db.create_all()

def get_network_conditions():
    """Obtener condiciones de red actuales"""
    return {'quality': 'medium', 'compression': 16, 'bandwidth': 50, 'latency': 100}

def enhance_image_espcn(image_path):
    """Mejorar imagen usando modelo ESPCN"""
    try:
        # Cargar imagen en RGB
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Reorganizar dimensiones a NCHW
        input_tensor = np.transpose(img_array, (2, 0, 1))  # HWC to CHW
        input_tensor = np.expand_dims(input_tensor, 0)     # Add batch dimension
        
        # Cargar modelo ONNX
        model_path = os.path.join(app.root_path, 'static/models/espcn_model.onnx')
        session = ort.InferenceSession(model_path)
        
        # Inferencia
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        output_tensor = session.run([output_name], {input_name: input_tensor})[0]
        
        # Postprocesamiento
        output_tensor = np.clip(output_tensor, 0, 1) * 255.0
        output_tensor = output_tensor.squeeze().transpose(1, 2, 0).astype(np.uint8)
        
        return Image.fromarray(output_tensor, 'RGB')
        
    except Exception as e:
        print(f"Error en procesamiento ESPCN: {e}")
        raise

def save_base64_image(base64_data, filename_prefix):
    """Guardar imagen desde datos base64"""
    try:
        # Extraer datos de la imagen
        header, data = base64_data.split(',', 1)
        image_data = base64.b64decode(data)
        
        # Crear nombre de archivo único
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename_prefix}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Guardar archivo
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Normalizar ruta para web
        return filepath.replace('\\', '/')
        
    except Exception as e:
        print(f"Error guardando imagen base64: {e}")
        return None

@app.route('/')
def index():
    """Página principal estilo Reddit"""
    posts = Post.query.order_by(Post.upvotes.desc(), Post.created_at.desc()).limit(20).all()
    
    posts_data = []
    for post in posts:
        post_data = {
            'id': post.id,
            'title': post.title,
            'image_path': post.image_path,
            'compressed_path': post.compressed_path,
            'upvotes': post.upvotes,
            'downvotes': post.downvotes,
            'username': post.username,
            'created_at': post.created_at,
            'subreddit': post.subreddit,
            'compression_level': post.compression_level,
            'score': post.upvotes - post.downvotes,
            'metadata': post.post_metadata
        }
        
        # Procesar metadatos si existen
        if post.post_metadata:
            try:
                metadata = json.loads(post.post_metadata)
                post_data['thumbnail_path'] = metadata.get('thumbnail_path')
                post_data['processing_method'] = metadata.get('processingMethod', 'onnx_client')
                post_data['model_used'] = metadata.get('modelUsed', 'unknown')
                post_data['espcn_applied'] = metadata.get('espcnApplied', False)
            except:
                post_data['thumbnail_path'] = None
                post_data['processing_method'] = 'unknown'
                post_data['model_used'] = 'unknown'
                post_data['espcn_applied'] = False
        
        # Usar thumbnail si está disponible, sino la imagen comprimida
        post_data['display_path'] = post_data.get('thumbnail_path') or post_data['compressed_path']
        
        # Obtener número de comentarios
        post_data['comment_count'] = Comment.query.filter_by(post_id=post.id).count()
        
        posts_data.append(post_data)
    
    network = get_network_conditions()
    return render_template('index.html', posts=posts_data, network=network)

@app.route('/submit', methods=['GET'])
def submit():
    """Página para subir nuevas imágenes - Solo interfaz, procesamiento en cliente"""
    network = get_network_conditions()
    return render_template('submit.html', network=network)

@app.route('/submit_processed', methods=['POST'])
def submit_processed():
    """Endpoint para recibir imágenes ya procesadas por el cliente"""
    try:
        title = request.form.get('title')
        subreddit = request.form.get('subreddit', 'pics')
        username = request.form.get('username', 'Anónimo')
        processed_image_data = request.form.get('processed_image_data')
        thumbnail_data = request.form.get('thumbnail_data')
        processing_metadata = request.form.get('processing_metadata')
        
        if not all([title, processed_image_data, thumbnail_data, processing_metadata]):
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Parsear metadatos del procesamiento del cliente
        metadata = json.loads(processing_metadata)
        
        # Resolver nivel de compresión si es "auto"
        compression_level = metadata.get('compressionLevel', 16)
        if compression_level == 'auto':
            # Obtener condiciones de red actuales para determinar el nivel
            network_conditions = get_network_conditions()
            compression_level = network_conditions['compression']
            # Actualizar metadatos con el nivel resuelto
            metadata['compressionLevel'] = compression_level
            metadata['resolvedFromAuto'] = True
        else:
            # Asegurar que sea un entero
            try:
                compression_level = int(compression_level)
            except (ValueError, TypeError):
                compression_level = 16  # Valor por defecto
        
        print(f"📥 Recibiendo imagen procesada por cliente:")
        print(f"   Método: {metadata.get('processingMethod', 'unknown')}")
        print(f"   Modelo: {metadata.get('modelUsed', 'unknown')}")
        print(f"   ESPCN: {metadata.get('espcnApplied', False)}")
        print(f"   Tamaño original: {metadata.get('originalSize', 0)} bytes")
        print(f"   Tamaño procesado: {metadata.get('processedSize', 0)} bytes")
        print(f"   Nivel de compresión: {compression_level}")
        
        # Guardar imágenes procesadas (ya vienen optimizadas del cliente)
        compressed_path = save_base64_image(processed_image_data, 'client_processed')
        thumbnail_path = save_base64_image(thumbnail_data, 'client_thumbnail')
        
        if not compressed_path or not thumbnail_path:
            return jsonify({'error': 'Error guardando imágenes procesadas'}), 500
        
        # Obtener tamaños de archivo
        compressed_size = os.path.getsize(compressed_path)
        thumbnail_size = os.path.getsize(thumbnail_path)
        
        # Actualizar metadatos con rutas del servidor
        metadata.update({
            'thumbnail_path': thumbnail_path,
            'compressed_path': compressed_path,
            'server_processed': False,
            'client_processed': True,
            'server_received_at': time.time()
        })
        
        # Guardar en base de datos
        new_post = Post(
            title=title,
            image_path=compressed_path,  # Usar imagen procesada como original
            compressed_path=compressed_path,
            original_size=metadata.get('originalSize', compressed_size),
            compressed_size=compressed_size,
            compression_level=compression_level,
            username=username,
            subreddit=subreddit,
            post_metadata=json.dumps(metadata)
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        print(f"✅ Imagen guardada con ID: {new_post.id}")
        
        return jsonify({
            'success': True,
            'message': 'Imagen procesada por cliente recibida correctamente',
            'post_id': new_post.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en submit_processed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/post/<int:post_id>')
def view_post(post_id):
    """Ver post individual con comentarios"""
    post = Post.query.get_or_404(post_id)
    
    post_data = {
        'id': post.id,
        'title': post.title,
        'image_path': post.image_path,
        'compressed_path': post.compressed_path,
        'upvotes': post.upvotes,
        'downvotes': post.downvotes,
        'username': post.username,
        'created_at': post.created_at,
        'subreddit': post.subreddit,
        'compression_level': post.compression_level,
        'original_size': post.original_size,
        'compressed_size': post.compressed_size,
        'metadata': json.loads(post.post_metadata) if post.post_metadata else {}
    }
    
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.upvotes.desc(), Comment.created_at.asc()).all()
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'username': comment.username,
            'content': comment.content,
            'upvotes': comment.upvotes,
            'downvotes': comment.downvotes,
            'created_at': comment.created_at
        })
    
    return render_template('post.html', post=post_data, comments=comments_data)

@app.route('/api/enhance/<int:post_id>', methods=['POST'])
def enhance_post(post_id):
    """Endpoint para mejorar imagen con ESPCN en el servidor"""
    try:
        # Obtener información del post
        post = Post.query.get_or_404(post_id)
        
        # Parsear metadatos existentes
        metadata = json.loads(post.post_metadata) if post.post_metadata else {}
        
        # Verificar si ya está mejorada
        if metadata.get('espcn_enhanced_path'):
            return jsonify({
                'success': True,
                'enhanced_path': metadata['espcn_enhanced_path'].replace('static/', ''),
                'already_enhanced': True
            })
        
        # Procesar imagen en el servidor
        image_path = os.path.join(app.root_path, post.compressed_path)
        enhanced_img = enhance_image_espcn(image_path)
        
        # Guardar imagen mejorada
        timestamp = str(int(time.time()))
        enhanced_filename = f"espcn_enhanced_{post_id}_{timestamp}.jpg"
        enhanced_path = os.path.join(UPLOAD_FOLDER, enhanced_filename)
        enhanced_img.save(enhanced_path)
        enhanced_path = enhanced_path.replace('\\', '/')
        
        # Actualizar metadatos
        metadata.update({
            'espcn_enhanced_path': enhanced_path,
            'espcn_applied': True,
            'processing_method': 'server_espcn',
            'server_processed_at': time.time()
        })
        
        # Actualizar base de datos
        post.post_metadata = json.dumps(metadata)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enhanced_path': enhanced_path.replace('static/', ''),
            'message': 'Imagen mejorada con ESPCN en el servidor'
        })
        
    except Exception as e:
        print(f"Error en enhance_post: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhance/save/<int:post_id>', methods=['POST'])
def save_enhanced_image(post_id):
    """Guardar imagen mejorada con ESPCN desde el cliente"""
    try:
        data = request.get_json()
        enhanced_image_data = data.get('enhanced_image_data')
        
        if not enhanced_image_data:
            return jsonify({'error': 'Datos de imagen mejorada requeridos'}), 400
        
        # Guardar imagen mejorada
        enhanced_path = save_base64_image(enhanced_image_data, f'enhanced_{post_id}')
        
        if not enhanced_path:
            return jsonify({'error': 'Error guardando imagen mejorada'}), 500
        
        # Actualizar metadatos del post
        post = Post.query.get_or_404(post_id)
        
        metadata = json.loads(post.post_metadata) if post.post_metadata else {}
        metadata.update({
            'espcn_enhanced_path': enhanced_path,
            'espcn_enhanced_at': time.time(),
            'espcn_applied': True
        })
        
        post.post_metadata = json.dumps(metadata)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enhanced_path': enhanced_path.replace('static/', ''),
            'message': 'Imagen mejorada guardada exitosamente'
        })
        
    except Exception as e:
        print(f"Error guardando imagen mejorada: {e}")
        return jsonify({'error': str(e)}), 500

# APIs para funcionalidad básica (sin procesamiento de imágenes)
@app.route('/api/vote', methods=['POST'])
def vote():
    """API para votar posts y comentarios"""
    data = request.get_json()
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    vote_type = data.get('vote_type')
    user_ip = request.remote_addr
    
    try:
        # Check if the user has already voted
        if post_id:
            existing_vote = Vote.query.filter_by(post_id=post_id, user_ip=user_ip, comment_id=None).first()
        else:
            existing_vote = Vote.query.filter_by(comment_id=comment_id, user_ip=user_ip, post_id=None).first()
            
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                db.session.delete(existing_vote)
            else:
                existing_vote.vote_type = vote_type
        else:
            new_vote = Vote(post_id=post_id, comment_id=comment_id, user_ip=user_ip, vote_type=vote_type)
            db.session.add(new_vote)
            
        db.session.commit()
        
        # Update the upvotes and downvotes count
        if post_id:
            upvotes = Vote.query.filter_by(post_id=post_id, vote_type='up').count()
            downvotes = Vote.query.filter_by(post_id=post_id, vote_type='down').count()
            
            # Update post counts
            post = Post.query.get(post_id)
            if post:
                post.upvotes = upvotes
                post.downvotes = downvotes
                db.session.commit()
        else:
            upvotes = Vote.query.filter_by(comment_id=comment_id, vote_type='up').count()
            downvotes = Vote.query.filter_by(comment_id=comment_id, vote_type='down').count()
            
            # Update comment counts
            comment = Comment.query.get(comment_id)
            if comment:
                comment.upvotes = upvotes
                comment.downvotes = downvotes
                db.session.commit()
            
        return jsonify({'upvotes': upvotes, 'downvotes': downvotes})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error en votación: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/comment', methods=['POST'])
def add_comment():
    """API para agregar comentarios"""
    data = request.get_json()
    post_id = data.get('post_id')
    content = data.get('content')
    username = data.get('username', 'Anónimo')
    
    if not post_id or not content:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    new_comment = Comment(post_id=post_id, username=username, content=content)
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({'success': True, 'comment_id': new_comment.id})

@app.route('/api/network')
def network_status():
    """API para obtener condiciones de red"""
    return jsonify(get_network_conditions())

@app.route('/api/network/update', methods=['POST'])
def update_network_conditions():
    """Endpoint para actualizar condiciones de red desde el cliente"""
    try:
        data = request.get_json()
        
        required_fields = ['bandwidth', 'latency', 'quality', 'compression']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Datos incompletos'}), 400
        
        new_metrics = NetworkMetrics(
            user_ip=request.remote_addr,
            bandwidth=data['bandwidth'],
            latency=data['latency'],
            quality=data['quality'],
            recommended_compression=data['compression']
        )
        
        db.session.add(new_metrics)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error actualizando condiciones de red: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping')
def ping():
    """Endpoint simple para medir latencia"""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

@app.route('/api/models/status')
def models_status():
    """API para verificar estado de modelos ONNX"""
    models_dir = 'static/models'
    status = {
        'autoencoders': {},
        'espcn': False,
        'models_directory_exists': os.path.exists(models_dir)
    }
    
    # Verificar autoencoders
    for level in [8, 16, 32]:
        model_path = os.path.join(models_dir, f'autoencoder_b{level}.onnx')
        status['autoencoders'][level] = os.path.exists(model_path)
    
    # Verificar ESPCN
    espcn_path = os.path.join(models_dir, 'espcn_model.onnx')
    status['espcn'] = os.path.exists(espcn_path)
    
    return jsonify(status)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("🚀 Servidor Dyzen iniciado")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
