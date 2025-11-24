import React from 'react';
import { View, Text, StyleSheet, Linking, TouchableOpacity } from 'react-native';

export default function CreateClassScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Managed via Config</Text>
      <Text style={styles.subtitle}>
        To keep the milestone lightweight, classes are seeded from backend config files. Edit
        `backend/app/config/settings.py` to add new courses, then restart the FastAPI server.
      </Text>
      <Text style={styles.subtitle}>
        The README explains how to reload the database and where to document new lecture halls.
      </Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => Linking.openURL('https://github.com/kdomac-14/AC215-HARV')}
      >
        <Text style={styles.buttonText}>Open project README</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    backgroundColor: '#fff',
    gap: 16,
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#555',
    lineHeight: 20,
  },
  button: {
    backgroundColor: '#A51C30',
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
});
