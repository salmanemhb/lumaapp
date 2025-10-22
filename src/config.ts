/**
 * Application configuration
 * Centralized place for all environment-specific URLs
 */

export const config = {
  // Backend API URL
  apiUrl: 'https://luma-final.onrender.com',
  
  // Frontend URL (for redirects, etc.)
  frontendUrl: window.location.origin,
} as const;
