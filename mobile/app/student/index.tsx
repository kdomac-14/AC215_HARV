import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../../utils/api';
import { useStore } from '../../utils/store';

export default function StudentScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState([]);
  const [studentId, setStudentId] = useState('');
  const studentIdStored = useStore((state) => state.user?.id);

  useEffect(() => {
    if (studentIdStored) {
      setStudentId(studentIdStored);
      loadClasses(studentIdStored);
    }
  }, [studentIdStored]);

  const loadClasses = async (id: string) => {
    try {
      const data = await api.getStudentClasses(id);
      setClasses(data);
    } catch (error) {
      console.error('Failed to load classes:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>My Classes</Text>
        
        {!studentIdStored && (
          <View style={styles.studentIdContainer}>
            <Text style={styles.label}>Student ID</Text>
            <TextInput
              style={styles.input}
              value={studentId}
              onChangeText={setStudentId}
              placeholder="Enter your student ID"
            />
          </View>
        )}

        <TouchableOpacity
          style={styles.browseButton}
          onPress={() => router.push('/student/class-list')}
        >
          <Text style={styles.browseButtonText}>+ Browse & Enroll in Classes</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.classList}>
        {classes.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No classes enrolled</Text>
            <Text style={styles.emptySubtext}>
              Browse available classes and enroll to start tracking attendance
            </Text>
          </View>
        ) : (
          classes.map((cls: any) => (
            <TouchableOpacity
              key={cls.id}
              style={styles.classCard}
              onPress={() => {
                router.push({
                  pathname: '/student/check-in',
                  params: {
                    classCode: cls.code,
                    className: cls.name,
                    studentId: studentId,
                  },
                });
              }}
            >
              <Text style={styles.className}>{cls.name}</Text>
              <Text style={styles.classCode}>Code: {cls.code}</Text>
              <View style={styles.checkInButton}>
                <Text style={styles.checkInButtonText}>📸 Check In</Text>
              </View>
            </TouchableOpacity>
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
  studentIdContainer: {
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
  browseButton: {
    backgroundColor: '#0066CC',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  browseButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
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
    paddingHorizontal: 20,
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
    marginBottom: 12,
  },
  checkInButton: {
    backgroundColor: '#4CAF50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  checkInButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
