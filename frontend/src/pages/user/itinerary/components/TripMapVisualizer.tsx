import { useEffect } from 'react'
import { Map, AdvancedMarker, Pin, useMap } from '@vis.gl/react-google-maps'
import type { ItineraryDetailResponse } from '@/types/itineraryTypes'

interface TripMapVisualizerProps {
  itinerary: ItineraryDetailResponse
}

export default function TripMapVisualizer({ itinerary }: TripMapVisualizerProps) {
  // Extract all stops that have valid coordinates
  const stopsWithCoords = itinerary.days
    .flatMap((day) => day.stops)
    .filter(
      (stop) =>
        stop.latitude !== undefined &&
        stop.latitude !== null &&
        stop.longitude !== undefined &&
        stop.longitude !== null
    )

  const defaultCenter =
    stopsWithCoords.length > 0
      ? { lat: stopsWithCoords[0].latitude!, lng: stopsWithCoords[0].longitude! }
      : { lat: 39.8283, lng: -98.5795 } // Center of US as fallback

  const defaultZoom = stopsWithCoords.length > 0 ? 12 : 3

  const map = useMap()

  useEffect(() => {
    if (!map || stopsWithCoords.length === 0) return

    const bounds = new window.google.maps.LatLngBounds()
    stopsWithCoords.forEach((stop) => {
      bounds.extend({ lat: stop.latitude!, lng: stop.longitude! })
    })

    // Fit bounds with generous padding so markers aren't at the very edge
    map.fitBounds(bounds, { top: 60, right: 60, bottom: 60, left: 60 })
  }, [map, stopsWithCoords])

  return (
    <div className="w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-slate-200/60 shadow-md ring-1 ring-slate-900/5 bg-slate-50 relative">
      <Map
        mapId="DEMO_MAP_ID" // Required for AdvancedMarker
        defaultZoom={defaultZoom}
        defaultCenter={defaultCenter}
        gestureHandling="greedy"
        disableDefaultUI={true}
      >
        {stopsWithCoords.map((stop) => (
          <AdvancedMarker
            key={stop.id}
            position={{ lat: stop.latitude!, lng: stop.longitude! }}
            title={stop.locationName || 'Unknown Location'}
          >
            <Pin
              background={'#2563eb'}
              borderColor={'#1d4ed8'}
              glyphColor={'#ffffff'}
            />
            {/* Optional label indicator below the pin */}
            <div className="absolute top-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900/90 px-2 py-1 text-[10px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
              {stop.locationName}
            </div>
          </AdvancedMarker>
        ))}
      </Map>
      
      {/* Fallback Overlay if no locations exist */}
      {stopsWithCoords.length === 0 && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/40 backdrop-blur-[2px]">
          <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100 text-center max-w-xs">
            <h3 className="font-semibold text-slate-800 mb-1">No Locations Yet</h3>
            <p className="text-xs text-slate-500">
              Once you add stops to your itinerary, they will appear on the map here.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
