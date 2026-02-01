import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

interface UserDto {
  username: string;
  city: string;
  sleep_goal_hours?: number;
}

interface MorningPlanDto {
  id: string;
  date: string;
  plan_text: string;
  weather?: string | null;
  sleep_duration?: number | null;
  created_at?: string;
  user_id?: string;
}

interface JournalEntryDto {
  id: string;
  date: string;
  mood: number;
  what_went_well: string;
  what_to_improve: string;
  how_i_feel: string;
  ai_summary?: string | null;
}

interface EveningPromptDto {
  id: string;
  date: string;
  prompt_text: string;
}

interface TodayBackendResponse {
  date: string;
  user: UserDto;
  morning_plan: MorningPlanDto | null;
  journal_entry: JournalEntryDto | null;
  evening_prompt: EveningPromptDto | null;
}

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

  /** Data returned by backend */
  morningPlanText: string | null = null;
  morningWeather: string | null = null;

  eveningPromptText: string | null = null;

  journalSummary: string | null = null;
  journalMood: number | null = null;

  /** Basic loading states */
  loadingToday = true;
  generatingMorningPlan = false;

  /** Guard to avoid infinite retry loops */
  private morningPlanTriggeredOnce = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadUsernameFromToken();
    this.loadTodayAndEnsureMorningPlan();
  }

  /**
   * Main flow:
   * 1) GET /today
   * 2) if morning_plan is missing -> GET /morning/plan
   * 3) re-GET /today
   */
  private loadTodayAndEnsureMorningPlan(): void {
    this.loadingToday = true;

    this.http.get<TodayBackendResponse>('http://localhost:5000/today')
      .subscribe({
        next: (res) => {
          this.applyTodayResponse(res);

          // If morning plan not generated yet, trigger generation once, then reload /today
          if (!res.morning_plan && !this.morningPlanTriggeredOnce) {
            this.morningPlanTriggeredOnce = true;
            this.generatingMorningPlan = true;

            this.http.get<any>('http://localhost:5000/morning/plan')
              .subscribe({
                next: () => {
                  this.generatingMorningPlan = false;

                  // Reload /today to fetch the freshly created morning_plan
                  this.http.get<TodayBackendResponse>('http://localhost:5000/today')
                    .subscribe({
                      next: (res2) => {
                        this.applyTodayResponse(res2);
                        this.loadingToday = false;
                      },
                      error: (err2) => {
                        console.error('Failed to reload /today after /morning/plan:', err2);
                        this.loadingToday = false;
                      }
                    });
                },
                error: (err) => {
                  console.error('Failed to generate morning plan via /morning/plan:', err);
                  this.generatingMorningPlan = false;
                  this.loadingToday = false;
                }
              });

            return;
          }

          this.loadingToday = false;
        },
        error: (err) => {
          console.error('Failed to load /today:', err);
          this.loadingToday = false;
        }
      });
  }

  /**
   * Maps backend response into UI fields.
   * Keep this aligned with your today.html bindings.
   */
  private applyTodayResponse(res: TodayBackendResponse): void {
    this.city = res.user?.city ?? '';
    this.morningPlanText = res.morning_plan?.plan_text ?? null;
    this.morningWeather = res.morning_plan?.weather ?? null;

    this.eveningPromptText = res.evening_prompt?.prompt_text ?? null;

    this.journalSummary = res.journal_entry?.ai_summary ?? null;
    this.journalMood = (typeof res.journal_entry?.mood === 'number') ? res.journal_entry.mood : null;

    // Keep displayed date in sync with backend date if you want
    // res.date is "YYYY-MM-DD"
    if (res.date) {
      const parsed = new Date(res.date + 'T00:00:00');
      if (!isNaN(parsed.getTime())) this.today = parsed;
    }
  }

  /**
   * Extracts the username from JWT token and formats it.
   * Used ONLY for greeting display.
   */
  private loadUsernameFromToken(): void {
    const username = this.getUsernameFromToken();
    if (username) {
      this.username = username.charAt(0).toUpperCase() + username.slice(1);
    }
  }

  /**
   * Decodes JWT token stored in localStorage and extracts the subject (username).
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

  /**
   * Returns emoji based on weather description.
   * This makes the weather card more visual.
   */
  getWeatherEmoji(): string {
    if (!this.morningWeather) return '🌤️';
    
    const weather = this.morningWeather.toLowerCase();
    
    if (weather.includes('sun') || weather.includes('clear')) return '☀️';
    if (weather.includes('cloud')) return '☁️';
    if (weather.includes('rain') || weather.includes('regen')) return '🌧️';
    if (weather.includes('snow') || weather.includes('schnee')) return '❄️';
    if (weather.includes('storm') || weather.includes('gewitter')) return '⛈️';
    if (weather.includes('fog') || weather.includes('nebel')) return '🌫️';
    
    return '🌤️'; // Default
  }

  /**
   * Extracts temperature from weather string if present.
   * E.g., "0.9°C, Mäßiger schnee" → "0.9°C"
   */
  getTemperature(): string {
    if (!this.morningWeather) return '';
    
    const match = this.morningWeather.match(/(-?\d+\.?\d*)°C/);
    return match ? match[1] + '°C' : '';
  }

  /**
   * Extracts weather condition from weather string.
   * E.g., "0.9°C, Mäßiger schnee" → "Mäßiger schnee"
   */
  getWeatherCondition(): string {
    if (!this.morningWeather) return '';
    
    const parts = this.morningWeather.split(',');
    return parts.length > 1 ? parts[1].trim() : this.morningWeather;
  }

  /**
   * Returns emoji based on mood rating.
   */
  getMoodEmoji(mood: number): string {
    if (mood >= 5) return '😄';
    if (mood >= 4) return '🙂';
    if (mood >= 3) return '😐';
    if (mood >= 2) return '😕';
    return '😢';
  }
}