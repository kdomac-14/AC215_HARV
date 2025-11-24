import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, RefreshControl } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import api, { CourseSummary } from '../../utils/api';
import { PROFESSOR_ID } from '../../utils/constants';

export default function ProfessorScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState<CourseSummary[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const professorId = PROFESSOR_ID;

  const loadClasses = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await api.listCourses(professorId);
      setClasses(data);
    } catch (error) {
      console.error('Failed to load classes:', error);
      Alert.alert('Error', 'Failed to load classes. Please try again.');
    } finally {
      setRefreshing(false);
    }
  }, [professorId]);

  useFocusEffect(
    useCallback(() => {
      loadClasses();
    }, [loadClasses]),
  );

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadClasses} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>My Classes</Text>
        <Text style={styles.subtitle}>
          Courses are seeded from backend configs. Select one to review attendance events.
        </Text>
      </View>

      <View style={styles.classList}>
        {classes.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No classes yet</Text>
            <Text style={styles.emptySubtext}>
              Create your first class to start tracking attendance
            </Text>
          </View>
        ) : (
          classes.map((cls) => (
            <TouchableOpacity
              key={cls.id}
              style={styles.classCard}
              onPress={() => {
                router.push({
                  pathname: '/professor/class-details',
                  params: {
                    courseId: String(cls.id),
                    className: cls.name,
                  },
                });
              }}
            >
              <Text style={styles.className}>{cls.name}</Text>
              <Text style={styles.classCode}>Code: {cls.code}</Text>
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
  subtitle: {
    color: '#555',
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
    fontSize: 16,
    color: '#A51C30',
    marginBottom: 12,
    fontWeight: '600',
  },
});
