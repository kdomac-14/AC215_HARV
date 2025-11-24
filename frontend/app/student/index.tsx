import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  RefreshControl,
  Alert,
} from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import api, { CourseSummary } from '../../utils/api';
import { useStore } from '../../utils/store';
import { DEFAULT_INSTRUCTORS } from '../../utils/constants';

export default function StudentScreen() {
  const router = useRouter();
  const setUser = useStore((state) => state.setUser);
  const studentIdStored = useStore((state) => state.user?.id);
  const [studentId, setStudentId] = useState(studentIdStored || '');
  const [activeStudentId, setActiveStudentId] = useState(studentIdStored || '');
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const loadCourses = useCallback(async () => {
    if (!activeStudentId) {
      return;
    }

    setLoading(true);
    try {
      const responses = await Promise.all(
        DEFAULT_INSTRUCTORS.map((instructorId) =>
          api
            .listCourses(instructorId)
            .then((res) => res.map((course) => ({ ...course, instructor_id: instructorId })))
            .catch(() => []),
        ),
      );
      const flattened = responses.flat();
      setCourses(flattened);
    } catch (error) {
      console.error('[student] failed to load courses', error);
      Alert.alert(
        'Unable to load courses',
        'Check that the backend API is running locally and API_URL points to it.',
      );
    } finally {
      setLoading(false);
    }
  }, [activeStudentId]);

  useFocusEffect(
    useCallback(() => {
      if (activeStudentId) {
        loadCourses();
      }
    }, [activeStudentId, loadCourses]),
  );

  const handleConfirmId = () => {
    const trimmed = studentId.trim();
    if (!trimmed) {
      Alert.alert('Student ID required', 'Enter your HarvardKey or a demo ID before proceeding.');
      return;
    }
    setActiveStudentId(trimmed);
    setUser({ id: trimmed, name: trimmed, role: 'student' });
    loadCourses();
  };

  const handleReset = () => {
    setUser(null);
    setStudentId('');
    setActiveStudentId('');
    setCourses([]);
  };

  if (!activeStudentId) {
    return (
      <View style={styles.identifyContainer}>
        <Text style={styles.identifyTitle}>Identify Yourself</Text>
        <Text style={styles.identifySubtitle}>
          HARV links attendance records to your ID. Enter any string for demos.
        </Text>
        <TextInput
          style={styles.identifyInput}
          placeholder="e.g. student_001"
          autoCapitalize="none"
          value={studentId}
          onChangeText={setStudentId}
        />
        <TouchableOpacity style={styles.primaryButton} onPress={handleConfirmId}>
          <Text style={styles.primaryButtonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={loadCourses} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Welcome, {activeStudentId}</Text>
        <Text style={styles.subtitle}>
          Tap a course to start a GPS-based check-in. We'll fall back to vision if necessary.
        </Text>
        <TouchableOpacity onPress={handleReset}>
          <Text style={styles.changeIdText}>Switch Student ID</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.classList}>
        {courses.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No courses available</Text>
            <Text style={styles.emptySubtext}>
              Confirm the backend is running and seeded with demo courses.
            </Text>
          </View>
        ) : (
          courses.map((course) => (
            <View key={`${course.id}-${course.code}`} style={styles.classCard}>
              <Text style={styles.className}>{course.name}</Text>
              <Text style={styles.classCode}>Code: {course.code}</Text>

              <TouchableOpacity
                style={styles.primaryButton}
                onPress={() =>
                  router.push({
                    pathname: '/student/check-in',
                    params: {
                      courseId: String(course.id),
                      className: course.name,
                      instructorId: course['instructor_id'],
                      studentId: activeStudentId,
                    },
                  })
                }
              >
                <Text style={styles.primaryButtonText}>Start Check-in</Text>
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
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  subtitle: {
    color: '#555',
    lineHeight: 20,
  },
  changeIdText: {
    color: '#0066CC',
    marginTop: 12,
    fontWeight: '600',
  },
  classList: {
    padding: 20,
    gap: 16,
  },
  classCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    gap: 8,
  },
  className: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
  },
  classCode: {
    fontSize: 14,
    color: '#555',
  },
  emptyCard: {
    padding: 40,
    backgroundColor: '#fff',
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  emptySubtext: {
    color: '#777',
    marginTop: 8,
    textAlign: 'center',
  },
  identifyContainer: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
    backgroundColor: '#f7f7f7',
    gap: 16,
  },
  identifyTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111',
  },
  identifySubtitle: {
    fontSize: 15,
    color: '#555',
  },
  identifyInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 16,
    fontSize: 18,
    backgroundColor: '#fff',
  },
  primaryButton: {
    backgroundColor: '#0066CC',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
  },
});
