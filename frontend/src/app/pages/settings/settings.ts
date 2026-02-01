import { Component, OnInit, ChangeDetectorRef } from '@angular/core';  // ← ChangeDetectorRef hinzufügen
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';



/**
 * Settings component
 *
 * This component is responsible for displaying and managing
 * user settings such as:
 * - city
 * - notification times (morning and evening)
 *
 * It loads the settings from the backend on initialization
 * and allows the user to update them via HTTP requests.
 */


@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule
  ],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings implements OnInit {

  city = 'Your city';
  morningTime = '07:30';
  eveningTime = '21:00';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef  // ← NEU
  ) {
    console.log('🏗️ Settings Constructor called');
  }

  ngOnInit(): void {
    console.log('🚀 Settings ngOnInit called');
    this.loadSettings();
  }

  loadSettings(): void {
    console.log('📡 loadSettings() called');

    this.http
      .get<any>('http://localhost:5000/settings')
      .subscribe({
        next: (res) => {
          console.log('📥 Settings response:', res);

          if (res.user) {
            this.city = res.user.city || 'Your city';
          }

          if (res.settings) {
            this.morningTime = res.settings.morning_time || '07:30';
            this.eveningTime = res.settings.evening_time || '21:00';
          }

          console.log('✅ Values updated:', {
            city: this.city,
            morningTime: this.morningTime,
            eveningTime: this.eveningTime
          });

          // ⚡ KRITISCH: Force Change Detection
          this.cdr.detectChanges();
        },
        error: (err) => {
          console.error('❌ Failed to load settings:', err);
        }
      });
  }


  /**
   * Saves the selected city to the backend.
   */
  saveCity(): void {
    this.http
      .post('http://localhost:5000/settings/city', {
        city: this.city
      })
      .subscribe({
        next: (res: any) => {
          console.log('✅ City saved:', res);
          alert('Stadt gespeichert!');
        },
        error: (err) => {
          console.error('❌ Failed to save city:', err);
          alert('Fehler beim Speichern!');
        }
      });
  }

  /**
   * Saves time settings (morning and evening) to the backend.
   */
  saveTimeSettings(): void {
    this.http
      .post('http://localhost:5000/settings/notifications', {
        morning_time: this.morningTime,
        evening_time: this.eveningTime
      })
      .subscribe({
        next: (res: any) => {
          console.log('✅ Time settings saved:', res);
          alert('Zeiten gespeichert!');
        },
        error: (err) => {
          console.error('❌ Failed to save time settings:', err);
          alert('Fehler beim Speichern!');
        }
      });
  }


 
}