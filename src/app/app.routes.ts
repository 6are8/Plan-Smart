import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import { Today } from './pages/today/today';
import { Diary } from './pages/diary/diary';
import { History } from './pages/history/history';
import { Settings } from './pages/settings/settings';

import { authGuard } from './guard/auth-guard';
import { MainLayout } from './structure/main-layout/main-layout';
import { AuthLayout } from './structure/auth-layout/auth-layout';

/**
 * Application routing configuration.
 *
 * Structure:
 * - Root path redirects to /today
 * - Authentication pages use AuthLayout
 * - Protected application pages use MainLayout
 * - All protected routes are guarded by authGuard
 */
export const routes: Routes = [

  /**
   * Root redirect.
   * Navigating to "/" always redirects to "/today".
   */
  {
    path: '',
    redirectTo: 'today',
    pathMatch: 'full',
  },

  /**
   * Authentication layout.
   * Contains public routes that do not require authentication.
   */
  {
    path: '',
    component: AuthLayout,
    children: [
      { path: 'login', component: Login },
      { path: 'register', component: Register },
    ],
  },

  /**
   * Main application layout.
   * All child routes require authentication.
   */
  {
    path: '',
    component: MainLayout,
    canActivateChild: [authGuard],
    children: [
      { path: 'today', component: Today },
      { path: 'diary', component: Diary },
      { path: 'history', component: History },
      { path: 'settings', component: Settings },
    ],
  },

  /**
   * Fallback route.
   * Redirects any unknown path to /today.
   */
  { path: '**', redirectTo: 'today' },
];
