from datetime import datetime
from app import app, db, Sighting

def seed_database():
    with app.app_context():
        # Clear existing data
        db.session.query(Sighting).delete()
        
        # Seed data with fictional example license plates for demonstration purposes
        plates_data = [
            {"state": "CA", "plate": "ABC1234", "make": "Honda", "model": "Civic", "color": "Blue", "timestamp": "2025-10-10 09:15:00"},
            {"state": "NY", "plate": "XYZ9876", "make": "Toyota", "model": "Camry", "color": "Silver", "timestamp": "2025-10-09 22:30:00"},
            {"state": "TX", "plate": "DEF5678", "make": "Ford", "model": "F-150", "color": "Red", "timestamp": "2025-10-09 14:00:00"},
            {"state": "FL", "plate": "GHI2345", "make": "Chevrolet", "model": "Silverado", "color": "Black", "timestamp": "2025-10-08 18:45:00"},
            {"state": "CA", "plate": "JKL6789", "make": "Tesla", "model": "Model 3", "color": "White", "timestamp": "2025-10-08 11:20:00"},
            {"state": "NY", "plate": "MNO1234", "make": "BMW", "model": "X5", "color": "Grey", "timestamp": "2025-10-07 08:05:00"},
            {"state": "TX", "plate": "PQR5678", "make": "Mazda", "model": "CX-5", "color": "Blue", "timestamp": "2025-10-06 17:55:00"},
            {"state": "FL", "plate": "STU9012", "make": "Nissan", "model": "Altima", "color": "Green", "timestamp": "2025-10-05 12:10:00"},
            {"state": "CA", "plate": "VWX3456", "make": "Hyundai", "model": "Tucson", "color": "Orange", "timestamp": "2025-10-04 16:00:00"},
        ]
        
        for data in plates_data:
            sighting = Sighting(
                state=data["state"],
                license_plate=data["plate"],
                car_make=data["make"],
                car_model=data["model"],
                color=data["color"],
                timestamp=datetime.strptime(data["timestamp"], '%Y-%m-%d %H:%M:%S')
            )
            db.session.add(sighting)
        
        db.session.commit()
        print(f"Successfully seeded {len(plates_data)} license plate sightings with demo data.")

if __name__ == "__main__":
    seed_database()
