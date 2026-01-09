import { Component, OnInit } from '@angular/core';
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

  /**
   * The city selected by the user.
   * Displayed in the settings view and sent to the backend when updated.
   */
  city = 'Your city';

  /**
   * Time for morning AI plan.
   */
  morningTime = '07:30';

  /**
   * Time for evening reflection.
   */
  eveningTime = '21:00';

  /**
   * Creates an instance of the Settings component.
   *
   * @param http HttpClient used for communicating with the backend API
   */
  constructor(private http: HttpClient) {}

  /**
   * Angular lifecycle hook.
   * Called once after the component has been initialized.
   * Loads the saved settings from the backend.
   */
  ngOnInit(): void {
    this.loadSettings();
  }

  /**
   * Loads user settings from the backend.
   * Updates local component state with the received values.
   */
  loadSettings(): void {
    this.http
      .get<any>('http://localhost:5000/settings')
      .subscribe(res => {
        this.city = res.city;
        this.morningTime = res.morning_time;
        this.eveningTime = res.evening_time;
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
      .subscribe();
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
      .subscribe();
  }
}
