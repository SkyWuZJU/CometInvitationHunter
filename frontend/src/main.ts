// Comet Invitation Hunter Frontend
// Three-step user flow: email input → X verification → success message

import './style.css';

interface VerificationRequest {
  email: string;
  oauth_token?: string;
  oauth_verifier?: string;
}

interface VerificationResponse {
  success: boolean;
  message: string;
  error?: string;
}

interface OAuthInitResponse {
  success: boolean;
  oauth_url?: string;
  error?: string;
}

interface FollowCheckRequest {
  email: string;
  screen_name: string;
}

interface FollowCheckResponse {
  success: boolean;
  is_following: boolean;
  message: string;
}

class CometHunterApp {
  private email: string = '';
  private oauthToken: string = '';
  private screenName: string = '';

  constructor() {
    console.log('CometHunterApp initialized');
    this.createHTML();
    this.initializeEventListeners();
  }

  private createHTML(): void {
    const app = document.getElementById('app');
    if (!app) return;

    app.innerHTML = `
      <div class="container">
        <div class="logo">🚀 Comet Hunter</div>
        <div class="subtitle">Subscribe the Email, and get intime notification when someone shares Comet invitations on X</div>
        
        <div class="step-indicator">
          <div class="step active" id="step1"></div>
          <div class="step" id="step2"></div>
          <div class="step" id="step3"></div>
        </div>

        <!-- Step 1: Email Collection -->
        <div id="email-step" class="step-content">
          <div class="form-group">
            <label for="email">Step1: Email Address</label>
            <input type="email" id="email" placeholder="" required>
          </div>
          <button class="btn" id="email-submit">Continue</button>
        </div>

        <!-- Step 2: X OAuth Verification -->
        <div id="verification-step" class="step-content hidden">
          <div class="verification-info">
            <h3>Step2: Follow and Subscribe</h3>
            <p>Follow the creator on X and get the service for FREE:</p>
            <ol style="margin: 15px 0; padding-left: 20px; text-align: left;">
              <li>Follow <strong>@0xSky99</strong> on X</li>
              <li>Verify your X account</li>
            </ol>
            <p>
              <a href="https://x.com/0xSky99" target="_blank" rel="noopener noreferrer">
                → Follow @0xSky99
              </a>
            </p>
          </div>
          
          <div id="oauth-connect-section">
            <button class="btn" id="oauth-connect">🔗 Connect X Account</button>
          </div>
          
          <div id="pin-input-section" class="hidden">
            <div class="verification-info">
              <h3>Enter PIN Code</h3>
              <p>After authorizing the app on X, you'll receive a PIN code. Enter it below:</p>
            </div>
            <div class="form-group">
              <label for="oauth-pin">PIN Code from X</label>
              <input type="text" id="oauth-pin" placeholder="Enter the PIN code" required>
            </div>
            <button class="btn" id="verify-pin">Verify PIN</button>
          </div>
          
          <button class="btn btn-secondary" id="back-to-email">← Back</button>
        </div>

        <!-- Step 3: Success -->
        <div id="success-step" class="step-content hidden">
          <div class="success-message">
            <h3>🎉 You're all set!</h3>
            <p>You'll receive email notifications whenever new Comet browser invitations are shared on X.</p>
            <p>A initialization Email has been sent. Make sure it's not in the spam and the Email address is trusted.</p>
          </div>
        </div>

        <!-- Error/Loading Messages -->
        <div id="error-container"></div>
        <div id="loading-container"></div>
      </div>
    `;
  }

