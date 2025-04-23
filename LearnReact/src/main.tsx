import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
//npm i bootstrap@5.3.5
//Bootstrap is a free, open-source CSS framework that simplifies front-end web development, particularly for creating responsive and mobile-first websites and web applications.
import 'bootstrap/dist/css/bootstrap.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
