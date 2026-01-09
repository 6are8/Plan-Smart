import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { HttpClient } from '@angular/common/http';

/**
 * Diary page component
 * Allows the user to submit a daily reflection with mood and text inputs
 */
@Component({
  selector: 'app-diary',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './diary.html',
  styleUrl: './diary.css',
})
export class Diary {

  /** Reactive form for diary inputs */
  form: FormGroup;

  /** Selected mood value (1–5) */
  mood = 0;

  /** Success feedback message after saving */
  successMessage: string | null = null;

  /** Available mood options */
  moods = [
    { value: 1, icon: '😞' },
    { value: 2, icon: '😕' },
    { value: 3, icon: '😐' },
    { value: 4, icon: '🙂' },
    { value: 5, icon: '😄' },
  ];

  constructor(
    private fb: FormBuilder,
    private http: HttpClient
  ) {
    this.form = this.fb.group({
      good: ['', Validators.required],
      improve: ['', Validators.required],
    });
  }

  /**
   * Sets the selected mood
   * @param value Mood value from 1 to 5
   */
  selectMood(value: number): void {
    this.mood = value;
  }

  /**
   * Submits the diary entry to the backend
   * Validates form fields and mood selection before sending
   */
  submit(): void {
    if (this.form.invalid || this.mood === 0) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = {
      mood: this.mood,
      good: this.form.value.good,
      improve: this.form.value.improve,
    };

    this.http
      .post('http://localhost:5000/diary', payload)
      .subscribe(() => {
        this.successMessage = 'Saved ✅';
        this.form.reset();
        this.mood = 0;
      });
  }
}
