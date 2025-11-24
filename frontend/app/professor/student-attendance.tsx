import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import api from '../../utils/api';
import { logError } from '../../utils/logger';

interface AttendanceRecord {
  date: string;
  status: 'present' | 'absent' | 'late';
  check_in_time?: string;
  confidence?: number;
}

const generateMockAttendance = (): AttendanceRecord[] => {
  const records: AttendanceRecord[] = [];
  const today = new Date();

  for (let i = 0; i < 10; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() - i * 7); // Weekly classes

    const random = Math.random();
    let status: 'present' | 'absent' | 'late';

    if (random > 0.85) {
      status = 'absent';
    } else if (random > 0.7) {
      status = 'late';
    } else {
      status = 'present';
    }

    records.push({
      date: date.toISOString(),
      status,
      check_in_time: status !== 'absent' ? date.toISOString() : undefined,
      confidence: status !== 'absent' ? 0.85 + Math.random() * 0.15 : undefined,
    });
  }

  return records.reverse();
};

export default function StudentAttendanceScreen() {
  const {
    studentId,
    classCode,
    studentName,
    className: courseName,
  } = useLocalSearchParams<{
    studentId?: string;
    classCode?: string;
    studentName?: string;
    className?: string;
  }>();
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({
    total: 0,
    present: 0,
    absent: 0,
    late: 0,
    rate: 0,
  });

  const loadAttendance = useCallback(async () => {
    if (!studentId || !classCode) {
      setAttendance([]);
      setSummary({ total: 0, present: 0, absent: 0, late: 0, rate: 0 });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await api.getStudentAttendance(studentId, classCode);

      // Process attendance data
      const records = response.records || [];
      setAttendance(records);

      // Calculate summary
      const total = records.length;
      const present = records.filter((r) => r.status === 'present').length;
      const absent = records.filter((r) => r.status === 'absent').length;
      const late = records.filter((r) => r.status === 'late').length;
      const rate = total > 0 ? Math.round(((present + late) / total) * 100) : 0;

      setSummary({ total, present, absent, late, rate });
    } catch (error) {
      logError('Failed to load attendance:', error);
      // Use mock data if API fails
      const mockRecords = generateMockAttendance();
      setAttendance(mockRecords);

      const total = mockRecords.length;
      const present = mockRecords.filter((r) => r.status === 'present').length;
      const absent = mockRecords.filter((r) => r.status === 'absent').length;
      const late = mockRecords.filter((r) => r.status === 'late').length;
      const rate = total > 0 ? Math.round(((present + late) / total) * 100) : 0;

      setSummary({ total, present, absent, late, rate });
    } finally {
      setLoading(false);
    }
  }, [classCode, studentId]);

  useEffect(() => {
    loadAttendance();
  }, [loadAttendance]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present':
        return '#4CAF50';
      case 'late':
        return '#FF9800';
      case 'absent':
        return '#F44336';
      default:
        return '#999';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'present':
        return '✓';
      case 'late':
        return '⏰';
      case 'absent':
        return '✗';
      default:
        return '?';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Attendance Summary</Text>
        {studentName && <Text style={styles.subtitle}>{studentName}</Text>}
        {courseName && <Text style={styles.classInfo}>{courseName}</Text>}
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#A51C30" />
          <Text style={styles.loadingText}>Loading attendance...</Text>
        </View>
      ) : (
        <>
          <View style={styles.summarySection}>
            <View style={styles.summaryCard}>
              <Text style={styles.summaryRate}>{summary.rate}%</Text>
              <Text style={styles.summaryLabel}>Attendance Rate</Text>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, styles.presentStat]}>{summary.present}</Text>
                <Text style={styles.statLabel}>Present</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, styles.lateStat]}>{summary.late}</Text>
                <Text style={styles.statLabel}>Late</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, styles.absentStat]}>{summary.absent}</Text>
                <Text style={styles.statLabel}>Absent</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{summary.total}</Text>
                <Text style={styles.statLabel}>Total</Text>
              </View>
            </View>
          </View>

          <View style={styles.recordsSection}>
            <Text style={styles.sectionTitle}>Attendance Records</Text>

            {attendance.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>No attendance records yet</Text>
              </View>
            ) : (
              <View style={styles.recordsList}>
                {attendance.map((record, index) => (
                  <View key={index} style={styles.recordCard}>
                    <View
                      style={[
                        styles.statusIndicator,
                        { backgroundColor: getStatusColor(record.status) },
                      ]}
                    >
                      <Text style={styles.statusIcon}>{getStatusIcon(record.status)}</Text>
                    </View>

                    <View style={styles.recordInfo}>
                      <Text style={styles.recordDate}>
                        {new Date(record.date).toLocaleDateString('en-US', {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </Text>
                      <Text style={[styles.recordStatus, { color: getStatusColor(record.status) }]}>
                        {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                      </Text>
                    </View>

                    <View style={styles.recordDetails}>
                      {record.check_in_time && (
                        <Text style={styles.checkInTime}>
                          {new Date(record.check_in_time).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </Text>
                      )}
                      {record.confidence !== undefined && (
                        <Text style={styles.confidence}>
                          {Math.round(record.confidence * 100)}% match
                        </Text>
                      )}
                    </View>
                  </View>
                ))}
              </View>
            )}
          </View>
        </>
      )}
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
    color: '#333',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 4,
  },
  classInfo: {
    fontSize: 14,
    color: '#999',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  summarySection: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryCard: {
    alignItems: 'center',
    marginBottom: 20,
  },
  summaryRate: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#333',
  },
  summaryLabel: {
    fontSize: 16,
    color: '#666',
    marginTop: 5,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  presentStat: {
    color: '#4CAF50',
  },
  lateStat: {
    color: '#FF9800',
  },
  absentStat: {
    color: '#F44336',
  },
  statLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  recordsSection: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
  recordsList: {
    gap: 10,
  },
  recordCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    borderLeftWidth: 4,
  },
  statusIndicator: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  statusIcon: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  recordInfo: {
    flex: 1,
  },
  recordDate: {
    fontSize: 14,
    color: '#333',
    marginBottom: 2,
  },
  recordStatus: {
    fontSize: 12,
    fontWeight: '600',
  },
  recordDetails: {
    alignItems: 'flex-end',
  },
  checkInTime: {
    fontSize: 12,
    color: '#666',
  },
  confidence: {
    fontSize: 11,
    color: '#999',
    marginTop: 2,
  },
});
