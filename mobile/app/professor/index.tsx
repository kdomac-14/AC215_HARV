import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, RefreshControl } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import api from '../../utils/api';
import { PROFESSOR_ID } from '../../utils/constants';

export default function ProfessorScreen() {
  const router = useRouter();
  const [classes, setClasses] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const professorId = PROFESSOR_ID;

  const loadClasses = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await api.getClassesByProfessor(professorId);
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
        <TouchableOpacity
          style={styles.createButton}
          onPress={() => router.push('/professor/create-class')}
        >
          <Text style={styles.createButtonText}>+ Create New Class</Text>
        </TouchableOpacity>
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
          classes.map((cls: any) => (
            <TouchableOpacity
              key={cls.id}
              style={styles.classCard}
              onPress={() => {
                // Navigate to class details
                Alert.alert('Class Details', `View details for ${cls.name}`);
              }}
            >
              <Text style={styles.className}>{cls.name}</Text>
              <Text style={styles.classCode}>Code: {cls.code}</Text>
              <View style={styles.classInfo}>
                <Text style={styles.infoText}>
                  📍 Location: {cls.lat.toFixed(4)}, {cls.lon.toFixed(4)}
                </Text>
                {cls.classroom_label && (
                  <Text style={styles.infoText}>🏫 Classroom: {cls.classroom_label}</Text>
                )}
                <Text style={styles.infoText}>
                  📏 Radius: {cls.epsilon_m}m
                </Text>
                <Text style={styles.infoText}>
                  📸 Photos: {cls.room_photos?.length || 0}
                </Text>
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
  createButton: {
    backgroundColor: '#A51C30',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  createButtonText: {
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
  classInfo: {
    gap: 6,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
  },
});
