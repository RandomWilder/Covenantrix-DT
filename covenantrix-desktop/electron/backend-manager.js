const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');
const log = require('electron-log');
const net = require('net');

const isDev = process.env.NODE_ENV === 'development';
const DEFAULT_BACKEND_PORT = 8000;

class BackendManager {
  constructor() {
    this.backendProcess = null;
    this.backendPort = DEFAULT_BACKEND_PORT;
    this.startupRetries = 0;
    this.maxRetries = 3;
    this.isShuttingDown = false;
  }

  /**
   * Get the path to the backend executable
   */
  getBackendPath() {
    if (isDev) {
      // In development, use Python directly
      const backendDir = path.join(__dirname, '..', '..', 'backend');
      return {
        executable: process.platform === 'win32' ? 'python' : 'python3',
        args: [path.join(backendDir, 'main.py')],
        cwd: backendDir
      };
    }

    // In production, use bundled Python + source
    const resourcesPath = process.resourcesPath;
    const backendDir = path.join(resourcesPath, 'backend');
    const pythonDistPath = path.join(resourcesPath, 'python-dist');
    
    let pythonExecutable;
    if (process.platform === 'win32') {
      pythonExecutable = path.join(pythonDistPath, 'python.exe');
    } else {
      pythonExecutable = path.join(pythonDistPath, 'bin', 'python');
    }
    
    // Verify Python executable exists
    if (!fs.existsSync(pythonExecutable)) {
      throw new Error(`Python executable not found at: ${pythonExecutable}`);
    }

    // Verify backend directory exists
    if (!fs.existsSync(backendDir)) {
      throw new Error(`Backend directory not found at: ${backendDir}`);
    }

    return {
      executable: pythonExecutable,
      args: ['main.py'],
      cwd: backendDir
    };
  }

