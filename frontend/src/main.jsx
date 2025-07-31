import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppAPI from './AppAPI.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppAPI />
  </StrictMode>,
)