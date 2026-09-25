import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { I18nProvider } from './i18n.jsx'
import './styles.css'

// Font Awesome 4.7 is loaded via <link> in index.html (CDN), per the
// project's "中国大陆镜像优先" rule. Do not import the npm package
// here -- it is not installed and the CDN is the only source.

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </React.StrictMode>,
)