  /**
   * Check if a port is available
   */
  async isPortAvailable(port) {
    return new Promise((resolve) => {
      const server = net.createServer();
      
      server.once('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          resolve(false);
        } else {
          resolve(false);
        }
      });

      server.once('listening', () => {
        server.close();
        resolve(true);
      });

      server.listen(port, '127.0.0.1');
    });
  }

  /**
   * Find an available port starting from the default
   */
  async findAvailablePort() {
    let port = DEFAULT_BACKEND_PORT;
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts) {
      const available = await this.isPortAvailable(port);
      if (available) {
        return port;
      }
      port++;
      attempts++;
    }

    throw new Error(`Could not find available port after ${maxAttempts} attempts`);
  }

  /**
   * Wait for backend to be ready
   */
  async waitForBackend(maxWaitTime = 120000) {
    const startTime = Date.now();
    const checkInterval = 500;

    return new Promise((resolve, reject) => {
      const checkBackend = async () => {
        if (Date.now() - startTime > maxWaitTime) {
          reject(new Error('Backend startup timeout'));
          return;
        }

        try {
          const http = require('http');
          const options = {
            hostname: '127.0.0.1',
            port: this.backendPort,
            path: '/health',
            method: 'GET',
            timeout: 2000
          };

          const req = http.request(options, (res) => {
            if (res.statusCode === 200) {
              log.info('Backend is ready');
              resolve();
            } else {
              setTimeout(checkBackend, checkInterval);
            }
          });

          req.on('error', () => {
            setTimeout(checkBackend, checkInterval);
          });

          req.on('timeout', () => {
            req.destroy();
            setTimeout(checkBackend, checkInterval);
          });

          req.end();
        } catch (error) {
          setTimeout(checkBackend, checkInterval);
        }
      };

      checkBackend();
    });
  }

  /**
   * Start the backend server
   */
  async start() {
    if (this.backendProcess) {
      log.info('Backend is already running');
      return { port: this.backendPort, pid: this.backendProcess.pid };
    }

    try {
      // Find available port
      this.backendPort = await this.findAvailablePort();
      log.info(`Using port ${this.backendPort} for backend`);

      // Get backend path and configuration
      const { executable, args, cwd } = this.getBackendPath();
      
      log.info(`Starting backend: ${executable} ${args.join(' ')}`);
      log.info(`Working directory: ${cwd}`);

      // Prepare environment variables
      const env = {
        ...process.env,
        PORT: this.backendPort.toString(),
        HOST: '127.0.0.1',
        PYTHONUNBUFFERED: '1', // Ensure real-time output
        BACKEND_MODE: 'desktop'
      };

      // macOS-specific: Add PYTHONPATH and DYLD_LIBRARY_PATH
      if (process.platform === 'darwin' && !isDev) {
        const resourcesPath = process.resourcesPath;
        const backendDir = path.join(resourcesPath, 'backend');
        const libDir = path.join(resourcesPath, 'lib');
        
        env.PYTHONPATH = backendDir;
        log.info(`[macOS] Set PYTHONPATH to: ${backendDir}`);
        
        if (fs.existsSync(libDir)) {
          env.DYLD_LIBRARY_PATH = libDir;
          log.info(`[macOS] Set DYLD_LIBRARY_PATH to: ${libDir}`);
        } else {
          log.warn(`[macOS] lib directory not found at: ${libDir}`);
        }
      }

      // Load .env file if it exists
      const envPath = path.join(cwd, '.env');
      if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        envContent.split('\n').forEach(line => {
          const [key, ...valueParts] = line.split('=');
          if (key && valueParts.length > 0) {
            env[key.trim()] = valueParts.join('=').trim();
          }
        });
      }

      // Start backend process
      this.backendProcess = spawn(executable, args, {
        cwd,
        env,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      // Handle stdout
      this.backendProcess.stdout.on('data', (data) => {
        log.info(`[Backend] ${data.toString().trim()}`);
      });

      // Handle stderr
      this.backendProcess.stderr.on('data', (data) => {
        log.error(`[Backend Error] ${data.toString().trim()}`);
      });

      // Handle process exit
      this.backendProcess.on('exit', (code, signal) => {
        log.info(`Backend process exited with code ${code}, signal ${signal}`);
        this.backendProcess = null;

        // Retry if not intentionally shut down
        if (!this.isShuttingDown && this.startupRetries < this.maxRetries) {
          this.startupRetries++;
          log.info(`Retrying backend startup (${this.startupRetries}/${this.maxRetries})...`);
          setTimeout(() => this.start(), 2000);
        } else if (this.startupRetries >= this.maxRetries) {
          log.error('Backend failed to start after maximum retries');
        }
      });

      // Handle process errors
      this.backendProcess.on('error', (error) => {
        log.error(`Backend process error: ${error.message}`);
        this.backendProcess = null;
      });

      // Wait for backend to be ready
      await this.waitForBackend();
      
      this.startupRetries = 0; // Reset retry counter on success
      log.info(`Backend started successfully on port ${this.backendPort}`);

      return {
        port: this.backendPort,
        pid: this.backendProcess.pid,
        url: `http://127.0.0.1:${this.backendPort}`
      };

    } catch (error) {
      log.error(`Failed to start backend: ${error.message}`);
      throw error;
    }
  }

  /**
   * Stop the backend server
   */
  async stop() {
    if (!this.backendProcess) {
      log.info('Backend is not running');
      return;
    }

    this.isShuttingDown = true;

    return new Promise((resolve) => {
      log.info('Stopping backend...');

      const timeout = setTimeout(() => {
        if (this.backendProcess) {
          log.warn('Backend did not stop gracefully, killing process');
          this.backendProcess.kill('SIGKILL');
        }
        resolve();
      }, 5000);

      this.backendProcess.once('exit', () => {
        clearTimeout(timeout);
        this.backendProcess = null;
        this.isShuttingDown = false;
        log.info('Backend stopped successfully');
        resolve();
      });

      // Try graceful shutdown first
      this.backendProcess.kill('SIGTERM');
    });
  }

  /**
   * Get backend status
   */
  getStatus() {
    return {
      running: this.backendProcess !== null,
      port: this.backendPort,
      pid: this.backendProcess?.pid || null,
      url: this.backendProcess ? `http://127.0.0.1:${this.backendPort}` : null
    };
  }

  /**
   * Restart the backend
   */
  async restart() {
    log.info('Restarting backend...');
    await this.stop();
    await new Promise(resolve => setTimeout(resolve, 1000));
    return await this.start();
  }
}

// Export singleton instance
const backendManager = new BackendManager();

module.exports = {
  backendManager,
  startBackend: () => backendManager.start(),
  stopBackend: () => backendManager.stop(),
  restartBackend: () => backendManager.restart(),
  getBackendStatus: () => backendManager.getStatus()
};