  private initializeEventListeners(): void {
    // Email step
    const emailSubmit = document.getElementById('email-submit') as HTMLButtonElement;
    const emailInput = document.getElementById('email') as HTMLInputElement;
    
    emailSubmit?.addEventListener('click', () => this.handleEmailSubmit());
    emailInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.handleEmailSubmit();
    });

    // OAuth verification step
    const oauthConnect = document.getElementById('oauth-connect') as HTMLButtonElement;
    const verifyPin = document.getElementById('verify-pin') as HTMLButtonElement;
    const pinInput = document.getElementById('oauth-pin') as HTMLInputElement;
    const backButton = document.getElementById('back-to-email') as HTMLButtonElement;
    
    oauthConnect?.addEventListener('click', () => this.handleOAuthConnect());
    verifyPin?.addEventListener('click', () => this.handlePinVerification());
    pinInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.handlePinVerification();
    });
    backButton?.addEventListener('click', () => this.goToStep(1));
  }

  private async handleEmailSubmit(): Promise<void> {
    const emailInput = document.getElementById('email') as HTMLInputElement;
    const email = emailInput.value.trim();

    // Clear previous errors
    this.clearMessages();

    // Validate email
    if (!this.validateEmail(email)) {
      this.showError('Please enter a valid email address.');
      return;
    }

    this.email = email;
    this.goToStep(2);
  }

  private async handleOAuthConnect(): Promise<void> {
    // Clear previous messages
    this.clearMessages();

    // Show loading state
    this.showLoading('Getting authorization URL...');
    this.setButtonLoading('oauth-connect', true);

    try {
      // Get OAuth URL from backend
      const response = await fetch('/api/auth/twitter/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: this.email })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: OAuthInitResponse = await response.json();
      
      if (data.success && data.oauth_url) {
        // Extract oauth_token from URL for later use
        const urlParams = new URLSearchParams(data.oauth_url.split('?')[1]);
        this.oauthToken = urlParams.get('oauth_token') || '';
        
        // Open Twitter OAuth in new tab and show PIN input
        window.open(data.oauth_url, '_blank');
        this.showPinInput();
      } else {
        this.showError(data.error || 'Failed to initialize OAuth. Please try again.');
      }
    } catch (error) {
      console.error('OAuth initialization error:', error);
      this.showError('Network error. Please check your connection and try again.');
    } finally {
      this.hideLoading();
      this.setButtonLoading('oauth-connect', false);
    }
  }

  private showPinInput(): void {
    const connectSection = document.getElementById('oauth-connect-section');
    const pinSection = document.getElementById('pin-input-section');
    
    if (connectSection) connectSection.classList.add('hidden');
    if (pinSection) pinSection.classList.remove('hidden');
  }

  private async handlePinVerification(): Promise<void> {
    const pinInput = document.getElementById('oauth-pin') as HTMLInputElement;
    const pin = pinInput.value.trim();

    // Clear previous messages
    this.clearMessages();

    // Validate PIN
    if (!pin) {
      this.showError('Please enter the PIN code from X.');
      return;
    }

    // Show loading state
    this.showLoading('Verifying your X account and follower status...');
    this.setButtonLoading('verify-pin', true);

    try {
      const response = await this.verifyUser(this.email, this.oauthToken, pin);
      
      if (response.success) {
        this.goToStep(3);
      } else {
        // Check if this is a follow-related error and extract screen name
        const isFollowError = !!(response.message && response.message.includes('follow @0xSky99'));
        if (isFollowError && response.message && response.message.includes('Authenticated as @')) {
          const match = response.message.match(/Authenticated as @(\w+)/);
          if (match) {
            this.screenName = match[1];
          }
        }
        this.showError(response.message || 'Verification failed. Please try again.', isFollowError);
      }
    } catch (error) {
      console.error('PIN verification error:', error);
      // Try to extract screen name from error if available
      const errorMessage = error instanceof Error ? error.message : 'Network error. Please check your connection and try again.';
      this.showError(errorMessage);
    } finally {
      this.hideLoading();
      this.setButtonLoading('verify-pin', false);
    }
  }



  private validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private async verifyUser(email: string, oauthToken: string, oauthVerifier: string): Promise<VerificationResponse> {
    const requestData: VerificationRequest = {
      email: email,
      oauth_token: oauthToken,
      oauth_verifier: oauthVerifier
    };

    const response = await fetch('/api/users/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      // Try to extract screen name from error details for follow checking
      if (errorData.detail && errorData.detail.includes('@')) {
        const match = errorData.detail.match(/@(\w+)/);
        if (match) {
          this.screenName = match[1];
        }
      }
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    return result;
  }

  private async handleTryFollowAgain(): Promise<void> {
    // Clear previous messages
    this.clearMessages();

    // Show loading state
    this.showLoading('Checking if you follow @0xSky99...');
    this.setButtonLoading('try-follow-again', true);

    try {
      const response = await this.checkFollowStatus(this.email, this.screenName);
      
      if (response.success && response.is_following) {
        // User is now following, complete the verification
        const user = await this.completeVerification(this.email);
        if (user.success) {
          this.goToStep(3);
        } else {
          this.showError(user.message || 'Failed to complete verification. Please try again.');
        }
      } else {
        this.showError(response.message, true); // Show try again button again
      }
    } catch (error) {
      console.error('Follow check error:', error);
      this.showError('Network error. Please check your connection and try again.');
    } finally {
      this.hideLoading();
      this.setButtonLoading('try-follow-again', false);
    }
  }

  private async checkFollowStatus(email: string, screenName: string): Promise<FollowCheckResponse> {
    const requestData: FollowCheckRequest = {
      email: email,
      screen_name: screenName
    };

    const response = await fetch('/api/users/check-follow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  private async completeVerification(email: string): Promise<VerificationResponse> {
    const response = await fetch('/api/users/complete-verification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  private goToStep(step: number): void {
    // Hide all step contents
    const steps = document.querySelectorAll('.step-content');
    steps.forEach(s => s.classList.add('hidden'));

    // Update step indicators
    for (let i = 1; i <= 3; i++) {
      const stepElement = document.getElementById(`step${i}`);
      if (stepElement) {
        stepElement.classList.remove('active', 'completed');
        if (i < step) {
          stepElement.classList.add('completed');
        } else if (i === step) {
          stepElement.classList.add('active');
        }
      }
    }

    // Show current step content
    let stepElementId: string;
    switch (step) {
      case 1:
        stepElementId = 'email-step';
        break;
      case 2:
        stepElementId = 'verification-step';
        break;
      case 3:
        stepElementId = 'success-step';
        break;
      default:
        stepElementId = 'email-step';
    }

    const stepElement = document.getElementById(stepElementId);
    if (stepElement) {
      stepElement.classList.remove('hidden');
    }

    this.clearMessages();
  }

  private showError(message: string, showTryAgain: boolean = false): void {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
      let tryAgainButton = '';
      if (showTryAgain) {
        tryAgainButton = `
          <button class="btn" id="try-follow-again" style="margin-top: 10px;">
            ✓ I have followed, try again
          </button>
        `;
      }
      
      errorContainer.innerHTML = `
        <div class="error-message">
          <strong>Error:</strong> ${message}
          ${tryAgainButton}
        </div>
      `;
      
      // Add event listener for try again button
      if (showTryAgain) {
        const tryAgainBtn = document.getElementById('try-follow-again');
        tryAgainBtn?.addEventListener('click', () => this.handleTryFollowAgain());
      }
    }
  }



  private showLoading(message: string): void {
    const loadingContainer = document.getElementById('loading-container');
    if (loadingContainer) {
      loadingContainer.innerHTML = `
        <div style="text-align: center; padding: 10px; color: #666;">
          <span class="loading"></span>
          ${message}
        </div>
      `;
    }
  }

  private hideLoading(): void {
    const loadingContainer = document.getElementById('loading-container');
    if (loadingContainer) {
      loadingContainer.innerHTML = '';
    }
  }

  private clearMessages(): void {
    const errorContainer = document.getElementById('error-container');
    const loadingContainer = document.getElementById('loading-container');
    
    if (errorContainer) errorContainer.innerHTML = '';
    if (loadingContainer) loadingContainer.innerHTML = '';
  }

  private setButtonLoading(buttonId: string, loading: boolean): void {
    const button = document.getElementById(buttonId) as HTMLButtonElement;
    if (button) {
      button.disabled = loading;
      if (loading) {
        if (buttonId === 'oauth-connect') {
          button.innerHTML = '<span class="loading"></span>Getting URL...';
        } else if (buttonId === 'verify-pin') {
          button.innerHTML = '<span class="loading"></span>Verifying...';
        } else if (buttonId === 'try-follow-again') {
          button.innerHTML = '<span class="loading"></span>Checking...';
        } else {
          button.innerHTML = '<span class="loading"></span>Processing...';
        }
      } else {
        if (buttonId === 'oauth-connect') {
          button.innerHTML = '🔗 Connect X Account';
        } else if (buttonId === 'verify-pin') {
          button.innerHTML = 'Verify PIN';
        } else if (buttonId === 'try-follow-again') {
          button.innerHTML = '✓ I have followed, try again';
        } else {
          button.innerHTML = 'Continue';
        }
      }
    }
  }
}

// Initialize the application when DOM is loaded or immediately if already loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new CometHunterApp();
  });
} else {
  new CometHunterApp();
}

// Export for potential testing
export { CometHunterApp };