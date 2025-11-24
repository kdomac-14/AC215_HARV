import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  TextInput,
  ScrollView,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import api from '../../utils/api';
import { PRESET_LOCATIONS } from '../../config/locations';

export default function CheckInScreen() {
  const router = useRouter();
  const { studentId, courseId, className, instructorId } = useLocalSearchParams<{
    studentId: string;
    courseId: string;
    className: string;
    instructorId: string;
  }>();

  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [hasLocationPermission, setHasLocationPermission] = useState(false);
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [checking, setChecking] = useState(false);
  const [gpsResult, setGpsResult] = useState<any>(null);
  const [visionResult, setVisionResult] = useState<any>(null);
  const [requiresVision, setRequiresVision] = useState(false);
  const cameraRef = useRef<CameraView>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      setHasLocationPermission(status === 'granted');
      if (status === 'granted') {
        const { coords } = await Location.getCurrentPositionAsync({});
        setLatitude(coords.latitude.toFixed(6));
        setLongitude(coords.longitude.toFixed(6));
      } else {
        const scienceCenter = PRESET_LOCATIONS.find((loc) => loc.id === 'science_center');
        if (scienceCenter) {
          setLatitude(scienceCenter.latitude.toString());
          setLongitude(scienceCenter.longitude.toString());
        }
      }
    })();
  }, []);

  const runGpsCheck = async () => {
    if (!studentId || !courseId || !instructorId) {
      Alert.alert('Missing details', 'Return to the previous screen and select a course again.');
      return;
    }

    if (!latitude || !longitude) {
      Alert.alert('Location required', 'Enter latitude/longitude values to continue.');
      return;
    }

    setChecking(true);
    setRequiresVision(false);
    setVisionResult(null);
    try {
      const response = await api.gpsCheckIn({
        student_id: studentId,
        course_id: Number(courseId),
        instructor_id: instructorId,
        latitude: Number(latitude),
        longitude: Number(longitude),
        device_id: hasLocationPermission ? 'gps-device' : 'manual',
      });
      setGpsResult(response);
      setRequiresVision(response.requires_visual_verification);
      if (!response.requires_visual_verification) {
        Alert.alert('Success', response.message);
      } else {
        Alert.alert(
          'Visual verification required',
          'Please capture the classroom or professor to finalize check-in.',
        );
      }
    } catch (error) {
      console.error('[student] gps check failed', error);
      Alert.alert('Check-in failed', 'Unable to reach the HARV backend. Is it running on port 8000?');
    } finally {
      setChecking(false);
    }
  };

  const submitVisionVerification = async () => {
    if (!cameraPermission?.granted) {
      const permission = await requestCameraPermission();
      if (!permission.granted) {
        Alert.alert('Camera permission', 'Camera access is required for the fallback model.');
        return;
      }
    }

    if (!cameraRef.current) {
      Alert.alert('Camera not ready', 'Hold on a second and try again.');
      return;
    }

    setChecking(true);
    try {
      const capture = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.6 });
      if (!capture.base64) {
        throw new Error('Capture failed');
      }
      const response = await api.visionCheckIn({
        student_id: studentId,
        course_id: Number(courseId),
        instructor_id: instructorId,
        image_b64: capture.base64,
      });
      setVisionResult(response);
      setRequiresVision(response.requires_visual_verification);
      Alert.alert(
        response.status === 'present' ? 'Attendance confirmed' : 'Vision did not match',
        response.message,
      );
    } catch (error) {
      console.error('[student] vision check failed', error);
      Alert.alert('Vision check failed', 'Could not evaluate the capture. Try again or adjust lighting.');
    } finally {
      setChecking(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Check in to {className}</Text>
      <Text style={styles.subtitle}>Student: {studentId}</Text>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>1. GPS Verification</Text>
        <Text style={styles.helperText}>
          We try the bounding-box validation first. You can edit coordinates if needed for demos.
        </Text>
        <View style={styles.row}>
          <View style={styles.field}>
            <Text style={styles.label}>Latitude</Text>
            <TextInput
              style={styles.input}
              keyboardType="decimal-pad"
              value={latitude}
              onChangeText={setLatitude}
            />
          </View>
          <View style={styles.field}>
            <Text style={styles.label}>Longitude</Text>
            <TextInput
              style={styles.input}
              keyboardType="decimal-pad"
              value={longitude}
              onChangeText={setLongitude}
            />
          </View>
        </View>

        <TouchableOpacity style={styles.primaryButton} onPress={runGpsCheck} disabled={checking}>
          {checking ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Send GPS Check</Text>}
        </TouchableOpacity>

        {gpsResult && (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>Latest result</Text>
            <Text style={styles.resultStatus}>{gpsResult.status.toUpperCase()}</Text>
            <Text style={styles.resultMessage}>{gpsResult.message}</Text>
          </View>
        )}
      </View>

      {requiresVision && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>2. Visual Fallback</Text>
          <Text style={styles.helperText}>
            Use the Expo camera preview to capture your professor or the classroom markers.
          </Text>
          {cameraPermission?.granted ? (
            <CameraView style={styles.camera} ref={cameraRef} facing="back" />
          ) : (
            <TouchableOpacity style={styles.secondaryButton} onPress={requestCameraPermission}>
              <Text style={styles.secondaryButtonText}>Grant Camera Permission</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity
            style={[styles.primaryButton, { marginTop: 16 }]}
            onPress={submitVisionVerification}
            disabled={checking}
          >
            {checking ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Upload Vision Scan</Text>
            )}
          </TouchableOpacity>

          {visionResult && (
            <View style={styles.resultBox}>
              <Text style={styles.resultTitle}>Vision model</Text>
              <Text style={styles.resultStatus}>{visionResult.status.toUpperCase()}</Text>
              <Text style={styles.resultMessage}>{visionResult.message}</Text>
              {typeof visionResult.confidence === 'number' && (
                <Text style={styles.resultMessage}>
                  Confidence: {(visionResult.confidence * 100).toFixed(1)}%
                </Text>
              )}
            </View>
          )}
        </View>
      )}

      {(gpsResult || visionResult) && (
        <TouchableOpacity style={styles.secondaryButton} onPress={() => router.back()}>
          <Text style={styles.secondaryButtonText}>Return to courses</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    gap: 16,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111',
  },
  subtitle: {
    color: '#666',
    marginBottom: 10,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  helperText: {
    color: '#666',
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  field: {
    flex: 1,
  },
  label: {
    fontWeight: '600',
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    fontSize: 16,
  },
  primaryButton: {
    backgroundColor: '#0066CC',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 16,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  secondaryButton: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#0066CC',
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#0066CC',
    fontWeight: '600',
  },
  resultBox: {
    marginTop: 16,
    backgroundColor: '#f5f8ff',
    borderRadius: 10,
    padding: 14,
    gap: 4,
  },
  resultTitle: {
    fontWeight: '600',
    color: '#002766',
  },
  resultStatus: {
    fontWeight: '700',
    color: '#001a33',
  },
  resultMessage: {
    color: '#1a1a1a',
  },
  camera: {
    width: '100%',
    height: 240,
    borderRadius: 12,
    overflow: 'hidden',
  },
});
