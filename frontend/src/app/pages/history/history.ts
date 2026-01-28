import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

/**
 * Single item displayed in the History list view.
 *
 * This is a lightweight projection of a diary/journal entry returned by the backend.
 * The list shows only:
 * - the entry date (human-readable)
 * - the AI-generated summary (or a fallback string)
 */
interface HistoryItem {
  /** Unique entry identifier used for navigation and fetching entry details. */
  id: string;

  /** Entry date as an ISO string. */
  date: string;

  /** Short AI-generated summary shown in the list UI. */
  summary: string;
}

/**
 * Supported mood labels.
 *
 * IMPORTANT:
 * The application uses mood labels as strings end-to-end:
 * - Diary component sends a string label to the backend (e.g. "Happy", "Angry").
 * - History component expects the backend to return the same string label.
 *
 * If the backend ever returns numeric mood values (legacy data), you should
 * normalize them to MoodName before assigning to `HistoryDetails.mood`.
 */
type MoodName =
  | 'Excited'
  | 'Happy'
  | 'Calm'
  | 'Focused'
  | 'Tired'
  | 'Sad'
  | 'Stressed'
  | 'Angry';

/**
 * Full details displayed inside the History "Details" modal.
 *
 * This structure is derived from the backend response returned by GET /journal/<id>.
 * Fields are mapped to a stable UI model to keep the template clean and predictable.
 */
interface HistoryDetails {
  /** Unique entry identifier. */
  id: string;

  /** Entry date as an ISO string. */
  date: string;

  /**
   * Mood label saved with the entry.
   * This is expected to be a MoodName string (e.g. "Calm").
   */
  mood: MoodName;

  /** "What went well" reflection text. */
  good: string;

  /** "What can be improved" reflection text. */
  improve: string;

  /** Optional AI-generated summary. May be null/undefined if not available. */
  aiSummary?: string | null;
}

/**
 * Backend response shape for GET /history?limit=...
 *
 * NOTE:
 * The backend endpoint is aggregated and can return several categories.
 * In this UI we only consume `journal_entries`, which we map to `HistoryItem[]`.
 *
 * We intentionally keep this as a loose/partial type because the backend can evolve,
 * while the UI only depends on the presence of `journal_entries`.
 */
interface BackendHistoryResponse {
  morning_sessions?: any[];
  journal_entries?: any[];
  evening_prompts?: any[];
  limit?: number;
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './history.html',
  styleUrl: './history.css',
})
export class History implements OnInit {

  /**
   * List of history entries shown in the UI (newest first).
   * Populated by `loadHistory()`.
   */
  entries: HistoryItem[] = [];

  /**
   * Loading state for the history list.
   * Used to display a loading message/spinner in the template.
   */
  loading = true;

  /**
   * Selected entry for the details modal.
   * When set, the template renders a modal overlay.
   */
  selectedEntry: HistoryDetails | null = null;

  /**
   * @param http Angular HttpClient used to communicate with the backend API.
   */
  constructor(private http: HttpClient) {}

  /**
   * Angular lifecycle hook.
   *
   * Loads the history list when the component initializes.
   * (Angular calls this method by name; it is not invoked manually.)
   */
  ngOnInit(): void {
    this.loadHistory();
  }

  /**
   * Loads history entries from the backend aggregated endpoint.
   *
   * Endpoint:
   * - GET /history?limit=30
   *
   * Behavior:
   * - Reads `journal_entries` from the response (if present)
   * - Maps each entry into a lightweight `HistoryItem` for display
   * - Sorts items by date (newest first)
   *
   * UI:
   * - Sets `loading=true` while request is in flight
   * - Sets `loading=false` on both success and error
   */
  loadHistory(): void {
    this.loading = true;

    this.http
      .get<BackendHistoryResponse>('http://localhost:5000/history?limit=30')
      .subscribe({
        next: (res) => {
          const journalEntries = Array.isArray(res?.journal_entries) ? res.journal_entries : [];

          // Map backend journal entry -> UI list item
          const mapped: HistoryItem[] = journalEntries.map((e: any) => ({
            id: String(e.id),
            date: String(e.date),
            summary: String(e.ai_summary ?? 'No AI summary available.')
          }));

          // Sort newest first
          this.entries = mapped.sort(
            (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
          );

          this.loading = false;
        },
        error: (err) => {
          console.error('Failed to load history:', err);
          this.entries = [];
          this.loading = false;
        }
      });
  }

  /**
   * Opens the details modal for the selected entry.
   *
   * Endpoint:
   * - GET /journal/<id>
   *
   * Mapping:
   * - Backend fields may use snake_case; we map them to a stable UI model.
   * - `mood` is expected to be a MoodName string label.
   *
   * @param id Entry identifier from the history list.
   */
  openDetails(id: string): void {
    this.http
      .get<any>(`http://localhost:5000/journal/${id}`)
      .subscribe({
        next: (res) => {
          const entry = res?.entry ?? res;

          this.selectedEntry = {
            id: String(entry.id),
            date: String(entry.date),
            mood: entry.mood as MoodName,
            good: String(entry.what_went_well ?? ''),
            improve: String(entry.what_to_improve ?? ''),
            aiSummary: entry.ai_summary ?? null
          };
        },
        error: (err) => {
          console.error('Failed to load entry details:', err);
        }
      });
  }

  /**
   * Closes the details modal and clears the selected entry state.
   */
  closeDetails(): void {
    this.selectedEntry = null;
  }

  /**
   * Formats a short date string for the history list display.
   *
   * Example output:
   * - "Mon, Sep 18"
   *
   * @param date ISO date string.
   * @returns Formatted date for list UI.
   */
  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'short',
      day: '2-digit',
      month: 'short'
    });
  }

  /**
   * Formats a full date string for the details modal.
   *
   * Example output:
   * - "Monday, September 18, 2025"
   *
   * @param date ISO date string.
   * @returns Formatted date for modal UI.
   */
  formatDateFull(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  /**
   * Returns an emoji representation for a given mood label.
   *
   * Contract:
   * - `mood` must be a MoodName string label coming from the backend,
   *   which in turn comes from the Diary component (e.g. "Happy", "Angry").
   *
   * @param mood Mood label saved in the diary entry.
   * @returns Emoji corresponding to the given mood label.
   */
  moodIcon(mood: MoodName): string {
    const map: Record<MoodName, string> = {
      Excited: '⚡',
      Happy: '😄',
      Calm: '😌',
      Focused: '🎯',
      Tired: '😴',
      Sad: '😢',
      Stressed: '😖',
      Angry: '😠',
    };

    return map[mood] ?? '🙂';
  }
}
