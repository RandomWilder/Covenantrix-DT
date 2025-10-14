import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'
import './styles/themes.css'
import './styles/markdown.css'
import './styles/notifications.css'
import './i18n'
import { SettingsProvider } from './contexts/SettingsContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { SubscriptionProvider } from './contexts/SubscriptionContext'
import { UpgradeModalProvider } from './contexts/UpgradeModalContext'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <NotificationProvider>
      <SettingsProvider>
        <SubscriptionProvider>
          <UpgradeModalProvider>
            <App />
          </UpgradeModalProvider>
        </SubscriptionProvider>
      </SettingsProvider>
    </NotificationProvider>
  </React.StrictMode>,
)
