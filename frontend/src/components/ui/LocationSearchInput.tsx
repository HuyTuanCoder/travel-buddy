import { useEffect, useRef, useState } from 'react'
import { useMapsLibrary } from '@vis.gl/react-google-maps'

interface LocationSearchInputProps {
  onPlaceSelected: (placeId: string, placeName: string) => void
  className?: string
}

export default function LocationSearchInput({
  onPlaceSelected,
  className,
}: LocationSearchInputProps) {
  const [placeAutocomplete, setPlaceAutocomplete] =
    useState<google.maps.places.Autocomplete | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const places = useMapsLibrary('places')

  useEffect(() => {
    if (!places || !inputRef.current) return

    const options = {
      fields: ['place_id', 'name', 'formatted_address'],
    }

    setPlaceAutocomplete(new places.Autocomplete(inputRef.current, options))
  }, [places])

  useEffect(() => {
    if (!placeAutocomplete) return

    const listener = placeAutocomplete.addListener('place_changed', () => {
      const place = placeAutocomplete.getPlace()
      if (place.place_id && place.name) {
        onPlaceSelected(place.place_id, place.name)
      }
    })

    return () => {
      google.maps.event.removeListener(listener)
    }
  }, [placeAutocomplete, onPlaceSelected])

  return (
    <input
      ref={inputRef}
      placeholder="Search for a place..."
      className={className}
      required
    />
  )
}
