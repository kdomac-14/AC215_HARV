import React from 'react';
import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: '#A51C30', // Harvard crimson
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            title: 'HARV',
            headerShown: true,
          }}
        />
        <Stack.Screen
          name="professor/index"
          options={{
            title: 'Professor Mode',
          }}
        />
        <Stack.Screen
          name="professor/create-class"
          options={{
            title: 'Create Class',
          }}
        />
        <Stack.Screen
          name="professor/class-details"
          options={{
            title: 'Attendance Events',
          }}
        />
        <Stack.Screen
          name="student/index"
          options={{
            title: 'Student Mode',
          }}
        />
        <Stack.Screen
          name="student/class-list"
          options={{
            title: 'My Classes',
          }}
        />
        <Stack.Screen
          name="student/check-in"
          options={{
            title: 'Check In',
          }}
        />
      </Stack>
    </SafeAreaProvider>
  );
}
