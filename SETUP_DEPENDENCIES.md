# Face Recognition Dependencies Setup

## 🚀 Quick Fix for OpenCV Error

The `make setup-faces` command failed because OpenCV isn't installed. Here are the solutions:

### **Option 1: Install Dependencies (Recommended)**

```bash
# Install required packages
pip install -r requirements-local.txt

# Then run the setup
make setup-faces
```

### **Option 2: Use Docker (No Local Dependencies)**

```bash
# Run the setup inside Docker container
docker compose run --rm ingestion python scripts/simple_face_setup.py
```

### **Option 3: Manual Dataset Setup**

If you prefer to avoid installing dependencies locally:

1. **Download the dataset manually:**
   - Go to: https://www.kaggle.com/datasets/ashwingupta3012/human-faces
   - Download the dataset
   - Extract to: `data/raw/human_faces/`

2. **Run the simplified setup:**
   ```bash
   python scripts/simple_face_setup.py
   ```

## 📦 Dependencies Explained

### **Required for Face Recognition:**
- **OpenCV**: Advanced face detection and image processing
- **PIL/Pillow**: Basic image processing fallback
- **NumPy**: Numerical operations
- **Pandas**: Data manipulation
- **scikit-learn**: Machine learning utilities

### **Optional:**
- **Kaggle API**: Automatic dataset download
- **Matplotlib/Seaborn**: Visualization and plotting

## 🔧 Installation Commands

### **Minimal Setup (Basic Image Processing)**
```bash
pip install numpy pandas pyyaml scikit-learn Pillow
```

### **Full Setup (Advanced Face Detection)**
```bash
pip install -r requirements-local.txt
```

### **Kaggle API Setup**
```bash
pip install kaggle
# Configure API key (optional)
# kaggle datasets download -d ashwingupta3012/human-faces
```

## 🐳 Docker Alternative

If you don't want to install dependencies locally, use Docker:

```bash
# Build and run the face setup in Docker
docker compose build ingestion
docker compose run --rm ingestion python scripts/simple_face_setup.py
```

## ✅ Verification

After installation, verify everything works:

```bash
# Test the setup
make setup-faces

# If successful, you should see:
# ✅ Face dataset setup completed!
# 📁 Processed data: data/processed/
# 🚀 Ready for training with real face data!
```

## 🆘 Troubleshooting

### **OpenCV Installation Issues**
```bash
# Try different OpenCV packages
pip install opencv-python-headless
# or
pip install opencv-python
```

### **Permission Issues**
```bash
# Use --user flag
pip install --user -r requirements-local.txt
```

### **Conda Environment**
```bash
# Create conda environment
conda create -n hlab python=3.11
conda activate hlab
pip install -r requirements-local.txt
```

## 🎯 Next Steps

Once dependencies are installed:

1. **Setup Face Dataset:**
   ```bash
   make setup-faces
   ```

2. **Train with Real Faces:**
   ```bash
   make run
   ```

3. **Fine-tune for Blurry Faces:**
   ```bash
   make fine-tune-blurry
   ```

The system will automatically fall back to synthetic data if real face data isn't available, ensuring the pipeline always works!
