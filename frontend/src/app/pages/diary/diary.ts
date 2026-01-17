import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-diary',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './diary.html',
  styleUrl: './diary.css',
})
export class Diary {

  form: FormGroup;
  mood = 0;

  successMessage: string | null = null;
  errorMessage: string | null = null;

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
      howIFeel: ['', Validators.required],
    });
  }

  selectMood(value: number): void {
    this.mood = value;
  }

  submit(): void {
    this.successMessage = null;
    this.errorMessage = null;

    if (this.form.invalid || this.mood === 0) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = {
      mood: this.mood,
      what_went_well: this.form.value.good,
      what_to_improve: this.form.value.improve,
      how_i_feel: this.form.value.howIFeel,
    };

    this.http
      .post('http://localhost:5000/journal/', payload)
      .subscribe({
        next: () => {
          this.successMessage = 'Saved ✅';
          this.form.reset();
          this.mood = 0;
        },
        error: (err) => {
          console.error('Failed to save journal entry:', err);
          this.errorMessage = 'Save failed. Please try again.';
        }
      });
  }
}
