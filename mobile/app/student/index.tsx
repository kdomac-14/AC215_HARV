import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, RefreshControl, Alert } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import api from '../../utils/api';
import { useStore } from '../../utils/store';

export default function StudentScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const studentIdStored = useStore((state) => state.user?.id);
  const setUser = useStore((state) => state.setUser);
  const [studentIdInput, setStudentIdInput] = useState(studentIdStored || '');
  const [activeStudentId, setActiveStudentId] = useState(studentIdStored || '');
  const [hasStudentId, setHasStudentId] = useState(Boolean(studentIdStored));

  useEffect(() => {
    if (studentIdStored) {
      setActiveStudentId(studentIdStored);
      setStudentIdInput(studentIdStored);
      setHasStudentId(true);
    }
  }, [studentIdStored]);

  const loadClasses = async (id?: string) => {
    const currentId = id || activeStudentId;
    if (!currentId) {
      return;
    }

    setRefreshing(true);
    try {
      const data = await api.getStudentClasses(currentId);
      setClasses(data || []);
    } catch (error) {
      console.error('Failed to load classes:', error);
      try {
        const allClasses = await api.getAvailableClasses();
        setClasses(allClasses || []);
      } catch (err) {
        console.error('Failed to load available classes:', err);
      }
    } finally {
      setRefreshing(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      if (hasStudentId && activeStudentId) {
        loadClasses(activeStudentId);
      }
    }, [hasStudentId, activeStudentId])
  );

  const confirmStudentId = () => {
    const trimmed = studentIdInput.trim();
    if (!trimmed) {
      Alert.alert('Student ID Required', 'Please enter your student ID to continue.');
      return;
    }

    setActiveStudentId(trimmed);
    setHasStudentId(true);
    setUser({ id: trimmed, name: trimmed, role: 'student' });
    loadClasses(trimmed);
  };

  const handleChangeStudent = () => {
    setHasStudentId(false);
    setActiveStudentId('');
    setClasses([]);
    setRefreshing(false);
    setUser(null);
  };

  const handleTakeAttendance = (cls: any) => {
    router.push({
      pathname: '/student/check-in',
      params: {
        classCode: cls.code,
        className: cls.name,
        studentId: activeStudentId,
      },
    });
  };

  const confirmUnenroll = (classCode: string, className: string) => {
    if (!activeStudentId) {
      return;
    }

    Alert.alert(
      'Unenroll from Class',
      `Are you sure you want to leave ${className}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unenroll',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await api.unenrollFromClass(classCode, activeStudentId);
              if (!response?.ok) {
                throw new Error(response?.reason || 'Unable to unenroll');
              }
              loadClasses();
            } catch (error) {
              console.error('Failed to unenroll:', error);
              Alert.alert('Error', 'Failed to unenroll from class. Please try again.');
            }
          },
        },
      ],
    );
  };

  if (!hasStudentId) {
    return (
      <View style={styles.identifyContainer}>
        <Text style={styles.identifyTitle}>Enter Your Student ID</Text>
        <Text style={styles.identifySubtitle}>
          We use your ID to load the classes you are enrolled in and to record your attendance.
        </Text>
        <TextInput
          style={styles.identifyInput}
          value={studentIdInput}
          onChangeText={setStudentIdInput}
          placeholder="e.g. student_001"
          autoCapitalize="none"
          autoCorrect={false}
        />
        <TouchableOpacity style={styles.continueButton} onPress={confirmStudentId}>
          <Text style={styles.continueButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadClasses()} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>My Classes</Text>
        <Text style={styles.subtitle}>Signed in as {activeStudentId}</Text>
        <TouchableOpacity onPress={handleChangeStudent}>
          <Text style={styles.changeIdText}>Switch Student ID</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.browseButton} onPress={() => router.push('/student/class-list')}>
          <Text style={styles.browseButtonText}>+ Browse & Enroll in Classes</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.classList}>
        {classes.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No classes enrolled</Text>
            <Text style={styles.emptySubtext}>
              Use the button above to browse available classes and enroll.
            </Text>
          </View>
        ) : (
          classes.map((cls: any) => (
            <View key={cls.id || cls.code} style={styles.classCard}>
              <Text style={styles.className}>{cls.name}</Text>
              <Text style={styles.classCode}>Code: {cls.code}</Text>

              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={[styles.actionButton, styles.attendanceButton]}
                  onPress={() => handleTakeAttendance(cls)}
                >
                  <Text style={styles.actionButtonText}>Take Attendance</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.actionButton, styles.unenrollButton]}
                  onPress={() => confirmUnenroll(cls.code, cls.name)}
                >
                  <Text style={styles.unenrollButtonText}>Unenroll</Text>
                </TouchableOpacity>
              </View>
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  changeIdText: {
    color: '#0066CC',
    fontWeight: '600',
    marginBottom: 15,
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
    marginBottom: 6,
  },
  classCode: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  attendanceButton: {
    backgroundColor: '#4CAF50',
  },
  unenrollButton: {
    backgroundColor: '#F2F2F2',
    borderWidth: 1,
    borderColor: '#E57373',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  unenrollButtonText: {
    color: '#C62828',
    fontSize: 15,
    fontWeight: '600',
  },
  identifyContainer: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 30,
    justifyContent: 'center',
  },
  identifyTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    textAlign: 'center',
  },
  identifySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 22,
  },
  identifyInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    marginBottom: 20,
  },
  continueButton: {
    backgroundColor: '#0066CC',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  continueButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
