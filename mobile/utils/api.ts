import axios from 'axios';
import Constants from 'expo-constants';

const manifestExtra =
  Constants.expoConfig?.extra ??
  // @ts-ignore manifestExtra is only available at runtime
  Constants.manifestExtra ??
  {};

const normalizeBaseUrl = (url?: string) => {
  if (!url) {
    return undefined;
  }
  // Avoid double-slashes that FastAPI treats as a different route (404).
  return url.replace(/\/+$/, '');
};

const resolvedApiUrl =
  (typeof manifestExtra.apiUrl === 'string' && manifestExtra.apiUrl.length > 0
    ? manifestExtra.apiUrl
    : undefined) ||
  process.env.EXPO_PUBLIC_API_URL ||
  process.env.API_URL;

const API_URL = normalizeBaseUrl(resolvedApiUrl) || 'http://localhost:8000';

if (!resolvedApiUrl) {
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
  classroom_id?: string | null;
  classroom_label?: string | null;
  created_at: string;
}

export interface ClassroomTemplate {
  id: string;
  name: string;
  building?: string;
  description?: string;
  photo_count: number;
  preview_photo?: string | null;
}

export interface CreateClassRequest {
  name: string;
  code: string;
  lat: number;
  lon: number;
  epsilon_m: number;
  secret_word: string;
  classroom_id?: string;
  room_photos?: string[];
  professor_id?: string;
  professor_name?: string;
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
  createClass: async (classData: CreateClassRequest) => {
    const response = await axios.post(`${API_URL}/professor/classes`, classData);
    return response.data;
  },

  getClassroomCatalog: async (): Promise<ClassroomTemplate[]> => {
    const response = await axios.get(`${API_URL}/professor/classrooms`);
    return response.data.classrooms;
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
