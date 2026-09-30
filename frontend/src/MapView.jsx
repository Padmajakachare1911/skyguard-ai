import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const dronePosition = [19.033, 73.0297]

function MapView() {
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
          Test drone position
        </Popup>
      </Marker>
    </MapContainer>
  )
}

export default MapView