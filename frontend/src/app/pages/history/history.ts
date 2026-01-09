import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

/**
 * Short information shown in the history list
 */
interface HistoryItem {
  id: number;
  date: string;     // ISO date string
  summary: string;  // AI-generated summary
}

/**
 * Full details for a single diary entry
 */
interface HistoryDetails {
  id: number;
  date: string;     // ISO date string
  mood: number;     // Mood value from 1 to 5
  good: string;     // What went well
  improve: string;  // What can be improved
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

  /**
   * Lifecycle hook
   * Loads the history list on component initialization
   */
  ngOnInit(): void {
    this.loadHistory();
  }

  /**
   * Loads all diary history entries from the backend
   * Entries are sorted by date (newest first)
   */
  loadHistory(): void {
    this.http
      .get<HistoryItem[]>('http://localhost:5000/history')
      .subscribe(res => {
        this.entries = res.sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );
        this.loading = false;
      });
  }

  /**
   * Opens the details modal for a specific diary entry
   * @param id Entry ID
   */
  openDetails(id: number): void {
    this.http
      .get<HistoryDetails>(`http://localhost:5000/history/${id}`)
      .subscribe(res => {
        this.selectedEntry = res;
      });
  }

  /**
   * Closes the details modal
   */
  closeDetails(): void {
    this.selectedEntry = null;
  }

  /**
   * Formats a short date for the history list
   * Example: Mon, Sep 18
   */
  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'short',
      day: '2-digit',
      month: 'short'
    });
  }

  /**
   * Formats a full date for the details modal
   * Example: Monday, September 18, 2025
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
   * Returns an emoji icon for a given mood value
   * @param mood Mood value from 1 to 5
   */
  moodIcon(mood: number): string {
    return ['😞', '😕', '😐', '🙂', '😄'][mood - 1] ?? '😐';
  }
}
