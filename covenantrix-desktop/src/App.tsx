import { useState, useEffect } from 'react'
import AppLayout from './components/layout/AppLayout'
import SettingsSetup from './features/onboarding/SettingsSetup'
import { useSettings } from './hooks/useSettings'
import { useTheme } from './hooks/useTheme'

function App() {
  const { isFirstRun, isLoading } = useSettings()
  const { effectiveTheme } = useTheme()
  const [showOnboarding, setShowOnboarding] = useState(false)

  useEffect(() => {
    if (!isLoading && isFirstRun) {
      setShowOnboarding(true)
    }
  }, [isFirstRun, isLoading])

  const handleOnboardingComplete = () => {
    setShowOnboarding(false)
  }

  const handleOnboardingSkip = () => {
    setShowOnboarding(false)
  }

  if (isLoading) {
    return (
      <div className={`h-screen w-screen flex items-center justify-center ${
        effectiveTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      }`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className={effectiveTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
            Loading application...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={`h-screen w-screen ${
      effectiveTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <AppLayout />
      {showOnboarding && (
        <SettingsSetup
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
    </div>
  )
}

export default App
