import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { HttpClient } from '@angular/common/http';

/**
 * Supported mood labels sent to the backend
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
 * Diary component
 *
 * Allows the user to:
 * - select a mood via a 2D mood circle or preset buttons
 * - write daily reflections
 * - submit the entry to the backend
 *
 * Only the mood label (string) is sent to the backend.
 */
@Component({
  selector: 'app-diary',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './diary.html',
  styleUrl: './diary.css',
})
export class Diary {
  /** Reactive form for diary text inputs */
  form: FormGroup;

  /** Reference to the mood circle element */
  @ViewChild('circle', { static: false })
  circleRef!: ElementRef<HTMLDivElement>;

  /** Internal drag state for pointer interaction */
  private dragging = false;

  /** Internal coordinates used only for UI positioning */
  moodValence = 0;
  moodArousal = 0;

  /** UI state flags */
  moodIsSet = false;
  moodTouched = false;

  /** Dot position in percentage values */
  dotLeftPct = 50;
  dotTopPct = 50;

  /** Selected mood output */
  moodLabel: MoodName | 'Not set' = 'Not set';
  moodEmoji = '🙂';

  /** Success feedback message */
  successMessage: string | null = null;

  /**
   * Preset moods used for:
   * - quick selection
   * - mapping pointer position to nearest mood
   *
   * Values are NOT sent to the backend.
   */
  private presets: Record<MoodName, { v: number; a: number; emoji: string }> = {
    Excited:  { v: 65,  a: 80,  emoji: '⚡' },
    Happy:    { v: 80,  a: 35,  emoji: '😄' },
    Calm:     { v: 60,  a: -55, emoji: '😌' },
    Focused:  { v: 35,  a: 20,  emoji: '🎯' },
    Tired:    { v: -10, a: -85, emoji: '😴' },
    Sad:      { v: -75, a: -35, emoji: '😢' },
    Stressed: { v: -35, a: 70,  emoji: '😖' },
    Angry:    { v: -85, a: 55,  emoji: '😠' },
  };

  constructor(private fb: FormBuilder, private http: HttpClient) {
    this.form = this.fb.group({
      good: ['', Validators.required],
      improve: ['', Validators.required],
    });
  }

  /**
   * Selects a mood preset directly
   */
  setPreset(name: MoodName): void {
    this.moodTouched = true;

    const preset = this.presets[name];

    this.moodValence = preset.v;
    this.moodArousal = preset.a;

    this.moodLabel = name;
    this.moodEmoji = preset.emoji;

    const nx = this.moodValence / 100;
    const ny = -(this.moodArousal / 100);

    this.dotLeftPct = 50 + nx * 50;
    this.dotTopPct = 50 + ny * 50;

    this.moodIsSet = true;
  }

  /** Pointer down handler for mood circle */
  onCirclePointerDown(ev: PointerEvent): void {
    this.moodTouched = true;
    this.dragging = true;

    const el = this.circleRef?.nativeElement;
    if (el) el.setPointerCapture(ev.pointerId);

    this.setMoodFromPointer(ev);
  }

  /** Pointer move handler for mood circle */
  onCirclePointerMove(ev: PointerEvent): void {
    if (!this.dragging) return;
    this.setMoodFromPointer(ev);
  }

  /** Pointer up handler for mood circle */
  onCirclePointerUp(): void {
    this.dragging = false;
  }

  /**
   * Updates mood selection based on pointer position
   * Used only for UI interaction, not sent to backend
   */
  private setMoodFromPointer(ev: PointerEvent): void {
    const el = this.circleRef?.nativeElement;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;

    const px = ev.clientX - cx;
    const py = ev.clientY - cy;

    const radius = Math.min(rect.width, rect.height) / 2 - 10;

    const dist = Math.sqrt(px * px + py * py);
    const k = dist > radius && dist !== 0 ? radius / dist : 1;

    const x = px * k;
    const y = py * k;

    const nx = radius === 0 ? 0 : x / radius;
    const ny = radius === 0 ? 0 : y / radius;

    this.moodValence = Math.round(nx * 100);
    this.moodArousal = Math.round(-ny * 100);

    this.dotLeftPct = 50 + nx * 50;
    this.dotTopPct = 50 + ny * 50;

    this.moodIsSet = true;
    this.updateLabelFromNearestPreset();
  }

  /**
   * Determines the closest preset mood
   * based on current internal coordinates
   */
  private updateLabelFromNearestPreset(): void {
    let best: MoodName = 'Happy';
    let bestDistance = Number.POSITIVE_INFINITY;

    (Object.keys(this.presets) as MoodName[]).forEach((name) => {
      const p = this.presets[name];
      const dv = this.moodValence - p.v;
      const da = this.moodArousal - p.a;
      const distance = dv * dv + da * da;

      if (distance < bestDistance) {
        bestDistance = distance;
        best = name;
      }
    });

    this.moodLabel = best;
    this.moodEmoji = this.presets[best].emoji;
  }

  /**
   * Submits the diary entry to the backend
   *
   * Payload contains:
   * - mood (string label)
   * - reflection text fields
   */
  submit(): void {
    this.moodTouched = true;

    if (this.form.invalid || !this.moodIsSet) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = {
      mood: this.moodLabel,
      good: this.form.value.good,
      improve: this.form.value.improve,
    };

    this.http.post('http://localhost:5000/diary', payload).subscribe(() => {
      this.successMessage = 'Saved ✅';
      this.form.reset();

      this.moodValence = 0;
      this.moodArousal = 0;
      this.moodIsSet = false;
      this.moodTouched = false;
      this.dotLeftPct = 50;
      this.dotTopPct = 50;
      this.moodLabel = 'Not set';
      this.moodEmoji = '🙂';
    });
  }
}
