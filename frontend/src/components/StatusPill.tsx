import React from 'react';
import { Text, StyleSheet } from 'react-native';

interface Props {
  status: string;
}

const palette: Record<string, string> = {
  present: '#4CAF50',
  pending: '#F9A602',
  rejected: '#E53935',
};

export default function StatusPill({ status }: Props) {
  const lower = status.toLowerCase();
  const backgroundColor = palette[lower] ?? '#607D8B';

  return (
    <Text style={[styles.pill, { backgroundColor }]}>
      {status.toUpperCase()}
    </Text>
  );
}

const styles = StyleSheet.create({
  pill: {
    color: '#fff',
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
});
