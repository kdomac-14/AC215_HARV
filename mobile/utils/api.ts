import axios from 'axios';
import Constants from 'expo-constants';

const manifestExtra =
  Constants.expoConfig?.extra ??
  // @ts-expect-error manifestExtra is only available at runtime
  Constants.manifestExtra ??
  {};
const envApiUrl =
  (typeof manifestExtra.apiUrl === 'string' && manifestExtra.apiUrl.length > 0
    ? manifestExtra.apiUrl
    : undefined) ||
  process.env.EXPO_PUBLIC_API_URL ||
  process.env.API_URL;
const API_URL = envApiUrl || 'http://localhost:8000';

if (!envApiUrl) {
  console.warn(
    '[api] Falling back to default API_URL (http://localhost:8000). Set API_URL in mobile/.env or EXPO_PUBLIC_API_URL.',
  );
}

export interface ClassProfile {
  id: string;
  name: string;
  code: string;
  lat: number;
  lon: number;
  epsilon_m: number;
  secret_word: string;
  room_photos: string[]; // base64 encoded images
  created_at: string;
}

export interface CheckInRequest {
  class_code: string;
  student_id: string;
  image_b64: string;
  lat?: number;
  lon?: number;
  accuracy_m?: number;
}

export interface CheckInResponse {
  ok: boolean;
  reason?: string;
  distance_m?: number;
  label?: string;
  confidence?: number;
  needs_manual_override?: boolean;
}

export interface ManualOverrideRequest {
  class_code: string;
  student_id: string;
  secret_word: string;
}

const api = {
  // Health check
  healthz: async () => {
    const response = await axios.get(`${API_URL}/healthz`);
    return response.data;
  },

  // Professor endpoints
  createClass: async (classData: Omit<ClassProfile, 'id' | 'created_at'>) => {
    const response = await axios.post(`${API_URL}/professor/classes`, classData);
    return response.data;
  },

  getClassesByProfessor: async (professorId: string) => {
    const response = await axios.get(`${API_URL}/professor/classes/${professorId}`);
    return response.data;
  },

  calibrateLocation: async (lat: number, lon: number, epsilon_m: number) => {
    const response = await axios.post(`${API_URL}/geo/calibrate`, {
      lat,
      lon,
      epsilon_m,
    });
    return response.data;
  },

  // Student endpoints
  getAvailableClasses: async () => {
    const response = await axios.get(`${API_URL}/student/classes`);
    return response.data;
  },

  enrollInClass: async (classCode: string, studentId: string) => {
    const response = await axios.post(`${API_URL}/student/enroll`, {
      class_code: classCode,
      student_id: studentId,
    });
    return response.data;
  },

  getStudentClasses: async (studentId: string) => {
    const response = await axios.get(`${API_URL}/student/classes/${studentId}`);
    return response.data;
  },

  checkIn: async (data: CheckInRequest): Promise<CheckInResponse> => {
    const response = await axios.post(`${API_URL}/student/checkin`, data);
    return response.data;
  },

  manualOverride: async (data: ManualOverrideRequest) => {
    const response = await axios.post(`${API_URL}/student/manual-override`, data);
    return response.data;
  },

  // Geolocation verification
  verifyLocation: async (lat?: number, lon?: number, accuracy_m?: number) => {
    const response = await axios.post(`${API_URL}/geo/verify`, {
      client_gps_lat: lat,
      client_gps_lon: lon,
      client_gps_accuracy_m: accuracy_m,
    });
    return response.data;
  },
};

export default api;
