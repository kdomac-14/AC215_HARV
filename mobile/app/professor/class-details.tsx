import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import axios from 'axios';
import api from '../../utils/api';

interface Student {
  id: string;
  name: string;
  email?: string;
  attendance_rate?: number;
  last_check_in?: string;
  total_classes?: number;
  attended_classes?: number;
}

export default function ClassDetailsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [classInfo, setClassInfo] = useState<any>(null);

  useEffect(() => {
    loadClassDetails();
    loadStudents();
  }, []);

  const loadClassDetails = async () => {
    try {
      // Load class information
      const classCode = params.classCode as string;
      const className = params.className as string;
      setClassInfo({ code: classCode, name: className });
    } catch (error) {
      console.error('Failed to load class details:', error);
    }
  };

  const loadStudents = async () => {
    try {
      setLoading(true);
      const classCode = params.classCode as string;
      
      // Call API to get enrolled students
      const response = await api.getStudentsByClass(classCode);
      setStudents(response);
    } catch (error) {
      console.error('Failed to load students:', error);
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        // Treat 404 as "no roster yet" rather than fatal.
        setStudents([]);
      } else {
        Alert.alert('Error', 'Failed to load student list');
      }
    } finally {
      setLoading(false);
    }
  };

  const navigateToStudentAttendance = (student: Student) => {
    router.push({
      pathname: '/professor/student-attendance',
      params: {
        studentId: student.id,
        studentName: student.name,
        classCode: params.classCode,
        className: params.className,
      },
    });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{classInfo?.name || 'Class Details'}</Text>
        <Text style={styles.subtitle}>Code: {classInfo?.code}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Enrolled Students</Text>
        
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#A51C30" />
            <Text style={styles.loadingText}>Loading students...</Text>
          </View>
        ) : students.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No students enrolled yet</Text>
            <Text style={styles.emptySubtext}>
              Students can enroll using the class code: {classInfo?.code}
            </Text>
          </View>
        ) : (
          <View style={styles.studentList}>
            {students.map((student) => (
              <TouchableOpacity
                key={student.id}
                style={styles.studentCard}
                onPress={() => navigateToStudentAttendance(student)}
              >
                <View style={styles.studentInfo}>
                  <Text style={styles.studentName}>{student.name || `Student ${student.id}`}</Text>
                  <Text style={styles.studentId}>ID: {student.id}</Text>
                  {student.email && (
                    <Text style={styles.studentEmail}>{student.email}</Text>
                  )}
                </View>
                
                <View style={styles.attendanceInfo}>
                  {student.attendance_rate !== undefined && (
                    <View style={styles.attendanceRate}>
                      <Text style={styles.rateLabel}>Attendance</Text>
                      <Text style={[
                        styles.rateValue,
                        student.attendance_rate >= 80 ? styles.goodRate :
                        student.attendance_rate >= 60 ? styles.warningRate : styles.poorRate
                      ]}>
                        {Math.round(student.attendance_rate)}%
                      </Text>
                    </View>
                  )}
                  {student.attended_classes !== undefined && student.total_classes !== undefined && (
                    <Text style={styles.classCount}>
                      {student.attended_classes}/{student.total_classes} classes
                    </Text>
                  )}
                  {student.last_check_in && (
                    <Text style={styles.lastCheckIn}>
                      Last: {new Date(student.last_check_in).toLocaleDateString()}
                    </Text>
                  )}
                </View>
                
                <View style={styles.chevronContainer}>
                  <Text style={styles.chevron}>›</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
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
    color: '#333',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#A51C30',
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 10,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  studentList: {
    gap: 12,
  },
  studentCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    flexDirection: 'row',
    alignItems: 'center',
  },
  studentInfo: {
    flex: 1,
  },
  studentName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  studentId: {
    fontSize: 14,
    color: '#666',
  },
  studentEmail: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  attendanceInfo: {
    marginRight: 10,
    alignItems: 'flex-end',
  },
  attendanceRate: {
    alignItems: 'center',
  },
  rateLabel: {
    fontSize: 10,
    color: '#999',
    marginBottom: 2,
  },
  rateValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  goodRate: {
    color: '#4CAF50',
  },
  warningRate: {
    color: '#FF9800',
  },
  poorRate: {
    color: '#F44336',
  },
  classCount: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  lastCheckIn: {
    fontSize: 11,
    color: '#999',
    marginTop: 2,
  },
  chevronContainer: {
    marginLeft: 10,
  },
  chevron: {
    fontSize: 24,
    color: '#999',
  },
});
