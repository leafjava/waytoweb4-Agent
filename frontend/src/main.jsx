import React from 'react'
import ReactDOM from 'react-dom/client'
import 'font-awesome/css/font-awesome.min.css'
import App from './App.jsx'
import { I18nProvider } from './i18n.jsx'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </React.StrictMode>,
)
