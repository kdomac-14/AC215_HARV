import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import api, { AttendanceEvent } from '../../utils/api';
import StatusPill from '../../src/components/StatusPill';

export default function ClassDetailsScreen() {
  const { courseId, className } = useLocalSearchParams<{ courseId: string; className: string }>();
  const [attendance, setAttendance] = useState<AttendanceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<'present' | 'absent'>('present');

  const loadAttendance = async () => {
    setLoading(true);
    try {
      const records = await api.listAttendance(Number(courseId));
      setAttendance(records);
    } catch (error) {
      console.error('[professor] failed to load attendance', error);
      Alert.alert('Unable to fetch records', 'Is the backend API running at http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttendance();
  }, [courseId]);

  const handleOverride = async (eventId: number) => {
    try {
      const updated = await api.overrideAttendance(eventId, {
        status: selectedStatus,
        notes: selectedStatus === 'present' ? 'Instructor override: verified' : 'Marked absent manually',
      });
      setAttendance((prev) => prev.map((event) => (event.id === updated.id ? updated : event)));
      Alert.alert('Override saved', `Event marked as ${selectedStatus.toUpperCase()}`);
    } catch (error) {
      console.error('[professor] override failed', error);
      Alert.alert('Override failed', 'Double-check that the backend is running and try again.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{className}</Text>
      <Text style={styles.subtitle}>Course ID: {courseId}</Text>

      <View style={styles.overrideControls}>
        <Text style={styles.sectionLabel}>Override selection</Text>
        <View style={styles.toggleRow}>
          {(['present', 'absent'] as const).map((option) => (
            <TouchableOpacity
              key={option}
              style={[
                styles.toggleButton,
                selectedStatus === option && styles.toggleButtonActive,
              ]}
              onPress={() => setSelectedStatus(option)}
            >
              <Text
                style={[
                  styles.toggleText,
                  selectedStatus === option && styles.toggleTextActive,
                ]}
              >
                {option.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.helperText}>
          Select the status to apply, then tap a record below to send the override API call.
        </Text>
      </View>

      {loading ? (
        <ActivityIndicator color="#A51C30" />
      ) : attendance.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No attendance records yet</Text>
          <Text style={styles.helperText}>
            Ask a student to run the GPS check-in flow from the mobile tab to populate this list.
          </Text>
        </View>
      ) : (
        attendance.map((event) => (
          <TouchableOpacity key={event.id} style={styles.eventCard} onPress={() => handleOverride(event.id)}>
            <View style={styles.eventHeader}>
              <Text style={styles.eventStudent}>{event.student_id}</Text>
              <StatusPill status={event.status} />
            </View>
            <Text style={styles.eventMeta}>
              {new Date(event.timestamp).toLocaleString()} • {event.verification_method}
            </Text>
            {event.notes && <Text style={styles.eventNotes}>{event.notes}</Text>}
            {typeof event.confidence === 'number' && (
              <Text style={styles.eventMeta}>Confidence: {(event.confidence * 100).toFixed(1)}%</Text>
            )}
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    gap: 16,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#555',
  },
  overrideControls: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  sectionLabel: {
    fontWeight: '600',
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  toggleButton: {
    flex: 1,
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    alignItems: 'center',
  },
  toggleButtonActive: {
    backgroundColor: '#A51C30',
    borderColor: '#A51C30',
  },
  toggleText: {
    fontWeight: '600',
    color: '#333',
  },
  toggleTextActive: {
    color: '#fff',
  },
  helperText: {
    color: '#666',
  },
  emptyCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
  },
  eventCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    gap: 6,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventStudent: {
    fontWeight: '700',
  },
  eventMeta: {
    color: '#666',
    fontSize: 13,
  },
  eventNotes: {
    color: '#333',
  },
});
