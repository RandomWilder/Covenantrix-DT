import React from 'react'
import { ChevronDown, Plus, Settings as SettingsIcon } from 'lucide-react'
import { GoogleAccountResponse } from '../../../services/googleService'

interface DriveAccountSelectorProps {
  accounts: GoogleAccountResponse[]
  selectedAccountId: string | null
  onAccountSelect: (accountId: string) => void
  onAddAccount: () => void
  onManageAccounts: () => void
  disabled?: boolean
}

const DriveAccountSelector: React.FC<DriveAccountSelectorProps> = ({
  accounts,
  selectedAccountId,
  onAccountSelect,
  onAddAccount,
  onManageAccounts,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const selectedAccount = accounts.find(acc => acc.account_id === selectedAccountId)

  return (
    <div className="relative">
      {/* Selected Account Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
            {selectedAccount ? selectedAccount.email[0].toUpperCase() : '?'}
          </div>
          <div className="text-left">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {selectedAccount ? selectedAccount.email : 'Select Account'}
            </div>
            {selectedAccount?.display_name && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {selectedAccount.display_name}
              </div>
            )}
          </div>
        </div>
        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Menu */}
          <div className="absolute top-full mt-2 left-0 right-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 overflow-hidden">
            {/* Accounts List */}
            <div className="max-h-64 overflow-y-auto">
              {accounts.map((account) => (
                <button
                  key={account.account_id}
                  onClick={() => {
                    onAccountSelect(account.account_id)
                    setIsOpen(false)
                  }}
                  className={`w-full flex items-center space-x-3 px-4 py-3 transition-colors ${
                    account.account_id === selectedAccountId
                      ? 'bg-primary/10 border-l-2 border-primary'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
                    {account.email[0].toUpperCase()}
                  </div>
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {account.email}
                    </div>
                    {account.display_name && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {account.display_name}
                      </div>
                    )}
                  </div>
                  {account.status === 'expired' && (
                    <span className="text-xs text-yellow-600 dark:text-yellow-500">
                      Expired
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Actions */}
            <div className="border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => {
                  onAddAccount()
                  setIsOpen(false)
                }}
                className="w-full flex items-center space-x-2 px-4 py-3 text-primary hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm font-medium">Add Another Account</span>
              </button>
              
              <button
                onClick={() => {
                  onManageAccounts()
                  setIsOpen(false)
                }}
                className="w-full flex items-center space-x-2 px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <SettingsIcon className="w-4 h-4" />
                <span className="text-sm font-medium">Manage Accounts</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default DriveAccountSelector

