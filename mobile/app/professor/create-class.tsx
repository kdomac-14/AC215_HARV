import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  Image,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import api from '../../utils/api';

type PhotoLocation = 'front_left' | 'front_right' | 'back_left' | 'back_right' | 'center';

interface RoomPhoto {
  location: PhotoLocation;
  label: string;
  uri: string | null;
  base64: string | null;
}

export default function CreateClassScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [className, setClassName] = useState('');
  const [classCode, setClassCode] = useState('');
  const [epsilon, setEpsilon] = useState('60');
  const [secretWord, setSecretWord] = useState('');
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [roomPhotos, setRoomPhotos] = useState<RoomPhoto[]>([
    { location: 'front_left', label: 'Front Left Corner', uri: null, base64: null },
    { location: 'front_right', label: 'Front Right Corner', uri: null, base64: null },
    { location: 'back_left', label: 'Back Left Corner', uri: null, base64: null },
    { location: 'back_right', label: 'Back Right Corner', uri: null, base64: null },
    { location: 'center', label: 'Center (Facing Screen)', uri: null, base64: null },
  ]);

  useEffect(() => {
    generateClassCode();
    generateSecretWord();
    getCurrentLocation();
  }, []);

  const generateClassCode = () => {
    const code = Math.random().toString(36).substring(2, 8).toUpperCase();
    setClassCode(code);
  };

  const generateSecretWord = () => {
    const words = ['crimson', 'veritas', 'harvard', 'scholar', 'wisdom', 'knowledge'];
    const randomWord = words[Math.floor(Math.random() * words.length)];
    const randomNum = Math.floor(Math.random() * 1000);
    setSecretWord(`${randomWord}${randomNum}`);
  };

  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required to create a class.');
        return;
      }

      setLoading(true);
      const loc = await Location.getCurrentPositionAsync({});
      setLocation({
        lat: loc.coords.latitude,
        lon: loc.coords.longitude,
      });
      setLoading(false);
    } catch (error) {
      setLoading(false);
      Alert.alert('Error', 'Failed to get current location');
    }
  };

  const takePhoto = async (index: number) => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Camera permission is required.');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.7,
        base64: true,
      });

      if (!result.canceled && result.assets[0]) {
        const newPhotos = [...roomPhotos];
        newPhotos[index] = {
          ...newPhotos[index],
          uri: result.assets[0].uri,
          base64: result.assets[0].base64 || null,
        };
        setRoomPhotos(newPhotos);
      }
    } catch (error) {
      console.error('Failed to take photo', error);
      const message = error instanceof Error ? error.message : undefined;
      Alert.alert('Error', message ? `Failed to take photo: ${message}` : 'Failed to take photo');
    }
  };

  const handleSubmit = async () => {
    if (!className.trim()) {
      Alert.alert('Error', 'Please enter a class name');
      return;
    }

    if (!location) {
      Alert.alert('Error', 'Location is required. Please enable location services.');
      return;
    }

    const missingPhotos = roomPhotos.filter((p) => !p.base64);
    if (missingPhotos.length > 0) {
      Alert.alert(
        'Missing Photos',
        `Please take photos from all 5 locations. Missing: ${missingPhotos
          .map((p) => p.label)
          .join(', ')}`,
      );
      return;
    }

    try {
      setLoading(true);

      const classData = {
        name: className,
        code: classCode,
        lat: location.lat,
        lon: location.lon,
        epsilon_m: parseFloat(epsilon),
        secret_word: secretWord,
        room_photos: roomPhotos.map((p) => p.base64!),
      };

      await api.createClass(classData);
      
      Alert.alert('Success', 'Class created successfully!', [
        {
          text: 'OK',
          onPress: () => router.back(),
        },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to create class. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Class Information</Text>
        
        <Text style={styles.label}>Class Name</Text>
        <TextInput
          style={styles.input}
          value={className}
          onChangeText={setClassName}
          placeholder="e.g., CS50 - Introduction to Computer Science"
        />

        <Text style={styles.label}>Class Code</Text>
        <View style={styles.codeContainer}>
          <TextInput
            style={[styles.input, styles.codeInput]}
            value={classCode}
            editable={false}
          />
          <TouchableOpacity style={styles.regenerateButton} onPress={generateClassCode}>
            <Text style={styles.regenerateText}>🔄</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>Secret Word (for manual override)</Text>
        <View style={styles.codeContainer}>
          <TextInput
            style={[styles.input, styles.codeInput]}
            value={secretWord}
            editable={false}
          />
          <TouchableOpacity style={styles.regenerateButton} onPress={generateSecretWord}>
            <Text style={styles.regenerateText}>🔄</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.helperText}>
          Keep this secret! Students will need this if automatic check-in fails.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Location Settings</Text>
        
        {location ? (
          <View style={styles.locationInfo}>
            <Text style={styles.locationText}>📍 Latitude: {location.lat.toFixed(6)}</Text>
            <Text style={styles.locationText}>📍 Longitude: {location.lon.toFixed(6)}</Text>
          </View>
        ) : (
          <TouchableOpacity style={styles.locationButton} onPress={getCurrentLocation}>
            <Text style={styles.locationButtonText}>
              {loading ? 'Getting Location...' : 'Get Current Location'}
            </Text>
          </TouchableOpacity>
        )}

        <Text style={styles.label}>Acceptable Distance (meters)</Text>
        <TextInput
          style={styles.input}
          value={epsilon}
          onChangeText={setEpsilon}
          keyboardType="numeric"
          placeholder="60"
        />
        <Text style={styles.helperText}>
          Students must be within this distance to check in
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Room Photos</Text>
        <Text style={styles.helperText}>
          Take photos from each corner and the center of the room for verification
        </Text>

        {roomPhotos.map((photo, index) => (
          <View key={photo.location} style={styles.photoItem}>
            <View style={styles.photoHeader}>
              <Text style={styles.photoLabel}>{photo.label}</Text>
              {photo.uri && <Text style={styles.photoCheck}>✓</Text>}
            </View>
            
            {photo.uri ? (
              <Image source={{ uri: photo.uri }} style={styles.photoPreview} />
            ) : (
              <View style={styles.photoPlaceholder}>
                <Text style={styles.photoPlaceholderText}>📷 No photo taken</Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.photoButton}
              onPress={() => takePhoto(index)}
            >
              <Text style={styles.photoButtonText}>
                {photo.uri ? 'Retake Photo' : 'Take Photo'}
              </Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      <TouchableOpacity
        style={[styles.submitButton, loading && styles.submitButtonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitButtonText}>Create Class</Text>
        )}
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  codeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  codeInput: {
    flex: 1,
    backgroundColor: '#f9f9f9',
  },
  regenerateButton: {
    padding: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  regenerateText: {
    fontSize: 20,
  },
  helperText: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
    fontStyle: 'italic',
  },
  locationInfo: {
    backgroundColor: '#f9f9f9',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  locationText: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
  },
  locationButton: {
    backgroundColor: '#0066CC',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  locationButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  photoItem: {
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    paddingBottom: 15,
  },
  photoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  photoLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  photoCheck: {
    fontSize: 20,
    color: '#4CAF50',
  },
  photoPreview: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    marginBottom: 10,
  },
  photoPlaceholder: {
    width: '100%',
    height: 200,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  photoPlaceholderText: {
    fontSize: 16,
    color: '#999',
  },
  photoButton: {
    backgroundColor: '#A51C30',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  photoButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#4CAF50',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    margin: 20,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
