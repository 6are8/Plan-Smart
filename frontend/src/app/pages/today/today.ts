import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

/**
 * Weather data received from the backend.
 * Describes current weather conditions for the user's city.
 */
interface Weather {
  temperature: number;   // Current temperature in °C
  description: string;   // Weather description (e.g. "clear sky")
  wind: number;          // Wind speed in m/s
  feels_like: number;    // Feels-like temperature in °C
}

/**
 * AI-generated daily plan for the user.
 */
interface DayPlan {
  items: string[]; // List of plan items for today
}

/**
 * Full response structure returned by GET /today endpoint.
 */
interface TodayResponse {
  city: string;      // User's selected city
  weather: Weather;  // Weather data for the city
  quote: string;     // Quote of the day
  plan: DayPlan;     // Daily AI-generated plan
}

/**
 * Today page component.
 *
 * Displays:
 * - Greeting with username (decoded from JWT)
 * - Current date
 * - Weather information
 * - Quote of the day
 * - Daily AI-generated plan
 */
@Component({
  selector: 'app-today',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './today.html',
  styleUrl: './today.css',
})
export class Today implements OnInit {

  /** Username extracted from JWT token (UI only) */
  username = '';

  /** User's city returned by the backend */
  city = '';

  /** Current date (used for date pipe in template) */
  today = new Date();

  /** Weather data (null until loaded) */
  weather: Weather | null = null;

  /** Quote of the day */
  quote = '';

  /** Daily plan (null until loaded) */
  plan: DayPlan | null = null;

  constructor(private http: HttpClient) {}

  /**
   * Angular lifecycle hook.
   * Initializes the page by:
   * - Extracting username from JWT (client-side only)
   * - Loading today's data from backend
   */
  ngOnInit(): void {
    this.loadUsernameFromToken();
    this.loadToday();
  }

  /**
   * Loads all data for the Today page from the backend.
   * Uses a single endpoint to minimize API calls.
   *
   * Authorization header is automatically added
   * by HttpInterceptor.
   *
   * GET /today
   */
  loadToday(): void {
    this.http
      .get<TodayResponse>('http://localhost:5000/today')
      .subscribe(res => {
        this.city = res.city;
        this.weather = res.weather;
        this.quote = res.quote;
        this.plan = res.plan;
      });
  }

  /**
   * Extracts the username from JWT token and formats it.
   * Used ONLY for greeting display.
   *
   * Backend should NEVER trust this value.
   */
  private loadUsernameFromToken(): void {
    const username = this.getUsernameFromToken();
    if (username) {
      this.username =
        username.charAt(0).toUpperCase() + username.slice(1);
    }
  }

  /**
   * Decodes JWT token stored in localStorage
   * and extracts the subject (username).
   *
   * This method is used only for UI convenience.
   *
   * @returns Username if token is valid, otherwise null
   */
  private getUsernameFromToken(): string | null {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      const payload = token.split('.')[1];
      const decoded = JSON.parse(
        atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
      );
      return decoded.sub ?? null;
    } catch {
      return null;
    }
  }
}
