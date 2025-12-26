import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

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

  notificationsEnabled = false;
  morningTime = '07:30';
  eveningTime = '21:00';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings() {
    this.http
      .get<any>('http://localhost:5000/settings')
      .subscribe(res => {
        this.city = res.city;
        this.notificationsEnabled = res.notifications_enabled;
        this.morningTime = res.morning_time;
        this.eveningTime = res.evening_time;
      });
  }

  saveCity() {
    this.http
      .post('http://localhost:5000/settings/city', {
        city: this.city
      })
      .subscribe();
  }

  saveNotificationSettings() {
    this.http
      .post('http://localhost:5000/settings/notifications', {
        enabled: this.notificationsEnabled,
        morning_time: this.morningTime,
        evening_time: this.eveningTime
      })
      .subscribe();
  }

  toggleNotifications(event: Event) {
    const checkbox = event.target as HTMLInputElement;
    this.notificationsEnabled = checkbox.checked;
  }
}
