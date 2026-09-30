import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

function MapView() {
  const [telemetry, setTelemetry] = useState(null)

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/telemetry')
      .then((response) => {
        setTelemetry(response.data)
      })
      .catch((error) => {
        console.error('Error fetching telemetry:', error)
      })
  }, [])

  if (!telemetry) {
    return <div>Loading drone telemetry...</div>
  }

  const dronePosition = [
    telemetry.latitude,
    telemetry.longitude
  ]

  return (
    <MapContainer
      center={dronePosition}
      zoom={15}
      style={{ height: '400px', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <Marker position={dronePosition}>
        <Popup>
          <strong>SkyGuard AI Drone</strong>
          <br />
          Latitude: {telemetry.latitude.toFixed(6)}
          <br />
          Longitude: {telemetry.longitude.toFixed(6)}
          <br />
          Altitude: {telemetry.altitude.toFixed(1)} m
          <br />
          Flight Mode: {telemetry.flight_mode}
        </Popup>
      </Marker>
    </MapContainer>
  )
}

export default MapView