import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import api from '../../utils/api';

export default function CheckInScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { classCode, className, studentId } = params as {
    classCode: string;
    className: string;
    studentId: string;
  };

  const [permission, requestPermission] = useCameraPermissions();
  const [locationPermission, setLocationPermission] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkInResult, setCheckInResult] = useState<{
    success: boolean;
    message: string;
    details?: any;
  } | null>(null);
  const [showManualOverride, setShowManualOverride] = useState(false);
  const [secretWord, setSecretWord] = useState('');
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  
  const cameraRef = useRef<any>(null);

  useEffect(() => {
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    setLocationPermission(status === 'granted');
  };

  if (!permission) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#0066CC" />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionTitle}>Camera Permission Required</Text>
          <Text style={styles.permissionText}>
            HARV needs camera access to verify your attendance by taking a photo of the classroom.
          </Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const takePicture = async () => {
    if (!cameraRef.current) {
      Alert.alert('Error', 'Camera is not ready');
      return;
    }

    try {
      setLoading(true);

      // Take the photo
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
        base64: true,
      });

      setCapturedPhoto(photo.base64);

      // Get current location
      let lat, lon, accuracy;
      if (locationPermission) {
        const location = await Location.getCurrentPositionAsync({});
        lat = location.coords.latitude;
        lon = location.coords.longitude;
        accuracy = location.coords.accuracy;
      }

      // Send check-in request
      const result = await api.checkIn({
        class_code: classCode,
        student_id: studentId,
        image_b64: photo.base64,
        lat,
        lon,
        accuracy_m: accuracy,
      });

      setLoading(false);

      if (result.ok) {
        setCheckInResult({
          success: true,
          message: '✅ Check-in Successful!',
          details: result,
        });
      } else {
        setCheckInResult({
          success: false,
          message: '❌ Check-in Failed',
          details: result,
        });

        if (result.needs_manual_override || result.reason === 'location_failed' || result.reason === 'recognition_failed') {
          // Show manual override option
          setTimeout(() => {
            Alert.alert(
              'Check-in Failed',
              'Your check-in could not be verified automatically. Would you like to request manual override from your professor?',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Manual Override',
                  onPress: () => setShowManualOverride(true),
                },
              ],
            );
          }, 1500);
        }
      }
    } catch (error) {
      setLoading(false);
      Alert.alert('Error', 'Failed to process check-in. Please try again.');
    }
  };

  const handleManualOverride = async () => {
    if (!secretWord.trim()) {
      Alert.alert('Error', 'Please enter the secret word');
      return;
    }

    try {
      setLoading(true);
      const result = await api.manualOverride({
        class_code: classCode,
        student_id: studentId,
        secret_word: secretWord,
      });

      setLoading(false);
      setShowManualOverride(false);

      if (result.ok) {
        setCheckInResult({
          success: true,
          message: '✅ Manual Override Successful!',
          details: result,
        });
      } else {
        Alert.alert('Error', 'Invalid secret word. Please ask your professor.');
      }
    } catch (error) {
      setLoading(false);
      Alert.alert('Error', 'Failed to process manual override.');
    }
  };

  const handleDone = () => {
    router.back();
  };

  if (checkInResult) {
    return (
      <View style={styles.container}>
        <View style={[
          styles.resultContainer,
          checkInResult.success ? styles.successContainer : styles.failureContainer
        ]}>
          <Text style={styles.resultEmoji}>
            {checkInResult.success ? '✅' : '❌'}
          </Text>
          <Text style={styles.resultTitle}>{checkInResult.message}</Text>
          
          <View style={styles.detailsContainer}>
            <Text style={styles.detailsTitle}>Details:</Text>
            <Text style={styles.detailsText}>Class: {className}</Text>
            <Text style={styles.detailsText}>Code: {classCode}</Text>
            
            {checkInResult.details?.distance_m !== undefined && (
              <Text style={styles.detailsText}>
                Distance: {checkInResult.details.distance_m.toFixed(1)}m
              </Text>
            )}
            
            {checkInResult.details?.label && (
              <Text style={styles.detailsText}>
                Room Detected: {checkInResult.details.label}
              </Text>
            )}
            
            {checkInResult.details?.confidence && (
              <Text style={styles.detailsText}>
                Confidence: {(checkInResult.details.confidence * 100).toFixed(1)}%
              </Text>
            )}

            {!checkInResult.success && checkInResult.details?.reason && (
              <Text style={styles.failureReason}>
                Reason: {checkInResult.details.reason.replace(/_/g, ' ')}
              </Text>
            )}
          </View>

          <TouchableOpacity style={styles.doneButton} onPress={handleDone}>
            <Text style={styles.doneButtonText}>Done</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Check In to {className}</Text>
        <Text style={styles.headerSubtitle}>Point camera at the classroom</Text>
      </View>

      <View style={styles.cameraContainer}>
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing="back"
        />
        
        <View style={styles.cameraOverlay}>
          <View style={styles.guidanceBox}>
            <Text style={styles.guidanceText}>
              📸 Center the lecture screen or a distinctive feature of the room
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.captureButton, loading && styles.captureButtonDisabled]}
          onPress={takePicture}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="large" />
          ) : (
            <View style={styles.captureButtonInner} />
          )}
        </TouchableOpacity>

        <Text style={styles.controlsText}>
          Tap to capture and verify attendance
        </Text>
      </View>

      {/* Manual Override Modal */}
      <Modal
        visible={showManualOverride}
        transparent
        animationType="slide"
        onRequestClose={() => setShowManualOverride(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Manual Override</Text>
            <Text style={styles.modalText}>
              Enter the secret word provided by your professor
            </Text>

            <TextInput
              style={styles.modalInput}
              value={secretWord}
              onChangeText={setSecretWord}
              placeholder="Secret word"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonCancel]}
                onPress={() => setShowManualOverride(false)}
              >
                <Text style={styles.modalButtonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonSubmit]}
                onPress={handleManualOverride}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.modalButtonTextWhite}>Submit</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  permissionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 24,
  },
  permissionButton: {
    backgroundColor: '#0066CC',
    padding: 15,
    borderRadius: 10,
    paddingHorizontal: 30,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    padding: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#ccc',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'flex-end',
    padding: 20,
  },
  guidanceBox: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  guidanceText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
  },
  controls: {
    padding: 30,
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
    borderWidth: 5,
    borderColor: '#0066CC',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#0066CC',
  },
  controlsText: {
    color: '#fff',
    fontSize: 14,
  },
  resultContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
    backgroundColor: '#fff',
  },
  successContainer: {
    backgroundColor: '#E8F5E9',
  },
  failureContainer: {
    backgroundColor: '#FFEBEE',
  },
  resultEmoji: {
    fontSize: 80,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 30,
    textAlign: 'center',
  },
  detailsContainer: {
    width: '100%',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 30,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  detailsText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  failureReason: {
    fontSize: 16,
    color: '#D32F2F',
    marginTop: 10,
    fontWeight: '600',
  },
  doneButton: {
    backgroundColor: '#0066CC',
    padding: 18,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 25,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  modalText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    fontSize: 16,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  modalButton: {
    flex: 1,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalButtonCancel: {
    backgroundColor: '#f0f0f0',
  },
  modalButtonSubmit: {
    backgroundColor: '#0066CC',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  modalButtonTextWhite: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
