// Preset locations for classrooms
// Coordinates are synthetic/demo friendly and safe to commit.
// Update locally if you need to match a specific lecture hall.

export interface PresetLocation {
  id: string;
  name: string;
  building: string;
  latitude: number;
  longitude: number;
}

export const PRESET_LOCATIONS: PresetLocation[] = [
  {
    id: 'emerson',
    name: 'Emerson Classroom',
    building: 'Emerson',
    latitude: 42.37385806640899,
    longitude: -71.11521638475821,
  },
  {
    id: 'sever',
    name: 'Sever Classroom',
    building: 'Sever',
    latitude: 42.37436150350825,
    longitude: -71.11549714983167,
  },
  {
    id: 'science_center',
    name: 'Science Center Classroom',
    building: 'Science Center',
    latitude: 42.37622938351009,
    longitude: -71.1170730606735,
  },
];

// Helper function to get location by building name
export function getLocationByBuilding(building: string): PresetLocation | undefined {
  return PRESET_LOCATIONS.find(
    loc => loc.building.toLowerCase() === building.toLowerCase()
  );
}

// Helper function to get location by classroom ID or name
export function getLocationByClassroom(classroomName: string): PresetLocation | undefined {
  const normalized = classroomName.toLowerCase();
  
  return PRESET_LOCATIONS.find(loc => {
    const locBuilding = loc.building.toLowerCase();
    const locName = loc.name.toLowerCase();
    
    // Check if the classroom name contains the building name
    return normalized.includes(locBuilding) || 
           normalized.includes(loc.id) ||
           locName.includes(normalized);
  });
}
