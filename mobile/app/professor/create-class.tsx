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
import api, { ClassroomTemplate } from '../../utils/api';

export default function CreateClassScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [className, setClassName] = useState('');
  const [classCode, setClassCode] = useState('');
  const [epsilon, setEpsilon] = useState('60');
  const [secretWord, setSecretWord] = useState('');
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [classrooms, setClassrooms] = useState<ClassroomTemplate[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [selectedClassroomId, setSelectedClassroomId] = useState<string | null>(null);

  useEffect(() => {
    generateClassCode();
    generateSecretWord();
    getCurrentLocation();
    loadClassroomCatalog();
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

  const loadClassroomCatalog = async () => {
    try {
      setCatalogLoading(true);
      const data = await api.getClassroomCatalog();
      setClassrooms(data);
      if (data.length > 0) {
        setSelectedClassroomId(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load classrooms', error);
      Alert.alert('Error', 'Unable to load classroom catalog. Please try again.');
    } finally {
      setCatalogLoading(false);
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

    const selectedClassroom = classrooms.find((room) => room.id === selectedClassroomId);
    if (!selectedClassroom) {
      Alert.alert('Error', 'Please select a classroom template');
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
        classroom_id: selectedClassroom.id,
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
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
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
        <Text style={styles.sectionTitle}>Select Classroom</Text>
        <Text style={styles.helperText}>
          Choose from pre-trained classrooms. Each option includes high-quality reference photos.
        </Text>

        {catalogLoading ? (
          <View style={styles.catalogLoading}>
            <ActivityIndicator />
            <Text style={styles.helperText}>Loading classroom catalog…</Text>
          </View>
        ) : classrooms.length === 0 ? (
          <View style={styles.catalogLoading}>
            <Text style={styles.helperText}>No classroom templates available.</Text>
          </View>
        ) : (
          classrooms.map((room) => {
            const isSelected = selectedClassroomId === room.id;
            return (
              <TouchableOpacity
                key={room.id}
                style={[styles.classroomCard, isSelected && styles.classroomCardSelected]}
                onPress={() => setSelectedClassroomId(room.id)}
              >
                <View style={styles.classroomHeader}>
                  <View>
                    <Text style={styles.classroomName}>{room.name}</Text>
                    {room.building && (
                      <Text style={styles.classroomMeta}>📍 {room.building}</Text>
                    )}
                  </View>
                  {isSelected && <Text style={styles.classroomSelected}>Selected</Text>}
                </View>
                {room.preview_photo && (
                  <Image
                    source={{ uri: `data:image/png;base64,${room.preview_photo}` }}
                    style={styles.classroomPreview}
                  />
                )}
                {room.description && (
                  <Text style={styles.classroomDescription}>{room.description}</Text>
                )}
                <Text style={styles.classroomMeta}>📸 {room.photo_count} reference photos</Text>
              </TouchableOpacity>
            );
          })
        )}
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
  classroomCard: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 15,
    marginTop: 15,
    backgroundColor: '#fafafa',
  },
  classroomCardSelected: {
    borderColor: '#A51C30',
    backgroundColor: '#fff0f3',
  },
  classroomHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  classroomName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#222',
  },
  classroomMeta: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  classroomSelected: {
    fontSize: 12,
    color: '#A51C30',
    fontWeight: '700',
  },
  classroomPreview: {
    width: '100%',
    height: 150,
    borderRadius: 8,
    marginBottom: 10,
    marginTop: 10,
  },
  classroomDescription: {
    fontSize: 14,
    color: '#444',
    marginBottom: 6,
  },
  catalogLoading: {
    paddingVertical: 20,
    alignItems: 'center',
    gap: 8,
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
