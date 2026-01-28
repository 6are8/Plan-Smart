import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

/**
 * Short information shown in the history list
 */
interface HistoryItem {
  id: string;
  date: string;      // ISO date string
  summary: string;   // AI-generated summary (or fallback)
}

/**
 * Full details for a single diary entry
 */
interface HistoryDetails {
  id: string;
  date: string;
  mood: number;         // 1..5
  good: string;
  improve: string;
  howIFeel?: string;
  aiSummary?: string | null;
}

/**
 * Backend response shape for GET /history
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

  /** List of diary entries (newest first) */
  entries: HistoryItem[] = [];

  /** Loading state for the history list */
  loading = true;

  /** Currently selected entry for the details modal */
  selectedEntry: HistoryDetails | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  /**
   * Loads all diary history entries from the backend (aggregated endpoint)
   * Then maps journal_entries -> HistoryItem list
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
   * Opens the details modal for a specific diary entry
   * Uses the existing backend endpoint: GET /journal/<id>
   */
  openDetails(id: string): void {
    this.http
      .get<any>(`http://localhost:5000/journal/${id}`)
      .subscribe({
        next: (res) => {
          const entry = res?.entry ?? res; // depending on your backend wrapper
          this.selectedEntry = {
            id: String(entry.id),
            date: String(entry.date),
            mood: Number(entry.mood),
            good: String(entry.what_went_well ?? ''),
            improve: String(entry.what_to_improve ?? ''),
            howIFeel: String(entry.how_i_feel ?? ''),
            aiSummary: entry.ai_summary ?? null
          };
        },
        error: (err) => {
          console.error('Failed to load entry details:', err);
        }
      });
  }

  closeDetails(): void {
    this.selectedEntry = null;
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'short',
      day: '2-digit',
      month: 'short'
    });
  }

  formatDateFull(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  moodIcon(mood: number): string {
    return ['😞', '😕', '😐', '🙂', '😄'][mood - 1] ?? '😐';
  }
}
