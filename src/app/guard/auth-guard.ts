import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

/**
 * Authentication route guard.
 *
 * Purpose:
 * - Allows navigation only if a valid access token exists
 * - Redirects unauthenticated users to the login page
 */
export const authGuard: CanActivateFn = () => {

  const router = inject(Router);
  const token = localStorage.getItem('token');

  if (token) {
    return true;
  }

  router.navigate(['/login']);
  return false;
};
