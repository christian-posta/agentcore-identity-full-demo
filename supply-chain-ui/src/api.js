const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.auth = null;
  }

  setAuth(authInstance) {
    this.auth = authInstance;
  }

  getToken() {
    if (this.auth && this.auth.token) {
      return this.auth.token;
    }
    return null;
  }

  async refreshTokenIfNeeded() {
    if (this.auth && this.auth.updateToken) {
      try {
        await this.auth.updateToken();
        return true;
      } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
      }
    }
    return false;
  }

  async getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    let token = this.getToken();
    if (!token && this.auth && this.auth.updateToken) {
      await this.refreshTokenIfNeeded();
      token = this.getToken();
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add ID token for agent-to-agent authentication if available
    if (this.auth && this.auth.idToken) {
      headers['X-ID-Token'] = this.auth.idToken;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = await this.getHeaders();
    const config = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication endpoints - now handled by Auth0
  async getCurrentUser() {
    return await this.request('/auth/me');
  }

  // Agent endpoints
  async getAgentStatus() {
    return await this.request('/agents/status');
  }

  async getAgentActivities() {
    return await this.request('/agents/activities');
  }

  // Optimization endpoints
  async startOptimization(requestData) {
    return await this.request('/optimization/start', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  async getOptimizationProgress(requestId) {
    return await this.request(`/optimization/progress/${requestId}`);
  }

  async getOptimizationResults(requestId) {
    return await this.request(`/optimization/${requestId}/results`);
  }
}

const apiService = new ApiService();
export default apiService;
