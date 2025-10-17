from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_basicauth import BasicAuth
from datetime import datetime, timedelta
import os
import csv
import io
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Database configuration - use PostgreSQL in production, SQLite for local development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Digital Ocean and some providers use postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development with SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///license_plates.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Basic Auth configuration for staging
app.config['BASIC_AUTH_USERNAME'] = os.environ.get('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('BASIC_AUTH_PASSWORD')
app.config['BASIC_AUTH_FORCE'] = os.environ.get('FLASK_ENV') == 'production' # Force auth only in production/staging

basic_auth = BasicAuth(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Sighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(2), nullable=False)
    license_plate = db.Column(db.String(15), nullable=False)
    car_make = db.Column(db.String(50), nullable=False)
    car_model = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Sighting {self.license_plate} - {self.car_make} {self.car_model}>"


@app.route('/')
def index():
    sort_by = request.args.get('sort_by', 'date_desc')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    query = Sighting.query

    # Date range filtering
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Sighting.timestamp >= start_date)
        except (ValueError, TypeError):
            flash('Invalid start date format. Please use YYYY-MM-DD.', 'error')
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sighting.timestamp < end_date)
        except (ValueError, TypeError):
            flash('Invalid end date format. Please use YYYY-MM-DD.', 'error')

    # Sorting logic
    if sort_by == 'date_asc':
        query = query.order_by(Sighting.timestamp.asc())
    elif sort_by == 'plate_asc':
        query = query.order_by(Sighting.state.asc(), Sighting.license_plate.asc())
    elif sort_by == 'plate_desc':
        query = query.order_by(Sighting.state.desc(), Sighting.license_plate.desc())
    elif sort_by == 'make_asc':
        query = query.order_by(Sighting.car_make.asc(), Sighting.car_model.asc())
    elif sort_by == 'make_desc':
        query = query.order_by(Sighting.car_make.desc(), Sighting.car_model.desc())
    else:  # Default sort
        query = query.order_by(Sighting.timestamp.desc())

    sightings = query.all()

    return render_template(
        'index.html',
        sightings=sightings,
        sort_by=sort_by,
        start_date=start_date_str,
        end_date=end_date_str
    )

@app.route('/add', methods=['GET', 'POST'])
def add_sighting():
    if request.method == 'POST':
        try:
            sighting_time_str = request.form.get('sighting_time')
            timestamp = datetime.strptime(sighting_time_str, '%Y-%m-%dT%H:%M') if sighting_time_str else datetime.utcnow()

            sighting = Sighting(
                state=request.form['state'].upper(),
                license_plate=request.form['license_plate'].upper(),
                car_make=request.form['car_make'],
                car_model=request.form['car_model'],
                color=request.form['color'],
                location=request.form.get('location'),
                timestamp=timestamp,
                notes=request.form.get('notes')
            )
            db.session.add(sighting)
            db.session.commit()
            flash('Sighting added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding sighting: {e}', 'error')
    return render_template('add_sighting.html')

@app.route('/search', methods=['GET'])
def search():
    state = request.args.get('state', '').upper().strip()
    plate = request.args.get('plate', '').upper().strip()

    if not state and not plate:
        return redirect(url_for('index'))

    query = Sighting.query

    if state:
        query = query.filter(Sighting.state == state)
    
    if plate:
        query = query.filter(Sighting.license_plate.like(f'%{plate}%'))

    sightings = query.order_by(Sighting.timestamp.desc()).all()
    
    return render_template('search.html', state=state, plate=plate, sightings=sightings)

@app.route('/edit/<int:sighting_id>', methods=['GET', 'POST'])
def edit_sighting(sighting_id):
    sighting = db.session.get(Sighting, sighting_id)
    if not sighting:
        flash('Sighting not found.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            sighting_time_str = request.form.get('sighting_time')
            timestamp = datetime.strptime(sighting_time_str, '%Y-%m-%dT%H:%M') if sighting_time_str else sighting.timestamp
            
            sighting.state = request.form['state'].upper()
            sighting.license_plate = request.form['license_plate'].upper()
            sighting.car_make = request.form['car_make']
            sighting.car_model = request.form['car_model']
            sighting.color = request.form['color']
            sighting.location = request.form.get('location')
            sighting.timestamp = timestamp
            sighting.notes = request.form.get('notes')
            
            db.session.commit()
            flash('Sighting updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating sighting: {e}', 'error')
    
    return render_template('edit_sighting.html', sighting=sighting)

@app.route('/delete/<int:sighting_id>', methods=['POST'])
def delete_sighting(sighting_id):
    sighting = db.session.get(Sighting, sighting_id)
    if sighting:
        try:
            db.session.delete(sighting)
            db.session.commit()
            flash('Sighting deleted successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting sighting: {e}', 'error')
    else:
        flash('Sighting not found.', 'error')
    return redirect(url_for('index'))

@app.route('/api/car_info/<string:plate>')
def get_car_info(plate):
    sighting = Sighting.query.filter_by(license_plate=plate.upper()).order_by(Sighting.timestamp.desc()).first()
    if sighting:
        return {
            'found': True,
            'car_make': sighting.car_make,
            'car_model': sighting.car_model,
            'color': sighting.color
        }
    return {'found': False}

@app.route('/export/csv')
def export_csv():
    include_notes = request.args.get('include_notes', 'true').lower() == 'true'
    sightings = Sighting.query.order_by(Sighting.timestamp.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Define fields
    if include_notes:
        fieldnames = ['state', 'license_plate', 'car_make', 'car_model', 'color', 'location', 'timestamp', 'notes']
    else:
        fieldnames = ['state', 'license_plate', 'car_make', 'car_model', 'color', 'location', 'timestamp']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for sighting in sightings:
        row = {
            'state': sighting.state or '',
            'license_plate': sighting.license_plate or '',
            'car_make': sighting.car_make or '',
            'car_model': sighting.car_model or '',
            'color': sighting.color or '',
            'location': sighting.location or '',
            'timestamp': sighting.timestamp.strftime('%Y-%m-%d %H:%M:%S') if sighting.timestamp else '',
        }
        if include_notes:
            row['notes'] = sighting.notes or ''
        writer.writerow(row)
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=license_plates_export.csv'}
    )

@app.route('/export/python')
def export_python():
    include_notes = request.args.get('include_notes', 'true').lower() == 'true'
    sightings = Sighting.query.order_by(Sighting.timestamp.desc()).all()
    
    # Build Python seed format
    lines = []
    lines.append('# Generated export from License Plate Tracker')
    lines.append('# Copy the plates_data list into your seed_data.py file')
    lines.append('')
    lines.append('plates_data = [')
    
    for sighting in sightings:
        data_dict = {
            'state': sighting.state or '',
            'plate': sighting.license_plate or '',
            'make': sighting.car_make or '',
            'model': sighting.car_model or '',
            'color': sighting.color or '',
            'location': sighting.location or '',
            'timestamp': sighting.timestamp.strftime('%Y-%m-%d %H:%M:%S') if sighting.timestamp else '',
        }
        if include_notes:
            data_dict['notes'] = sighting.notes or ''
        
        # Format as Python dictionary
        items = ', '.join(f'"{k}": "{v}"' for k, v in data_dict.items())
        lines.append(f'    {{{items}}},')
    
    lines.append(']')
    
    output = '\n'.join(lines)
    
    return Response(
        output,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=license_plates_seed.py'}
    )

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


if __name__ == '__main__':
    # Only enable debug mode in development, never in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
