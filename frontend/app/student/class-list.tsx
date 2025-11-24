import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import api, { CourseSummary } from '../../utils/api';
import { DEFAULT_INSTRUCTORS } from '../../utils/constants';

export default function ClassListScreen() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const responses = await Promise.all(
          DEFAULT_INSTRUCTORS.map((id) => api.listCourses(id).catch(() => [])),
        );
        setCourses(responses.flat());
      } catch (error) {
        console.error('[class-list] failed to load courses', error);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Campus Courses</Text>
      <Text style={styles.subtitle}>
        Reference list shared by the backend. Use the student dashboard to check in.
      </Text>
      {loading ? (
        <ActivityIndicator color="#A51C30" />
      ) : (
        courses.map((course) => (
          <View key={course.id} style={styles.courseCard}>
            <Text style={styles.courseName}>{course.name}</Text>
            <Text style={styles.courseCode}>Code: {course.code}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    gap: 12,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#666',
  },
  courseCard: {
    padding: 16,
    borderRadius: 10,
    backgroundColor: '#f5f5f5',
  },
  courseName: {
    fontWeight: '600',
    fontSize: 16,
  },
  courseCode: {
    color: '#555',
  },
});
