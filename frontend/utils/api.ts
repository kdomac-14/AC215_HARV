import axios from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const manifestExtra =
  Constants.expoConfig?.extra ??
  // @ts-ignore manifestExtra is only available at runtime
  Constants.manifestExtra ??
  {};

const normalizeBaseUrl = (url?: string) => {
  if (!url) {
    return undefined;
  }
  return url.replace(/\/+$/, '');
};

const getExpoHostUri = (): string | undefined => {
  return (
    (typeof Constants.expoConfig?.hostUri === 'string' && Constants.expoConfig.hostUri) ||
    // @ts-ignore hostUri is only surfaced at runtime depending on the Expo SDK
    (typeof Constants.manifest?.hostUri === 'string' && Constants.manifest.hostUri) ||
    undefined
  );
};

const deriveExpoNetworkUrl = (): string | undefined => {
  const hostUri = getExpoHostUri();
  if (!hostUri) {
    return Platform.OS === 'android' ? 'http://10.0.2.2:8000' : undefined;
  }

  const sanitized = hostUri.replace(/^(.*:\/\/)/, '');
  const [host] = sanitized.split(':');
  if (!host) {
    return undefined;
  }

  if (host === 'localhost' && Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  return `http://${host}:8000`;
};

const resolvedApiUrl =
  (typeof manifestExtra.apiUrl === 'string' && manifestExtra.apiUrl.length > 0
    ? manifestExtra.apiUrl
    : undefined) ||
  process.env.EXPO_PUBLIC_API_URL ||
  process.env.API_URL;

const derivedDevUrl = deriveExpoNetworkUrl();
const platformDefault = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
const API_URL = normalizeBaseUrl(resolvedApiUrl || derivedDevUrl || platformDefault) || platformDefault;

if (!resolvedApiUrl && !derivedDevUrl) {
  console.warn(
    `[api] Falling back to platform default API_URL (${platformDefault}). Set API_URL in frontend/.env or EXPO_PUBLIC_API_URL.`,
  );
}

export interface CourseSummary {
  id: number;
  code: string;
  name: string;
  instructor_id?: string;
}

export interface AttendanceEvent {
  id: number;
  student_id: string;
  course_id: number;
  instructor_id: string;
  timestamp: string;
  verification_method: string;
  status: string;
  confidence?: number | null;
  requires_manual_review: boolean;
  notes?: string | null;
}

export interface GPSCheckInPayload {
  student_id: string;
  instructor_id: string;
  course_id: number;
  latitude: number;
  longitude: number;
  timestamp?: string;
  device_id?: string;
}

export interface VisionCheckInPayload {
  student_id: string;
  instructor_id: string;
  course_id: number;
  image_b64: string;
  timestamp?: string;
}

export interface CheckInResponse {
  status: string;
  message: string;
  record_id: number;
  requires_visual_verification: boolean;
  confidence?: number;
}

export interface OverrideRequest {
  status: 'present' | 'absent';
  notes: string;
}

const api = {
  health: async () => {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },

  listCourses: async (instructorId: string) => {
    const response = await axios.get(`${API_URL}/api/instructor/courses`, {
      params: { instructor_id: instructorId },
    });
    return response.data as CourseSummary[];
  },

  listAttendance: async (courseId: number) => {
    const response = await axios.get(`${API_URL}/api/instructor/attendance`, {
      params: { course_id: courseId },
    });
    return response.data as AttendanceEvent[];
  },

  overrideAttendance: async (eventId: number, payload: OverrideRequest) => {
    const response = await axios.post(
      `${API_URL}/api/instructor/attendance/${eventId}/override`,
      payload,
    );
    return response.data as AttendanceEvent;
  },

  gpsCheckIn: async (payload: GPSCheckInPayload) => {
    const response = await axios.post(`${API_URL}/api/checkin/gps`, payload);
    return response.data as CheckInResponse;
  },

  visionCheckIn: async (payload: VisionCheckInPayload) => {
    const response = await axios.post(`${API_URL}/api/checkin/vision`, payload);
    return response.data as CheckInResponse;
  },
};

export default api;
