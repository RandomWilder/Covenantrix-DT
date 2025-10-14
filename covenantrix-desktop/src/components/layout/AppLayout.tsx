import React, { useState } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'
import StatusBar from './StatusBar'
import UploadScreen from '../../features/upload/UploadScreen'
import DocumentsScreen from '../../features/documents/DocumentsScreen'
import { ChatScreen } from '../../features/chat/ChatScreen'
import { ChatProvider } from '../../contexts/ChatContext'
import ProfileModal from '../../features/profile/ProfileModal'
import { TrialBanner } from '../../features/subscription/TrialBanner'
import { GracePeriodWarning } from '../../features/subscription/GracePeriodWarning'

interface AppLayoutProps {
  children?: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [activeScreen, setActiveScreen] = useState<string>('dashboard')
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)

  const renderContent = () => {
    switch (activeScreen) {
      case 'upload':
        return <UploadScreen />
      case 'documents':
        return <DocumentsScreen />
      case 'chat':
        return (
          <ChatProvider>
            <ChatScreen />
          </ChatProvider>
        )
      case 'dashboard':
      default:
        return children || (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                Welcome to Covenantrix
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Your RAG-powered document intelligence platform
              </p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="app-window flex flex-col">
      <Header onProfileClick={() => setIsProfileModalOpen(true)} />
      <GracePeriodWarning />
      <TrialBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar onNavigate={setActiveScreen} activeScreen={activeScreen} />
        <main className="main-content flex-1 flex flex-col">
          <div className="flex-1 overflow-auto">
            {renderContent()}
          </div>
          <StatusBar onProfileClick={() => setIsProfileModalOpen(true)} />
        </main>
      </div>
      
      {/* Profile Modal */}
      <ProfileModal 
        isOpen={isProfileModalOpen} 
        onClose={() => setIsProfileModalOpen(false)} 
      />
    </div>
  )
}

export default AppLayout
