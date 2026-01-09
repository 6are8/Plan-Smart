import { Component } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { Sidebar } from '../sidebar/sidebar';

/**
 * Main application layout.
 *
 * Wraps all authenticated pages and provides:
 * - Sidebar navigation
 * - Content container
 * - Global logout action
 */
@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, Sidebar],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.css',
})
export class MainLayout {

  constructor(private router: Router) {}

  /**
   * Logs the user out by:
   * - Removing tokens from localStorage
   * - Redirecting to login page
   */
  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');

    this.router.navigate(['/login']);
  }
}
