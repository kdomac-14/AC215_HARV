import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import axios from 'axios';
import api, { ClassroomTemplate } from '../../utils/api';
import FALLBACK_CLASSROOMS from '../../data/classroomCatalog';
import { PROFESSOR_ID, PROFESSOR_NAME } from '../../utils/constants';

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
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);

  const selectedClassroom = selectedClassroomId
    ? classrooms.find((room) => room.id === selectedClassroomId) ?? null
    : null;

  useEffect(() => {
    generateClassCode();
    generateSecretWord();
    getCurrentLocation();
    applyCatalog(FALLBACK_CLASSROOMS);
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

  const applyCatalog = (catalog: ClassroomTemplate[]) => {
    setClassrooms(catalog);
    if (catalog.length === 0) {
      setSelectedClassroomId(null);
      return;
    }

    setSelectedClassroomId((prev) => {
      if (prev && catalog.some((room) => room.id === prev)) {
        return prev;
      }
      return catalog[0].id;
    });
    setIsCatalogOpen(false);
  };

  const loadClassroomCatalog = async () => {
    try {
      setCatalogLoading(true);
      const data = await api.getClassroomCatalog();
      applyCatalog(data);
    } catch (error) {
      console.warn('[create-class] Failed to load classrooms', {
        error:
          axios.isAxiosError(error) && error.response
            ? {
                status: error.response.status,
                url: error.config?.url,
                data: error.response.data,
              }
            : String(error),
      });
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
        professor_id: PROFESSOR_ID,
        professor_name: PROFESSOR_NAME,
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
          Choose the lecture hall template that matches your class.
        </Text>

        <View style={styles.dropdownContainer}>
          <TouchableOpacity
            style={styles.dropdownTrigger}
            onPress={() => {
              if (classrooms.length > 0) {
                setIsCatalogOpen((prev) => !prev);
              }
            }}
            disabled={classrooms.length === 0}
          >
            <View style={{ flex: 1 }}>
              <Text style={styles.dropdownValue}>
                {selectedClassroom?.name || 'No templates available'}
              </Text>
              {selectedClassroom?.building && (
                <Text style={styles.dropdownMeta}>{selectedClassroom.building}</Text>
              )}
            </View>
            <Text style={styles.dropdownChevron}>{isCatalogOpen ? '▲' : '▼'}</Text>
          </TouchableOpacity>

          {isCatalogOpen && classrooms.length > 0 && (
            <ScrollView style={styles.dropdownList}>
              {classrooms.map((room) => (
                <TouchableOpacity
                  key={room.id}
                  style={[
                    styles.dropdownOption,
                    selectedClassroomId === room.id && styles.dropdownOptionSelected,
                  ]}
                  onPress={() => {
                    setSelectedClassroomId(room.id);
                    setIsCatalogOpen(false);
                  }}
                >
                  <Text style={styles.dropdownOptionName}>{room.name}</Text>
                  <Text style={styles.dropdownOptionMeta}>
                    {room.building || 'Unknown building'} • {room.photo_count} ref photos
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}
        </View>

        {catalogLoading && (
          <View style={styles.catalogLoading}>
            <ActivityIndicator />
            <Text style={styles.helperText}>Refreshing catalog…</Text>
          </View>
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
  dropdownContainer: {
    marginTop: 12,
  },
  dropdownTrigger: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  dropdownValue: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111',
  },
  dropdownMeta: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  dropdownChevron: {
    fontSize: 18,
    color: '#6b7280',
    marginLeft: 12,
  },
  dropdownList: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    backgroundColor: '#fff',
    maxHeight: 240,
  },
  dropdownOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  dropdownOptionSelected: {
    backgroundColor: '#eff6ff',
  },
  dropdownOptionName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111',
  },
  dropdownOptionMeta: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
  },
  catalogLoading: {
    marginTop: 12,
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#eef2ff',
    flexDirection: 'row',
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
