# License Plate Tracker

A web application to track license plate sightings, car descriptions, and locations.

## Features

- Add new license plate sightings with vehicle details
- **Attach images to sightings** (optional, with preview)
- **Bulk image upload** for restoring multiple photos at once
- Edit existing sightings by clicking on the plate number
- Replace or remove images from existing sightings
- Search for license plates
- View and sort recent sightings with image thumbnails
- Export data in CSV or Python seed format (with optional notes exclusion)
- Responsive design that works on desktop and mobile
- Secure data storage with SQLite or PostgreSQL
- Protected image storage with authentication

## Setup

1. **Prerequisites**
   - Python 3.8+
   - pip (Python package installer)

2. **Install Dependencies**
   
   On macOS/Linux, use `pip3`:
   ```bash
   pip3 install -r requirements.txt
   ```
   
   Or on Windows:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables (Optional)**
   
   For local development, you can optionally create a `.env` file to customize settings. A template is provided:
   
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` to set your preferred values. If you don't create a `.env` file, the application will use sensible defaults (SQLite database, auto-generated secret key).

4. **Seed the Database (Optional)**
   
   To populate your database with sample data for testing:
   
   ```bash
   python3 seed_data_demo.py
   ```
   
   This will add fictional license plate entries to your database for demonstration purposes.

5. **Run the Application**

   On macOS/Linux:
   ```bash
   python3 app.py
   ```
   
   Or on Windows:
   ```bash
   python app.py
   ```

6. **Access the Application**

   Open your web browser and go to: `http://127.0.0.1:5001/`

## Image Attachments

The application supports attaching images to license plate sightings:

- **Supported formats**: PNG, JPG, JPEG, GIF, WEBP
- **Maximum file size**: 5MB per image
- **Storage location**: Images are stored in `instance/uploads/` (automatically created)
- **Filename format**: Images are saved as `sighting_{id}_{original_filename}` to preserve original names
- **Security**: Images are served through a protected route and respect BasicAuth settings
- **Features**:
  - Live preview before uploading
  - Click images to view full size in new tab
  - Replace or remove images when editing sightings
  - Automatic cleanup when sightings are deleted
  - **Bulk upload** for restoring multiple images at once (see footer link)

## Configuration Files

- **`.env.example`**: Template for environment variables. Copy to `.env` and customize for your local setup.
- **`seed_data_demo.py`**: Script to populate the database with fictional sample data for testing and demonstration.

## Deployment to DigitalOcean

### DigitalOcean App Platform (Recommended)

The easiest way to deploy this application is using DigitalOcean's App Platform with a managed PostgreSQL database.

#### Steps:

1. **Create a PostgreSQL Database**:
   - In DigitalOcean, go to **Databases** → **Create Database**
   - Choose **PostgreSQL** (latest version)
   - Select your preferred plan and region
   - Note the connection details after creation

2. **Deploy the App**:
   - Go to **Apps** → **Create App**
   - Connect your GitHub repository or upload your code
   - DigitalOcean will auto-detect the buildpacks (Python, Procfile)

3. **Configure Build Settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: Leave blank (uses Procfile automatically)

4. **Add Environment Variables**:

   Go to your App's **Settings** → **App-Level Environment Variables** and add the following:

   - **`FLASK_ENV`**: Set this to `production`.
   - **`BASIC_AUTH_USERNAME`**: The username you want for password protection.
   - **`BASIC_AUTH_PASSWORD`**: The password you want for password protection.

5. **Attach Database** (Alternative to manual DATABASE_URL):
   - In App settings, go to **Components** → **Create Component** → **Database**
   - Select your PostgreSQL database
   - This automatically sets the `DATABASE_URL` environment variable

6. **Deploy**:
   - Click **Deploy** and wait for the build to complete
   - Your app will be available at the provided URL

#### Running Database Migrations in Production

When you make changes to your database models (e.g., adding a new column), you must run a migration to apply these changes to your production database. 

