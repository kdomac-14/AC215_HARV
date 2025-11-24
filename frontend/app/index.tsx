import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      <View style={styles.header}>
        <Text style={styles.title}>HARV</Text>
        <Text style={styles.subtitle}>Harvard Attendance Recognition{'\n'}and Verification</Text>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.professorButton]}
          onPress={() => router.push('/professor')}
        >
          <Text style={styles.buttonText}>Professor Mode</Text>
          <Text style={styles.buttonSubtext}>Set up classes and manage attendance</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.studentButton]}
          onPress={() => router.push('/student')}
        >
          <Text style={styles.buttonText}>Student Mode</Text>
          <Text style={styles.buttonSubtext}>Check in to your classes</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Version 1.0.0</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#A51C30',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
  buttonContainer: {
    flex: 2,
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 20,
  },
  button: {
    padding: 30,
    borderRadius: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  professorButton: {
    backgroundColor: '#A51C30',
  },
  studentButton: {
    backgroundColor: '#0066CC',
  },
  buttonText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  buttonSubtext: {
    color: '#fff',
    fontSize: 14,
    opacity: 0.9,
    textAlign: 'center',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    color: '#999',
    fontSize: 12,
  },
});
