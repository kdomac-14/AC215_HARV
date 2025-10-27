# Face Recognition Setup Guide

This guide explains how to set up real human face datasets and implement blurry face recognition for the HARV project.

## 🎯 Overview

The enhanced pipeline now supports:
- **Real Face Datasets**: Integration with Kaggle human faces dataset
- **Blurry Face Recognition**: Fine-tuning for faces at different distances
- **Advanced Augmentation**: Blur simulation and distance effects
- **Enhanced Evaluation**: Face-specific metrics and visualizations

## 📊 Dataset Integration

### 1. **Kaggle Dataset Setup**

The pipeline uses the [Human Faces dataset](https://www.kaggle.com/datasets/ashwingupta3012/human-faces) from Kaggle.

**Automatic Setup:**
```bash
# Enable real faces in params.yaml
# Set use_real_faces: true

# Run setup script
make setup-faces
```

**Manual Setup:**
```bash
# 1. Download dataset from Kaggle
# 2. Extract to data/raw/human_faces/
# 3. Run processing script
python scripts/setup_real_faces.py
```

### 2. **Data Processing Pipeline**

The system automatically:
- Detects faces in images using OpenCV Haar cascades
- Classifies faces into ProfA/Room1 categories
- Creates blur augmentations for distance simulation
- Organizes data into train/val/test splits

## 🔧 Configuration

### **params.yaml Updates**

```yaml
# Face-specific parameters
use_real_faces: true
face_detection: true
blur_augmentation: true
blur_strength: 0.3
distance_augmentation: true
distance_levels: [1.0, 1.5, 2.0]

# Enhanced training parameters
epochs: 10
batch_size: 32
lr: 0.001
freeze_ratio: 0.7
```

## 🚀 Usage

### **1. Setup Real Face Dataset**

```bash
# Enable real faces
# Edit params.yaml: use_real_faces: true

# Download and process dataset
make setup-faces
```

### **2. Train with Real Faces**

```bash
# Run full pipeline with real face data
make run
```

### **3. Fine-tune for Blurry Faces**

```bash
# Fine-tune model for blurry face recognition
make fine-tune-blurry
```

## 📈 Enhanced Features

### **1. Blur Augmentation**

The system creates multiple blur levels to simulate different distances:
- **Level 0.0**: Original sharp image
- **Level 0.5**: Slight blur (close distance)
- **Level 1.0**: Medium blur (medium distance)
- **Level 1.5**: Strong blur (far distance)
- **Level 2.0**: Heavy blur (very far distance)

### **2. Advanced Training**

- **Transfer Learning**: Uses ImageNet pretrained weights
- **Layer Freezing**: Configurable freeze ratio for fine-tuning
- **Data Augmentation**: Rotation, color jitter, affine transforms
- **Learning Rate Scheduling**: Cosine annealing for better convergence

### **3. Enhanced Evaluation**

- **Confusion Matrix**: Visual performance analysis
- **ROC AUC**: Binary classification metrics
- **Per-class Metrics**: Precision, recall, F1-score
- **Blur Performance**: Accuracy across different blur levels

## 📊 Results and Metrics

### **Training Metrics**
- Training/validation accuracy and loss
- Per-epoch performance tracking
- Best model checkpointing

### **Evaluation Metrics**
- Test accuracy across all samples
- Performance breakdown by class
- Blur level performance analysis
- Confusion matrix visualization

### **Fine-tuning Results**
- Blurry face recognition accuracy
- Performance across distance levels
- Model robustness analysis

## 🔍 File Structure

```
scripts/
├── setup_real_faces.py          # Dataset download and processing
├── fine_tune_blurry_faces.py    # Blurry face fine-tuning
└── download_kaggle_faces.py      # Kaggle dataset utilities

data/
├── raw/human_faces/             # Downloaded Kaggle dataset
├── processed/                   # Processed face images
│   ├── train/ProfA/            # Professor-like faces
│   ├── train/Room1/            # Student-like faces
│   ├── val/ProfA/              # Validation data
│   ├── val/Room1/
│   ├── test/ProfA/             # Test data
│   └── test/Room1/
└── interim/face_manifest.csv    # Dataset manifest

artifacts/
├── checkpoints/best.pt          # Best model checkpoint
├── checkpoints/blurry_faces_best.pt  # Blurry face model
├── metrics.json                # Training metrics
├── confusion_matrix.png        # Confusion matrix plot
└── blurry_performance.png      # Blur performance plot
```

## 🛠️ Troubleshooting

### **Common Issues**

1. **Kaggle API Not Found**
   ```bash
   pip install kaggle
   # Configure API key if needed
   ```

2. **Dataset Download Fails**
   - Check internet connection
   - Verify Kaggle API credentials
   - Use manual download method

3. **Face Detection Issues**
   - Ensure OpenCV is properly installed
   - Check image quality and format
   - Verify face cascade files

4. **Training Performance**
   - Adjust learning rate in params.yaml
   - Modify freeze_ratio for transfer learning
   - Increase epochs for better convergence

### **Performance Optimization**

1. **Memory Issues**
   - Reduce batch_size in params.yaml
   - Use smaller image sizes
   - Enable gradient checkpointing

2. **Training Speed**
   - Use GPU if available
   - Reduce number of blur augmentations
   - Optimize data loading

## 📚 Advanced Usage

### **Custom Blur Levels**

```python
# Modify blur levels in params.yaml
distance_levels: [0.5, 1.0, 1.5, 2.0, 2.5]
```

### **Model Architecture Changes**

```python
# Switch between models in params.yaml
model_name: "efficientnet_lite0"  # or mobilenet_v3_small
```

### **Custom Face Classification**

Modify `classify_face_simple()` in `setup_real_faces.py` to implement custom classification logic.

## 🎯 Expected Results

### **Baseline Performance**
- **Clean Images**: 85-95% accuracy
- **Slight Blur**: 80-90% accuracy
- **Medium Blur**: 70-85% accuracy
- **Heavy Blur**: 60-75% accuracy

### **Fine-tuned Performance**
- **Blurry Faces**: 5-10% improvement
- **Distance Robustness**: Better performance at far distances
- **Generalization**: Improved performance on unseen blur levels

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `artifacts/` directory
3. Verify configuration in `params.yaml`
4. Test with synthetic data first

## 🎉 Success Indicators

✅ **Dataset Setup**: Face images processed and organized
✅ **Training**: Model converges with good accuracy
✅ **Evaluation**: Confusion matrix and metrics generated
✅ **Fine-tuning**: Blurry face performance improved
✅ **Visualization**: Performance plots created

The system is now ready for production face recognition with robust blur handling!
