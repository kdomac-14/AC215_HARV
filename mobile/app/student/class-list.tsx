import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../../utils/api';

export default function ClassListScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState([]);
  const [studentId, setStudentId] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAvailableClasses();
  }, []);

  const loadAvailableClasses = async () => {
    try {
      const data = await api.getAvailableClasses();
      setClasses(data);
    } catch (error) {
      console.error('Failed to load classes:', error);
      Alert.alert(
        'Network Error',
        'Unable to contact the HARV backend. Ensure API_URL in mobile/.env points to a reachable server and that it is running.',
      );
    }
  };

  const handleEnroll = async (classCode: string, className: string) => {
    if (!studentId.trim()) {
      Alert.alert('Error', 'Please enter your student ID first');
      return;
    }

    try {
      setLoading(true);
      await api.enrollInClass(classCode, studentId);
      Alert.alert('Success', `You have enrolled in ${className}!`, [
        {
          text: 'OK',
          onPress: () => router.back(),
        },
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to enroll. You may already be enrolled in this class.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Available Classes</Text>
        
        <Text style={styles.label}>Student ID</Text>
        <TextInput
          style={styles.input}
          value={studentId}
          onChangeText={setStudentId}
          placeholder="Enter your student ID"
        />
      </View>

      <View style={styles.classList}>
        {classes.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No classes available</Text>
            <Text style={styles.emptySubtext}>
              Check back later for new classes
            </Text>
          </View>
        ) : (
          classes.map((cls: any) => (
            <View key={cls.id} style={styles.classCard}>
              <Text style={styles.className}>{cls.name}</Text>
              <Text style={styles.classCode}>Code: {cls.code}</Text>
              <Text style={styles.classInfo}>
                Professor: {cls.professor_name || 'Unknown'}
              </Text>
              
              <TouchableOpacity
                style={[styles.enrollButton, loading && styles.enrollButtonDisabled]}
                onPress={() => handleEnroll(cls.code, cls.name)}
                disabled={loading}
              >
                <Text style={styles.enrollButtonText}>Enroll</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  classList: {
    padding: 20,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 20,
    color: '#666',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  classCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  className: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  classCode: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  classInfo: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  enrollButton: {
    backgroundColor: '#0066CC',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  enrollButtonDisabled: {
    backgroundColor: '#ccc',
  },
  enrollButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