1. **Generate a Migration Script Locally**:
   ```bash
   # Make sure your local database is up-to-date
   python3 -m flask db upgrade

   # Generate the new migration script
   python3 -m flask db migrate -m "A descriptive message for your migration"
   ```

2. **Commit and Deploy**:
   - Commit the new migration script (located in `migrations/versions/`) to your git repository.
   - Push the changes to trigger a new deployment on DigitalOcean.

3. **Run the Migration in Production**:
   - In your DigitalOcean App, go to the **Console** tab.
   - Run the following command to apply the migration:
     ```bash
     python3 -m flask db upgrade
     ```

#### Image Storage in Production

The application stores uploaded images in the `instance/uploads/` directory:

- **Persistence**: On DigitalOcean App Platform, this directory is ephemeral and will be cleared on redeploys
- **Temporary Workaround**: For testing, the directory will automatically recreate on app start, but uploaded images will be lost on each deployment
- **Impact**: After each deployment, image files are deleted but database records (including filenames) remain intact
- **Result**: Sightings will show camera badges but images won't load until manually restored

**Recommended Recovery Workflow:**

The easiest way to restore images after deployment is using the **Bulk Upload** feature:

1. **Keep Your Original Photos**: Save your original camera roll images (e.g., `IMG_1234.jpg`, `photo.jpg`)

2. **After Deployment - Bulk Restore:**
   - Log into your production app
   - Click **"📸 Bulk Upload"** in the footer
   - Select all your original photos from your device
   - Upload them all at once
   - The system automatically matches photos to sightings by filename

**Alternative Methods:**

- **Export/Import Workflow:**
  1. Before deployment: Export via **ZIP (CSV + Photos)**
  2. After deployment: Use bulk upload to restore from the extracted `images/` folder
  3. Works with both original filenames and full database filenames

- **Manual Re-upload:**
  1. Edit each sighting individually
  2. Re-upload images one at a time
  3. Slower, but useful for selective updates

**Long-term Solution:**

For automatic persistence, consider implementing object storage (DigitalOcean Spaces, AWS S3).

## Security Notes

- The application uses environment variables for sensitive configuration
- PostgreSQL database recommended for production (automatically configured via `DATABASE_URL`)
- SQLite is used for local development only
- **Image Security**:
  - Images are stored in `instance/uploads/`, NOT in the public `static/` folder
  - Images are served through a protected `/image/<filename>` route
  - BasicAuth protection applies to all image access in production
  - Filenames are sanitized with `secure_filename()` to prevent path traversal attacks
  - Original filenames are preserved (format: `sighting_{id}_{original_name}`)
  - Server-side validation of file types and sizes
- `seed_data.py` is excluded from version control to protect real license plate data
  - Use `seed_data_demo.py` for demonstration purposes
  - Create your own `seed_data.py` locally if you want to populate personal data
- For production use, consider:
  - Setting up proper user authentication
  - Enabling HTTPS (automatic with DigitalOcean App Platform)
  - Regular database backups
  - Rate limiting for API endpoints
  - Privacy implications of tracking license plates in your jurisdiction
  - **Note**: The `instance/uploads/` directory should be backed up separately or included in your database backup strategy

## Contributing

**This is a read-only mirror** published from a private repository. The public repository is automatically updated whenever changes are pushed to the private repo.

### How to Contribute

While this is a read-only mirror, contributions are welcome! Here's how:

1. **Fork this repository** to your GitHub account
2. **Create a feature branch** in your fork (`git checkout -b feature/your-feature`)
3. **Make your changes** and commit them
4. **Push to your fork** and create a pull request
5. **Wait for review** - Your PR will be reviewed and manually merged into the private repo
6. **Changes will be published** - Once merged privately, they'll appear in the next public snapshot

### Important Notes

- Pull requests are **manually reviewed and backported** to the private repository
- Changes are published as **single-commit snapshots** (commit history is not preserved)
- For questions, bug reports, or feature requests, please **open an issue**
